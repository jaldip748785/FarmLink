from flask import Blueprint, render_template, jsonify
from models.location import Taluka, Village
from models.product import Product

home_bp = Blueprint(
    "home",
    __name__
)


@home_bp.route("/")
def index():
    featured_products = (
        Product.query.filter(Product.status == "Available", Product.quantity > 0)
        .order_by(Product.id.desc())
        .limit(6)
        .all()
    )

    return render_template(
        "index.html",
        featured_products=featured_products
    )


@home_bp.route("/api/talukas/<int:district_id>")
def get_talukas(district_id):

    talukas = Taluka.query.filter_by(
        district_id=district_id
    ).order_by(Taluka.name).all()

    return jsonify([
        {"id": t.id, "name": t.name}
        for t in talukas
    ])


@home_bp.route("/api/villages/<int:taluka_id>")
def get_villages(taluka_id):

    villages = Village.query.filter_by(
        taluka_id=taluka_id
    ).order_by(Village.name).all()

    return jsonify([
        {"id": v.id, "name": v.name}
        for v in villages
    ])