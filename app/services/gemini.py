import os
import json
from google import genai
from google.genai import types
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.transaction import TransactionBase

# Assume SYSTEM_INSTRUCTIONS.md is in the project root
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INSTRUCTIONS_PATH = os.path.join(ROOT_DIR, "SYSTEM_INSTRUCTIONS.md")

class GeminiService:
    def __init__(self):
        # We only need one client instance globally, initialized here
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self._load_instructions()

    def _load_instructions(self):
        if os.path.exists(INSTRUCTIONS_PATH):
            with open(INSTRUCTIONS_PATH, "r", encoding="utf-8") as f:
                self.system_instructions = f.read()
        else:
            self.system_instructions = (
                "You are a Financial Data Extraction Specialist. "
                "Parse expenses to JSON with 'amount', 'type', 'category', 'description'."
            )

    async def parse_transaction_text(self, text: str) -> dict:
        """
        Sends the user text to Gemini and parses the structured response.
        Returns a dictionary representing the extracted transaction or an error.
        """
        config = types.GenerateContentConfig(
            system_instruction=self.system_instructions,
            response_mime_type="application/json",
            temperature=0.0, # Deterministic extraction behavior
        )

        try:
            response = await self.client.aio.models.generate_content(
                model='gemini-2.5-flash',
                contents=text,
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
                
            # Basic validation using our schema to ensure no arbitrary keys are injected
            TransactionBase(**extracted_json)
            
            return extracted_json
            
        except json.JSONDecodeError:
            return {"error": "Failed to parse API output into valid JSON."}
        except ValidationError as e:
            return {"error": f"Extracted data is invalid or missing fields: {e.errors()[0]['msg']}"}
        except Exception as e:
            return {"error": f"LLM API Error: {str(e)}"}
