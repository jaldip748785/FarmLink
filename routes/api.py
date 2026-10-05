from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models import db
from models.order import Order
from models.product import Product
from models.review import Review
from utils.apmc_sync import sync_apmc_rates_from_api

api_bp = Blueprint("api", __name__)


@api_bp.route("/ping")
def ping():
    return jsonify({"success": True})


@api_bp.route("/apmc/sync", methods=["POST"])
def sync_apmc_rates_api():
    api_key = request.json.get("api_key") if request.is_json else None
    resource_id = request.json.get("resource_id") if request.is_json else None
    base_url = request.json.get("base_url") if request.is_json else None

    try:
        result = sync_apmc_rates_from_api(api_key=api_key, resource_id=resource_id, base_url=base_url)
        return jsonify({"success": True, **result}), 200
    except Exception as exc:
        return jsonify({"success": False, "message": str(exc)}), 400


@api_bp.route("/reviews", methods=["POST"])
@login_required
def create_review():
    data = request.get_json(silent=True) or {}
    product_id = data.get("product_id")
    rating = data.get("rating")
    comment = (data.get("comment") or "").strip()

    if not product_id or not rating or not comment:
        return jsonify({"success": False, "message": "Please provide a product, rating, and review comment."}), 400

    product = Product.query.get(product_id)
    if not product:
        return jsonify({"success": False, "message": "Product not found."}), 404

    purchase = Order.query.filter_by(product_id=product_id, buyer_id=current_user.id).filter(
        Order.status.in_(["Paid", "Confirmed", "Delivered"])
    ).first()
    if not purchase:
        return jsonify({"success": False, "message": "You can only review products you purchased."}), 403

    if not 1 <= int(rating) <= 5:
        return jsonify({"success": False, "message": "Rating must be between 1 and 5."}), 400

    existing_review = Review.query.filter_by(product_id=product_id, author_id=current_user.id).first()
    if existing_review:
        existing_review.rating = int(rating)
        existing_review.comment = comment
    else:
        review = Review(product_id=product_id, author_id=current_user.id, rating=int(rating), comment=comment)
        db.session.add(review)

    db.session.commit()
    return jsonify({"success": True, "message": "Review submitted successfully."}), 201

