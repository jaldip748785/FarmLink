from .home import home_bp
from .auth import auth_bp
from .farmer import farmer_bp
from .buyer import buyer_bp
from .product import product_bp
from .admin import admin_bp
from .bargaining import bargaining_bp
from .order import order_bp
from .notification import notification_bp
from .api import api_bp


def register_blueprints(app):
    """
    Register all application blueprints.
    """

    app.register_blueprint(home_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(farmer_bp, url_prefix="/farmer")
    app.register_blueprint(buyer_bp, url_prefix="/buyer")
    app.register_blueprint(product_bp, url_prefix="/product")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(bargaining_bp)
    app.register_blueprint(order_bp, url_prefix="/order")
    app.register_blueprint(notification_bp)
    app.register_blueprint(api_bp, url_prefix="/api")