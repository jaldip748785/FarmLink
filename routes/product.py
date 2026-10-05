from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from models import db
from models.product import Product
from models.category import Category
from models.location import District, Taluka, Village


product_bp = Blueprint(
    "product",
    __name__
)


# ---------------------------------------
# All Products
# ---------------------------------------
@product_bp.route("/")
def all_products():

    products = Product.query.order_by(
        Product.id.desc()
    ).all()

    return render_template(
        "products.html",
        products=products
    )


# ---------------------------------------
# Product Details
# ---------------------------------------
@product_bp.route("/<int:product_id>")
def product_details(product_id):

    product = Product.query.get_or_404(
        product_id
    )

    return render_template(
        "product_details.html",
        product=product
    )


# ---------------------------------------
# Search Products
# ---------------------------------------
@product_bp.route("/search")
def search_products():

    keyword = request.args.get(
        "keyword",
        ""
    )

    products = Product.query.filter(
        Product.title.ilike(
            f"%{keyword}%"
        )
    ).all()

    return render_template(
        "search_results.html",
        products=products,
        keyword=keyword
    )


# ---------------------------------------
# Filter Products
# ---------------------------------------
@product_bp.route("/filter")
def filter_products():

    category = request.args.get("category")
    district = request.args.get("district")
    taluka = request.args.get("taluka")
    village = request.args.get("village")


    query = Product.query


    if category:
        query = query.filter_by(
            category_id=category
        )

    if district:
        query = query.filter_by(
            district_id=district
        )

    if taluka:
        query = query.filter_by(
            taluka_id=taluka
        )

    if village:
        query = query.filter_by(
            village_id=village
        )


    products = query.all()

    categories = Category.query.all()
    districts = District.query.all()
    talukas = Taluka.query.all()
    villages = Village.query.all()


    return render_template(
        "filter_products.html",
        products=products,
        categories=categories,
        districts=districts,
        talukas=talukas,
        villages=villages
    )


# ---------------------------------------
# Products By Category
# ---------------------------------------
@product_bp.route("/category/<int:category_id>")
def category_products(category_id):

    category = Category.query.get_or_404(
        category_id
    )

    products = Product.query.filter_by(
        category_id=category.id
    ).all()


    return render_template(
        "category_products.html",
        category=category,
        products=products
    )


# ---------------------------------------
# Products By District
# ---------------------------------------
@product_bp.route("/district/<int:district_id>")
def district_products(district_id):

    district = District.query.get_or_404(
        district_id
    )

    products = Product.query.filter_by(
        district_id=district.id
    ).all()


    return render_template(
        "district_products.html",
        district=district,
        products=products
    )


# ---------------------------------------
# Products By Taluka
# ---------------------------------------
@product_bp.route("/taluka/<int:taluka_id>")
def taluka_products(taluka_id):

    taluka = Taluka.query.get_or_404(
        taluka_id
    )

    products = Product.query.filter_by(
        taluka_id=taluka.id
    ).all()


    return render_template(
        "taluka_products.html",
        taluka=taluka,
        products=products
    )


# ---------------------------------------
# Products By Village
# ---------------------------------------
@product_bp.route("/village/<int:village_id>")
def village_products(village_id):

    village = Village.query.get_or_404(
        village_id
    )

    products = Product.query.filter_by(
        village_id=village.id
    ).all()


    return render_template(
        "village_products.html",
        village=village,
        products=products
    )


# ---------------------------------------
# My Products (Farmer)
# ---------------------------------------
@product_bp.route("/my-products")
@login_required
def my_products():

    if current_user.role != "farmer":

        flash(
            "Access denied.",
            "danger"
        )

        return redirect(
            url_for("home.home")
        )


    products = Product.query.filter_by(
        farmer_id=current_user.id
    ).order_by(
        Product.id.desc()
    ).all()


    return render_template(
        "farmer/my_products.html",
        products=products
    )


# ---------------------------------------
# Delete Product
# ---------------------------------------
@product_bp.route("/delete/<int:product_id>")
@login_required
def delete_product(product_id):

    product = Product.query.get_or_404(product_id)

    if product.farmer_id != current_user.id:
        flash("You are not authorized to delete this product.", "danger")
        return redirect(url_for("product.my_products"))

    try:
        for session_obj in list(product.sessions):
            for offer in list(session_obj.offers):
                db.session.delete(offer)
            db.session.delete(session_obj)

        for review in list(product.reviews):
            db.session.delete(review)

        for cart_item in list(product.cart_items):
            db.session.delete(cart_item)

        for order in list(product.orders):
            db.session.delete(order)

        db.session.delete(product)
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash("The product could not be deleted because related records are still attached.", "danger")
        return redirect(url_for("product.my_products"))

    flash("Product deleted successfully.", "success")
    return redirect(url_for("product.my_products"))


# ---------------------------------------
# Toggle Product Availability
# ---------------------------------------
@product_bp.route("/toggle-status/<int:product_id>")
@login_required
def toggle_status(product_id):

    product = Product.query.get_or_404(
        product_id
    )


    if product.farmer_id != current_user.id:

        flash(
            "Access denied.",
            "danger"
        )

        return redirect(
            url_for("product.my_products")
        )


    product.status = (
        "Sold"
        if product.status == "Available"
        else "Available"
    )


    db.session.commit()


    flash(
        "Product status updated.",
        "success"
    )


    return redirect(
        url_for("product.my_products")
    )