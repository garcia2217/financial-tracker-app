import uuid
from datetime import datetime
from sqlalchemy import Numeric, ForeignKey, DateTime, func, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

class Budget(Base):
    __tablename__ = "budgets"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    category_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("categories.id"), index=True)
    
    amount: Mapped[float] = mapped_column(Numeric(14, 2))
    
    month: Mapped[int | None] = mapped_column(Integer, nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", lazy="selectin")
    category: Mapped["Category"] = relationship("Category", lazy="selectin")
