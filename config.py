import os
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()


def _build_database_uri():
    db_type = os.getenv("DB_TYPE", "mysql").lower()

    if db_type == "sqlite":
        return "sqlite:///farmlink.db"

    required_mysql_vars = ["DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD"]
    if not all(os.getenv(key) for key in required_mysql_vars):
        return "sqlite:///farmlink.db"

    uri = (
        f"mysql+pymysql://"
        f"{os.getenv('DB_USER')}:"
        f"{quote_plus(os.getenv('DB_PASSWORD'))}@"
        f"{os.getenv('DB_HOST')}:"
        f"{os.getenv('DB_PORT', '3306')}/"
        f"{os.getenv('DB_NAME')}"
    )

    try:
        engine = create_engine(uri)
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return uri
    except Exception:
        return "sqlite:///farmlink.db"


class Config:

    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "farmlink_secret_key"
    )

    # Admin Credentials Configuration
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "farmerlink87@gmail.com")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "farmlink@123")

    # Database Configuration
    DB_TYPE = os.getenv("DB_TYPE", "sqlite")
    SQLALCHEMY_DATABASE_URI = _build_database_uri()

    SQLALCHEMY_TRACK_MODIFICATIONS = False


    # Upload Configuration
    UPLOAD_FOLDER = os.getenv(
        "UPLOAD_FOLDER",
        "static/uploads"
    )

    # OGD API Config
    OGD_API_KEY = os.getenv("OGD_API_KEY", "")
    OGD_APMC_RESOURCE_ID = os.getenv("OGD_APMC_RESOURCE_ID", "9ef84268-d588-465a-a308-a864a43d0070")
    OGD_APMC_API_BASE_URL = os.getenv("OGD_APMC_API_BASE_URL", "https://api.data.gov.in")
    APMC_SYNC_TIME = os.getenv("APMC_SYNC_TIME", "06:00")


    # Maximum upload size (5 MB)
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024


    # Allowed image extensions
    ALLOWED_EXTENSIONS = {
        "png",
        "jpg",
        "jpeg",
        "gif",
        "webp"
    }