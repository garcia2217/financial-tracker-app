import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Numeric, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    wallet_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("wallets.id"), index=True)
    category_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("categories.id"), nullable=True, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    type: Mapped[str] = mapped_column(String(20)) # 'income', 'expense', 'transfer'
    description: Mapped[str] = mapped_column(String(500))
    destination_wallet_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("wallets.id"), nullable=True, index=True)
    transaction_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", lazy="selectin")
    wallet: Mapped["Wallet"] = relationship("Wallet", foreign_keys=[wallet_id], lazy="selectin")
    destination_wallet: Mapped["Wallet"] = relationship("Wallet", foreign_keys=[destination_wallet_id], lazy="selectin")
    category: Mapped["Category"] = relationship("Category", lazy="selectin")
