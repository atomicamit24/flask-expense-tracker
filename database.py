import os
from flask_sqlalchemy import SQLAlchemy

# Ensure pure Python fallback is used if C extensions are blocked by Windows policies
os.environ.setdefault("DISABLE_SQLALCHEMY_CEXT", "1")

# Initialize the SQLAlchemy instance for database connectivity & session management
db = SQLAlchemy()


def init_db(app):
    """
    Configures database connectivity and initializes SQLite tables.
    """
    base_dir = os.path.abspath(os.path.dirname(__file__))
    app.config.setdefault(
        "SQLALCHEMY_DATABASE_URI",
        f"sqlite:///{os.path.join(base_dir, 'expenses.db')}",
    )
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)

    db.init_app(app)

    with app.app_context():
        db.create_all()
