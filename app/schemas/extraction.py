from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.transaction import MoneyAmount


class TransactionExtraction(BaseModel):
    """Everything the model is allowed to say about a transaction message.

    Kept apart from the persistence schemas because the model speaks in names,
    not ids, and `wallet` stops existing once the transaction is stored. Extra
    keys are rejected rather than ignored, so a field the model invents is a
    failed extraction instead of unvalidated data flowing on.
    """

    model_config = ConfigDict(extra="forbid")

    amount: MoneyAmount
    type: Literal["income", "expense"]
    category: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=500)
    wallet: Optional[str] = None
