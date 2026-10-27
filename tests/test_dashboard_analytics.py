import calendar
import unittest
from datetime import date
from unittest.mock import patch

import database
from flask import template_rendered

# Importing app.py normally creates the default on-disk database at module load.
with patch.object(database, "init_db"):
    import app as app_module

app_module.init_db = database.init_db

from database import db
from models import Expense


class DashboardAnalyticsTests(unittest.TestCase):
    def setUp(self):
        self.app = app_module.create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "test-secret",
                "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            }
        )
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.engine.dispose()

    def render_dashboard_context(self):
        rendered = {}

        def capture_context(sender, template, context, **extra):
            if template.name == "index.html":
                rendered.update(context)

        template_rendered.connect(capture_context, sender=self.app)
        try:
            response = self.client.get("/")
        finally:
            template_rendered.disconnect(capture_context, sender=self.app)

        self.assertEqual(response.status_code, 200)
        self.assertIn("chart_data", rendered)
        return rendered

    def add_expenses(self, expenses):
        with self.app.app_context():
            db.session.add_all(expenses)
            db.session.commit()

    def test_total_current_month_average_and_category_totals(self):
        today = date.today()
        other_month = today.month + 1 if today.month < 12 else today.month - 1

        self.add_expenses(
            [
                Expense(
                    title="Current month food",
                    amount=12.50,
                    category="Food",
                    spent_on=date(today.year, today.month, 1),
                ),
                Expense(
                    title="Current month travel",
                    amount=7.25,
                    category="Travel",
                    spent_on=date(today.year, today.month, 2),
                ),
                Expense(
                    title="Other month food",
                    amount=25.50,
                    category="Food",
                    spent_on=date(today.year, other_month, 1),
                ),
                Expense(
                    title="Previous year expense",
                    amount=90.00,
                    category="Others",
                    spent_on=date(today.year - 1, today.month, 1),
                ),
            ]
        )

        context = self.render_dashboard_context()
        self.assertEqual(context["total_amount"], 135.25)
        self.assertEqual(context["current_month_total"], 19.75)
        self.assertEqual(context["current_month_count"], 2)
        self.assertEqual(context["category_totals"], {
            "Food": 38.0,
            "Travel": 7.25,
            "Utilities": 0.0,
            "Others": 90.0,
        })

        average_expense = context["total_amount"] / len(context["expenses"])
        self.assertEqual(average_expense, 33.8125)

    def test_monthly_aggregation_separates_years_and_leaves_empty_months_zero(self):
        today = date.today()
        other_month = today.month + 1 if today.month < 12 else today.month - 1
        self.add_expenses(
            [
                Expense(
                    title="Current year expense",
                    amount=19.75,
                    category="Food",
                    spent_on=date(today.year, today.month, 1),
                ),
                Expense(
                    title="Another current year month",
                    amount=25.50,
                    category="Travel",
                    spent_on=date(today.year, other_month, 1),
                ),
                Expense(
                    title="Same month previous year",
                    amount=90.00,
                    category="Others",
                    spent_on=date(today.year - 1, today.month, 1),
                ),
            ]
        )

        context = self.render_dashboard_context()
        chart_data = context["chart_data"]
        current_month_index = today.month - 1
        other_month_index = other_month - 1
        self.assertEqual(context["report_year"], today.year)
        self.assertEqual(len(chart_data["monthly_labels"]), 12)
        self.assertEqual(
            chart_data["monthly_labels"],
            [calendar.month_name[month] for month in range(1, 13)],
        )
        expected_monthly_totals = [0.0] * 12
        expected_monthly_totals[current_month_index] = 19.75
        expected_monthly_totals[other_month_index] = 25.50
        self.assertEqual(chart_data["monthly_totals"], expected_monthly_totals)
        self.assertEqual(chart_data["category_totals"], [19.75, 25.5, 0.0, 90.0])

    def test_empty_database_returns_zero_summaries_and_charts(self):
        context = self.render_dashboard_context()

        self.assertEqual(context["expenses"], [])
        self.assertEqual(context["total_amount"], 0)
        self.assertEqual(context["current_month_total"], 0.0)
        self.assertEqual(context["current_month_count"], 0)
        self.assertTrue(all(value == 0.0 for value in context["category_totals"].values()))
        self.assertEqual(context["category_percentages"], {
            "Food": 0.0,
            "Travel": 0.0,
            "Utilities": 0.0,
            "Others": 0.0,
        })
        self.assertEqual(context["chart_data"]["monthly_totals"], [0.0] * 12)
        self.assertEqual(context["chart_data"]["category_totals"], [0.0] * 4)

    def test_zero_value_expense_does_not_divide_by_zero_in_category_percentages(self):
        today = date.today()
        self.add_expenses(
            [
                Expense(
                    title="Zero amount",
                    amount=0.0,
                    category="Food",
                    spent_on=today,
                )
            ]
        )

        context = self.render_dashboard_context()
        self.assertEqual(context["total_amount"], 0.0)
        self.assertEqual(context["current_month_total"], 0.0)
        self.assertEqual(context["current_month_count"], 1)
        self.assertEqual(context["category_percentages"]["Food"], 0.0)
        self.assertEqual(context["chart_data"]["monthly_totals"], [0.0] * 12)
        self.assertEqual(context["chart_data"]["category_totals"], [0.0] * 4)


if __name__ == "__main__":
    unittest.main()
