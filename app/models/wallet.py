import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Index, String, Numeric, ForeignKey, DateTime, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

class Wallet(Base):
    __tablename__ = "wallets"
    __table_args__ = (
        Index("uq_wallets_user_id_lower_name", "user_id", text("lower(name)"), unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    balance: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", lazy="selectin")
