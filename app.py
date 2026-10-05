import re
from pathlib import Path
from sqlalchemy import inspect, text

from flask import Flask
from flask_login import LoginManager
from config import Config
from models import db
from routes import register_blueprints
from models.user import User
from models.product import Product
from models.bargaining import BargainingSession, BargainingOffer
from models.order import Order
from models.notification import Notification
from models.cart import CartItem
from models.review import Review
from models.apmc_rate import APMCRate
from models.location import District
from models.category import Category
from models.farmer_verification import FarmerVerification
from flask import session
from utils.voice import get_voice_language


def seed_default_category_data(app):
    with app.app_context():
        if Category.query.count() > 0:
            return

        base_dir = Path(__file__).resolve().parent
        sql_file = base_dir / "database" / "catefgories.sql"

        if not sql_file.exists():
            return

        with sql_file.open("r", encoding="utf-8") as handle:
            content = handle.read()

        insert_statements = re.findall(r"INSERT\s+INTO\s+.*?;", content, flags=re.IGNORECASE | re.DOTALL)
        for statement in insert_statements:
            db.session.execute(db.text(statement))
        db.session.commit()


def seed_default_location_data(app):
    with app.app_context():
        from models.location import Taluka, Village

        if District.query.count() > 0 and Taluka.query.count() > 0 and Village.query.count() > 0:
            return

        base_dir = Path(__file__).resolve().parent
        sql_files = [
            base_dir / "database" / "districts.sql",
            base_dir / "database" / "talukas.sql",
            base_dir / "database" / "villages.sql",
        ]

        for sql_file in sql_files:
            if not sql_file.exists():
                continue
            with sql_file.open("r", encoding="utf-8") as handle:
                content = handle.read()
            insert_statements = re.findall(r"INSERT\s+INTO\s+.*?;", content, flags=re.IGNORECASE | re.DOTALL)
            for statement in insert_statements:
                db.session.execute(db.text(statement))
        db.session.commit()


def ensure_order_schema(app):
    with app.app_context():
        inspector = inspect(db.engine)
        if "orders" not in inspector.get_table_names():
            return

        existing_columns = {column["name"] for column in inspector.get_columns("orders")}
        required_columns = {
            "payment_method": "VARCHAR(50) DEFAULT 'cash_on_delivery'",
            "payment_status": "VARCHAR(50) DEFAULT 'Pending'",
        }

        for column_name, column_type in required_columns.items():
            if column_name not in existing_columns:
                db.session.execute(text(f"ALTER TABLE orders ADD COLUMN {column_name} {column_type}"))
        db.session.commit()


def ensure_apmc_schema(app):
    with app.app_context():
        inspector = inspect(db.engine)
        if "apmc_rates" not in inspector.get_table_names():
            return

        existing_columns = {column["name"] for column in inspector.get_columns("apmc_rates")}
        if "category_id" not in existing_columns:
            db.session.execute(text("ALTER TABLE apmc_rates ADD COLUMN category_id INTEGER NULL"))
            db.session.commit()


def ensure_farmer_verification_schema(app):
    with app.app_context():
        inspector = inspect(db.engine)
        if "farmer_verifications" not in inspector.get_table_names():
            return

        existing_columns = {column["name"] for column in inspector.get_columns("farmer_verifications")}
        for column_name in ("document_712_path", "document_8a_path", "document_712_paths", "document_8a_paths"):
            if column_name not in existing_columns:
                column_type = "TEXT" if column_name.endswith("_paths") else "VARCHAR(255)"
                db.session.execute(text(f"ALTER TABLE farmer_verifications ADD COLUMN {column_name} {column_type}"))
        db.session.commit()


def create_app():

    app = Flask(__name__)

    # Load configuration
    app.config.from_object(Config)

    # Initialize database
    db.init_app(app)

    # Fall back to SQLite for local runs when the configured MySQL server is unavailable.
    with app.app_context():
        try:
            db.create_all()
        except Exception:
            app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///farmlink.db"
            db.drop_all(bind=None)
            db.create_all()

        ensure_order_schema(app)
        ensure_apmc_schema(app)
        ensure_farmer_verification_schema(app)
        Product.sync_all_statuses()
        seed_default_category_data(app)
        seed_default_location_data(app)

    # Injected translation context processor
    @app.context_processor
    def inject_translations():
        from datetime import date
        lang = session.get("lang") or "en"
        if "lang" not in session:
            session["lang"] = lang
        from utils.translations import TRANSLATIONS
        def translate(key):
            return TRANSLATIONS.get(lang, TRANSLATIONS["gu"]).get(key, key)
        return dict(_=translate, current_lang=lang, voice_lang=get_voice_language(lang), today_date=date.today())

    @app.context_processor
    def inject_voice_state():
        voice_message = session.pop("voice_message", "")
        return dict(voice_message=voice_message)

    @app.errorhandler(413)
    def request_entity_too_large(error):
        from flask import flash, redirect, url_for
        flash("The uploaded document must be 5 MB or smaller.", "danger")
        return redirect(url_for("auth.register"))

    # Injected unread notification badge helper
    @app.context_processor
    def inject_notifications():
        from flask_login import current_user
        if current_user and current_user.is_authenticated:
            unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
            return dict(unread_notifications_count=unread_count)
        return dict(unread_notifications_count=0)

    # Initialize LoginManager for Flask-Login session management
    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "warning"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Create database tables and sync admin user
    with app.app_context():
        db.create_all()
        try:
            from werkzeug.security import generate_password_hash
            from routes.admin import get_admin_credentials
            admin_email, admin_password = get_admin_credentials()
            admin_user = User.query.filter_by(role="admin").first()
            if not admin_user:
                admin_user = User.query.filter_by(email=admin_email).first()
            if not admin_user:
                admin_user = User(
                    full_name="Administrator",
                    email=admin_email,
                    phone="0000000000",
                    password=generate_password_hash(admin_password),
                    role="admin"
                )
                db.session.add(admin_user)
            else:
                admin_user.full_name = "Administrator"
                admin_user.email = admin_email
                admin_user.phone = admin_user.phone or "0000000000"
                admin_user.role = "admin"
                admin_user.password = generate_password_hash(admin_password)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print("Admin user init note:", e)

    # Register routes
    register_blueprints(app)

    return app


app = create_app()


if __name__ == "__main__":

    app.run(
        debug=True
    )