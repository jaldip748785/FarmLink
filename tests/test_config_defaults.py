import importlib
import os
import unittest


class ConfigDefaultFallbackTests(unittest.TestCase):
    def test_sqlite_is_used_when_mysql_environment_is_missing(self):
        original = {key: os.environ.get(key) for key in [
            "DB_TYPE", "DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"
        ]}

        try:
            for key in original:
                os.environ.pop(key, None)

            import config
            importlib.reload(config)
            self.assertEqual(config.Config.SQLALCHEMY_DATABASE_URI, "sqlite:///farmlink.db")
        finally:
            for key, value in original.items():
                if value is not None:
                    os.environ[key] = value
            import config
            importlib.reload(config)
