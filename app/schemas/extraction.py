from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.transaction import MoneyAmount


class TransactionExtraction(BaseModel):
    """Everything the model is allowed to say about a transaction message.

    Kept apart from the persistence schemas because the model speaks in the
    user's words, not ids, and `wallet_mention` stops existing once the
    transaction is stored. Extra keys are rejected rather than ignored, so a
    field the model invents is a failed extraction instead of unvalidated data
    flowing on.

    `wallet_mention` is what the user called their account, not a wallet this
    application knows about — resolving it is `resolve_wallet`'s job, and it is
    typed as free text to keep it from reading as anything more trustworthy.
    """

    model_config = ConfigDict(extra="forbid")

    amount: MoneyAmount
    type: Literal["income", "expense"]
    category: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=500)
    wallet_mention: Optional[str] = Field(None, max_length=100)
