import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Boolean, Index, String, Numeric, ForeignKey, DateTime, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

class Wallet(Base):
    __tablename__ = "wallets"
    __table_args__ = (
        Index("uq_wallets_user_id_lower_name", "user_id", text("lower(name)"), unique=True),
        Index(
            "uq_wallets_one_default_per_user",
            "user_id",
            unique=True,
            postgresql_where=text("is_default"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    balance: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", lazy="selectin")
