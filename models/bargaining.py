from models import db
from datetime import datetime

class BargainingSession(db.Model):
    __tablename__ = "bargaining_sessions"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    buyer_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    farmer_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    listed_price = db.Column(db.Numeric(10, 2), nullable=False)
    final_price = db.Column(db.Numeric(10, 2), nullable=True)
    status = db.Column(db.String(50), default="PENDING") # PENDING, NEGOTIATING, ACCEPTED, REJECTED, EXPIRED, CANCELLED, COMPLETED
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    product = db.relationship("Product", backref=db.backref("sessions", lazy=True, cascade="all, delete-orphan"))
    buyer = db.relationship("User", foreign_keys=[buyer_id], backref=db.backref("buyer_sessions", lazy=True))
    farmer = db.relationship("User", foreign_keys=[farmer_id], backref=db.backref("farmer_sessions", lazy=True))

    def check_expiration(self):
        if self.status in ["ACCEPTED", "REJECTED", "CANCELLED", "COMPLETED", "EXPIRED"]:
            return self.status == "EXPIRED"
        if self.expires_at and datetime.utcnow() > self.expires_at:
            self.status = "EXPIRED"
            for offer in self.offers:
                if offer.status == "PENDING":
                    offer.status = "EXPIRED"
            db.session.commit()
            return True
        return False


class BargainingOffer(db.Model):
    __tablename__ = "bargaining_offers"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("bargaining_sessions.id", ondelete="CASCADE"), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    offer_price = db.Column(db.Numeric(10, 2), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    message = db.Column(db.Text, nullable=True)
    offer_type = db.Column(db.String(50), nullable=False) # INITIAL, COUNTER, ACCEPTANCE
    status = db.Column(db.String(50), default="PENDING") # PENDING, ACCEPTED, REJECTED, EXPIRED, CANCELLED
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    session_rel = db.relationship("BargainingSession", backref=db.backref("offers", lazy=True, cascade="all, delete-orphan"))
    sender = db.relationship("User", foreign_keys=[sender_id])
    receiver = db.relationship("User", foreign_keys=[receiver_id])
