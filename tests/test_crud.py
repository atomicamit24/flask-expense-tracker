
from datetime import date
from unittest.mock import patch

import database
import pytest

# Importing app.py normally creates the default on-disk database at module load.
with patch.object(database, "init_db"):
    import app as app_module

app_module.init_db = database.init_db

from database import db
from models import Expense


@pytest.fixture
def client():
    app = app_module.create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        }
    )
    with app.app_context():
        db.create_all()

    yield app.test_client()

    with app.app_context():
        db.session.remove()
        db.drop_all()
        db.engine.dispose()


def test_create_expense_persists_to_database(client):
    response = client.post(
        "/add",
        data={
            "title": "Test groceries",
            "amount": "24.50",
            "category": "Food",
            "description": "Weekly shop",
            "spent_on": date.today().isoformat(),
        },
    )

    assert response.status_code == 302
    with client.application.app_context():
        expense = Expense.query.one()
        assert expense.title == "Test groceries"
        assert expense.amount == 24.50
        assert expense.category == "Food"
        assert expense.description == "Weekly shop"


def test_update_expense_changes_title_category_description_and_amount(client):
    with client.application.app_context():
        expense = Expense(
            title="Old title",
            amount=24.50,
            category="Food",
            description="Old notes",
            spent_on=date.today(),
        )
        db.session.add(expense)
        db.session.commit()
        expense_id = expense.id

    response = client.post(
        f"/edit/{expense_id}",
        data={
            "title": "Updated groceries",
            "amount": "30.25",
            "category": "Travel",
            "description": "Updated notes",
        },
    )

    assert response.status_code == 302
    with client.application.app_context():
        expense = db.session.get(Expense, expense_id)
        assert expense is not None
        assert expense.title == "Updated groceries"
        assert expense.amount == 30.25
        assert expense.category == "Travel"
        assert expense.description == "Updated notes"


def test_delete_expense_removes_it_from_database(client):
    with client.application.app_context():
        expense = Expense(
            title="Remove this expense",
            amount=12.00,
            category="Others",
            spent_on=date.today(),
        )
        db.session.add(expense)
        db.session.commit()
        expense_id = expense.id

    response = client.post(f"/delete/{expense_id}")

    assert response.status_code == 302
    with client.application.app_context():
        assert db.session.get(Expense, expense_id) is None
        assert Expense.query.count() == 0


def test_create_route_rejects_zero_amount(client):
    response = client.post(
        "/add",
        data={
            "title": "Invalid zero amount",
            "amount": "0",
            "category": "Food",
            "spent_on": date.today().isoformat(),
        },
    )

    assert response.status_code == 400
    with client.application.app_context():
        assert Expense.query.count() == 0
