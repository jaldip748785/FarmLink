from models import db
from datetime import datetime


class APMCRate(db.Model):
    __tablename__ = "apmc_rates"

    id = db.Column(db.Integer, primary_key=True)
    commodity_name = db.Column(db.String(150), nullable=False)
    market_name = db.Column(db.String(150), nullable=False)
    state = db.Column(db.String(100), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)
    district_id = db.Column(db.Integer, db.ForeignKey("districts.id"), nullable=True)
    modal_price = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    minimum_price = db.Column(db.Numeric(10, 2), nullable=True, default=0)
    maximum_price = db.Column(db.Numeric(10, 2), nullable=True, default=0)
    unit = db.Column(db.String(20), nullable=False, default="kg")
    rate_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    source = db.Column(db.String(100), nullable=True, default="AGMARKNET")
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())

    district = db.relationship("District", primaryjoin="APMCRate.district_id == District.id")
    category = db.relationship(
        "Category",
        primaryjoin="APMCRate.category_id == Category.id",
        backref=db.backref("apmc_rates", lazy=True)
    )
