import os
import calendar
from datetime import date, datetime, timezone
from flask import Flask, flash, redirect, render_template, request, url_for
from database import db, init_db
from models import CATEGORIES, Expense


def create_app(test_config=None) -> Flask:
    """Factory function to configure and initialize the Flask application."""
    app = Flask(__name__)

    app.config["SECRET_KEY"] = os.environ.get(
        "SECRET_KEY", "expense-tracker-secret-key"
    )

    if test_config:
        app.config.update(test_config)

    # Initialize SQLAlchemy database connectivity and tables
    init_db(app)

    # ==========================================
    # Routes
    # ==========================================

    @app.route("/", methods=["GET"])
    def index():
        """
        Root route: Fetches all expenses from the database and renders index.html.
        """
        expenses = Expense.query.order_by(
            Expense.spent_on.desc(), Expense.created_at.desc()
        ).all()
        today = date.today()
        report_year = today.year
        total_amount = sum(e.amount for e in expenses)

        # Calculate category spending breakdown for reports
        category_totals = {cat: 0.0 for cat in CATEGORIES}
        monthly_totals = [0.0] * 12
        current_month_count = 0
        for e in expenses:
            category_totals[e.category] = category_totals.get(e.category, 0.0) + e.amount
            if e.spent_on:
                month_index = e.spent_on.month - 1
                if e.spent_on.year == report_year:
                    monthly_totals[month_index] += e.amount
                if e.spent_on.year == report_year and month_index == today.month - 1:
                    current_month_count += 1

        category_percentages = {}
        for cat, total in category_totals.items():
            category_percentages[cat] = (
                round((total / total_amount * 100), 1) if total_amount > 0 else 0.0
            )

        return render_template(
            "index.html",
            expenses=expenses,
            total_amount=total_amount,
            report_year=report_year,
            current_month_total=round(monthly_totals[today.month - 1], 2),
            current_month_count=current_month_count,
            categories=CATEGORIES,
            category_totals=category_totals,
            category_percentages=category_percentages,
            chart_data={
                "monthly_labels": [
                    calendar.month_name[month] for month in range(1, 13)
                ],
                "monthly_totals": [round(amount, 2) for amount in monthly_totals],
                "categories": CATEGORIES,
                "category_totals": [
                    round(category_totals[category], 2) for category in CATEGORIES
                ],
            },
        )

    @app.route("/expense/<int:expense_id>", methods=["GET"])
    @app.route("/view/<int:expense_id>", methods=["GET"])
    def view_expense(expense_id: int):
        """
        View detailed information for a single expense.
        """
        expense = db.get_or_404(Expense, expense_id)
        return render_template("view.html", expense=expense)

    @app.route("/add", methods=["GET", "POST"])
    def add_expense():
        """
        Route to capture and create a new expense.
        GET: Renders add.html form with category options and default date.
        POST: Processes form submission, validates inputs, and saves to database.
        """
        if request.method == "POST":
            title = request.form.get("title", "").strip()
            amount_raw = request.form.get("amount", "").strip()
            category = request.form.get("category", "Others").strip()
            description = request.form.get("description", "").strip()
            spent_on_raw = request.form.get("spent_on", "").strip()

            # Validation
            if not title:
                flash("Title is required.", "danger")
                return (
                    render_template(
                        "add.html",
                        categories=CATEGORIES,
                        today_date=date.today().isoformat(),
                    ),
                    400,
                )

            try:
                amount = float(amount_raw)
                if amount <= 0:
                    raise ValueError()
            except (ValueError, TypeError):
                flash(
                    "Please enter a valid positive amount greater than 0.",
                    "danger",
                )
                return (
                    render_template(
                        "add.html",
                        categories=CATEGORIES,
                        today_date=date.today().isoformat(),
                    ),
                    400,
                )

            if category not in CATEGORIES:
                category = "Others"

            # Parse spent_on date
            if spent_on_raw:
                try:
                    spent_on = datetime.strptime(spent_on_raw, "%Y-%m-%d").date()
                except ValueError:
                    spent_on = date.today()
            else:
                spent_on = date.today()

            new_expense = Expense(
                title=title,
                amount=round(amount, 2),
                category=category,
                description=description if description else None,
                spent_on=spent_on,
            )

            db.session.add(new_expense)
            db.session.commit()

            flash(
                f"Expense '{title}' of ${amount:.2f} added successfully!",
                "success",
            )
            return redirect(url_for("index"))

        return render_template(
            "add.html",
            categories=CATEGORIES,
            today_date=date.today().isoformat(),
        )

    @app.route("/edit/<int:expense_id>", methods=["GET", "POST"])
    @app.route("/edit", methods=["GET", "POST"])
    def edit_expense(expense_id=None):
        """
        Route to edit an existing expense.
        Captures: title, description, amount.
        """
        if expense_id is None:
            expense_id = request.args.get("id", type=int) or request.form.get("id", type=int)

        if not expense_id:
            flash("Expense ID is required.", "danger")
            return redirect(url_for("index"))

        expense = db.get_or_404(Expense, expense_id)

        if request.method == "POST":
            title = request.form.get("title", "").strip()
            amount_raw = request.form.get("amount", "").strip()
            description = request.form.get("description", "").strip()
            category = request.form.get("category", expense.category).strip()

            if not title:
                flash("Title cannot be empty.", "danger")
                return render_template(
                    "edit.html", expense=expense, categories=CATEGORIES
                ), 400

            try:
                amount = float(amount_raw)
                if amount <= 0:
                    raise ValueError()
            except (ValueError, TypeError):
                flash("Amount must be a positive number greater than 0.", "danger")
                return render_template(
                    "edit.html", expense=expense, categories=CATEGORIES
                ), 400

            if category not in CATEGORIES:
                flash("Please select a valid category.", "danger")
                return render_template(
                    "edit.html", expense=expense, categories=CATEGORIES
                ), 400

            expense.title = title
            expense.amount = round(amount, 2)
            expense.description = description if description else None
            expense.category = category
            expense.updated_at = datetime.now(timezone.utc)

            db.session.commit()
            flash(f"Expense '{expense.title}' updated successfully!", "success")
            return redirect(url_for("index"))

        return render_template("edit.html", expense=expense, categories=CATEGORIES)

    @app.route("/delete/<int:expense_id>", methods=["GET", "POST"])
    @app.route("/delete", methods=["GET", "POST"])
    def delete_expense(expense_id=None):
        """
        Route to directly delete an expense.
        """
        if expense_id is None:
            expense_id = request.args.get("id", type=int) or request.form.get("id", type=int)

        if not expense_id:
            flash("Expense ID is required.", "danger")
            return redirect(url_for("index"))

        expense = db.get_or_404(Expense, expense_id)
        title = expense.title
        db.session.delete(expense)
        db.session.commit()

        flash(f"Expense '{title}' was deleted successfully.", "info")
        return redirect(url_for("index"))

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=False, port=5000)
