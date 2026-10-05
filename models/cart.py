from models import db
from datetime import datetime

class CartItem(db.Model):
    __tablename__ = "cart_items"
    
    id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    buyer = db.relationship("User", foreign_keys=[buyer_id], backref=db.backref("cart_items", lazy=True, cascade="all, delete-orphan"))
    product = db.relationship("Product", backref=db.backref("cart_items", lazy=True, cascade="all, delete-orphan"))
