from models import db
from datetime import datetime


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    buyer_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    farmer_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    original_price = db.Column(db.Numeric(10, 2), nullable=False)
    negotiated_price = db.Column(db.Numeric(10, 2), nullable=True)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    bargaining_session_id = db.Column(db.Integer, db.ForeignKey("bargaining_sessions.id", ondelete="SET NULL"), nullable=True)
    status = db.Column(db.String(50), default="Pending")  # Pending, Confirmed, Processing, Shipped, Out for Delivery, Delivered, Cancelled
    payment_method = db.Column(db.String(50), default="cash_on_delivery")
    payment_status = db.Column(db.String(50), default="Pending")  # Pending, Paid, Failed, Refunded
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def valid_statuses():
        return [
            "Pending",
            "Confirmed",
            "Processing",
            "Shipped",
            "Out for Delivery",
            "Delivered",
            "Cancelled",
        ]

    @staticmethod
    def normalize_status(value):
        if not value:
            return "Pending"
        legacy_map = {
            "Pending Payment": "Pending",
            "Paid": "Confirmed",
            "Completed": "Delivered",
            "processing": "Processing",
        }
        return legacy_map.get(value, value)

    # Relationships
    product = db.relationship("Product", backref=db.backref("orders", lazy=True))
    buyer = db.relationship("User", foreign_keys=[buyer_id], backref=db.backref("buyer_orders", lazy=True))
    farmer = db.relationship("User", foreign_keys=[farmer_id], backref=db.backref("farmer_orders", lazy=True))
    bargaining_session = db.relationship("BargainingSession", backref=db.backref("order", uselist=False))
