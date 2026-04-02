import uuid
from datetime import datetime
from sqlalchemy import String, Numeric, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

class Debt(Base):
    __tablename__ = "debts"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    person_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("persons.id"), index=True)

    amount: Mapped[float] = mapped_column(Numeric(14, 2))
    amount_settled: Mapped[float] = mapped_column(Numeric(14, 2), default=0.0)

    type: Mapped[str] = mapped_column(String(20))  # 'receivable' (they owe you) or 'payable' (you owe them)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # 'pending', 'partial', 'settled'
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", lazy="selectin")
    person: Mapped["Person"] = relationship("Person", lazy="selectin")
