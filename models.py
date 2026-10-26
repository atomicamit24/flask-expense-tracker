from datetime import date, datetime, timezone
from database import db

# Supported expense categories
CATEGORIES = ["Food", "Travel", "Utilities", "Others"]


def get_utc_now():
    """Returns current UTC timestamp."""
    return datetime.now(timezone.utc)


class Expense(db.Model):
    __tablename__ = "expenses"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(120), nullable=False)
    amount = db.Column(db.Float, nullable=False, default=0.0)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=False, default="Others")
    spent_on = db.Column(db.Date, nullable=False, default=date.today)
    created_at = db.Column(db.DateTime, nullable=False, default=get_utc_now)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=get_utc_now,
        onupdate=get_utc_now,
    )

    def to_dict(self) -> dict:
        """Serializes the expense model to a dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "amount": self.amount,
            "description": self.description or "",
            "category": self.category,
            "spent_on": self.spent_on.isoformat() if self.spent_on else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @property
    def formatted_amount(self) -> str:
        """Returns the amount formatted as currency."""
        return f"${self.amount:,.2f}"

    def __repr__(self) -> str:
        return f"<Expense {self.id}: {self.title} (${self.amount}) - {self.category}>"
