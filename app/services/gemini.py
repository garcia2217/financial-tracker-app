import os
import json
from typing import Sequence
from google import genai
from google.genai import types
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.extraction import TransactionExtraction

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INSTRUCTIONS_PATH = os.path.join(ROOT_DIR, "SYSTEM_INSTRUCTIONS.md")

class GeminiService:
    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.system_instructions = self._load_instructions()

    @staticmethod
    def _load_instructions() -> str:
        """Read the extraction contract, or fail.

        No inline fallback: it would be a second copy of the contract to keep in
        step with the schema, and a missing file would surface as invented
        categories and dropped wallet hints rather than as an error.
        """
        with open(INSTRUCTIONS_PATH, "r", encoding="utf-8") as f:
            return f.read()

    async def parse_transaction_text(self, text: str, wallet_names: Sequence[str]) -> dict:
        """
        Sends the user text to Gemini and parses the structured response.
        Returns a dictionary representing the extracted transaction or an error.

        wallet_names travels in the request rather than the system instructions,
        which stay static and shared. It also bounds what the model can say about
        wallets: a returned name that is not one we sent is discarded, so a
        hallucinated name never reaches a lookup.
        """
        config = types.GenerateContentConfig(
            system_instruction=self.system_instructions,
            response_mime_type="application/json",
            temperature=0.0, # Deterministic extraction behavior
        )
        contents = f"Available wallets: {json.dumps(list(wallet_names))}\n\nTransaction: {text}"

        try:
            response = await self.client.aio.models.generate_content(
                model='gemini-2.5-flash',
                contents=contents,
                config=config,
            )
            
            result_text = response.text.strip()
            # Clean up potential markdown blocks if the model ignores our schema constraints
            if result_text.startswith("```json"):
                result_text = result_text[7:-3].strip()
            elif result_text.startswith("```"):
                result_text = result_text[3:-3].strip()

            extracted_json = json.loads(result_text)
            
            # Application logic: detect handled semantic errors parsed by Gemini
            if "error" in extracted_json:
                return extracted_json
                
            extracted = TransactionExtraction(**extracted_json)

            if extracted.wallet not in wallet_names:
                extracted.wallet = None

            return extracted.model_dump()

        except json.JSONDecodeError:
            return {"error": "Failed to parse API output into valid JSON."}
        except ValidationError as e:
            return {"error": f"Extracted data is invalid or missing fields: {e.errors()[0]['msg']}"}
        except Exception as e:
            return {"error": f"LLM API Error: {str(e)}"}
