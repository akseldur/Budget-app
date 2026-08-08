"""ORM-modeller for skjemaet skissert i prosjektplanen.

Inntekt er ikke en egen tabell - det er transaksjoner/splitter kategorisert
under en rot-kategori "Inntekt" (se categories). Færre tabeller å holde
synkronisert, samme fleksibilitet.
"""

import uuid
from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def _uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[uuid.UUID] = _uuid_pk()
    bank_name: Mapped[str] = mapped_column(String, nullable=False)
    account_number: Mapped[str] = mapped_column(String, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)

    transactions: Mapped[list["Transaction"]] = relationship(back_populates="account")


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[uuid.UUID] = _uuid_pk()
    name: Mapped[str] = mapped_column(String, nullable=False)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True
    )

    parent: Mapped["Category | None"] = relationship(remote_side="Category.id", back_populates="children")
    children: Mapped[list["Category"]] = relationship(back_populates="parent")


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (UniqueConstraint("bank_tx_id", name="uq_transactions_bank_tx_id"),)

    id: Mapped[uuid.UUID] = _uuid_pk()
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    bank_tx_id: Mapped[str] = mapped_column(String, nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)

    account: Mapped["Account"] = relationship(back_populates="transactions")
    splits: Mapped[list["TransactionSplit"]] = relationship(
        back_populates="transaction", cascade="all, delete-orphan"
    )


class TransactionSplit(Base):
    """Standard: én rad med hele beløpet per transaksjon. Splitting = flere rader.

    CHECK: SUM(splits.amount WHERE transaction_id = X) = transactions.amount
    håndheves i applikasjonslaget (regnes over flere rader), ikke som DB-constraint.
    """

    __tablename__ = "transaction_splits"

    id: Mapped[uuid.UUID] = _uuid_pk()
    transaction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("transactions.id"), nullable=False
    )
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True
    )
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)

    transaction: Mapped["Transaction"] = relationship(back_populates="splits")
    category: Mapped["Category | None"] = relationship()


class BudgetLine(Base):
    __tablename__ = "budget_lines"
    __table_args__ = (
        UniqueConstraint("month", "category_id", name="uq_budget_lines_month_category"),
        CheckConstraint("EXTRACT(DAY FROM month) = 1", name="ck_budget_lines_month_is_first_of_month"),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    month: Mapped[date] = mapped_column(Date, nullable=False)
    category_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=False)
    planned_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)

    category: Mapped["Category"] = relationship()


class FundPriceSnapshot(Base):
    __tablename__ = "fund_price_snapshots"

    id: Mapped[uuid.UUID] = _uuid_pk()
    fund_isin: Mapped[str] = mapped_column(String, nullable=False)
    price: Mapped[float] = mapped_column(Numeric(14, 4), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class StudentLoanSnapshot(Base):
    __tablename__ = "student_loan_snapshots"

    id: Mapped[uuid.UUID] = _uuid_pk()
    balance: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    as_of_date: Mapped[date] = mapped_column(Date, nullable=False)
