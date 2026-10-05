from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from models.location import District, Taluka, Village
from models.product import Product
from models.category import Category
from models.notification import Notification
from models.farmer_verification import FarmerVerification
from models.order import Order
from models import db
from utils.voice import set_voice_message
from utils.voice import get_translated_voice_text
from decimal import Decimal, InvalidOperation

import os


farmer_bp = Blueprint(
    "farmer",
    __name__
)
def farmer_verification_required(view):
    from functools import wraps

    @wraps(view)
    def wrapped(*args, **kwargs):
        if current_user.role == "farmer":
            verification = FarmerVerification.query.filter_by(user_id=current_user.id).first()
            if verification and verification.status != "APPROVED":
                session["verification_user_id"] = current_user.id
                flash("Your farmer account is currently under verification. Please wait for Admin approval." if verification.status == "PENDING" else "Your farmer registration request was rejected.", "warning")
                return redirect(url_for("auth.verification_status"))
        return view(*args, **kwargs)

    return wrapped


# ---------------------------------------
# Published APMC Market Rates
# ---------------------------------------
@farmer_bp.route("/apmc/rates")
@login_required
def apmc_rates():
    return redirect(url_for("buyer.apmc_rates", **request.args))


# ---------------------------------------
# Farmer Dashboard
# ---------------------------------------
@farmer_bp.route("/dashboard")
@login_required
@farmer_verification_required
def dashboard():

    if current_user.role != "farmer":
        flash("Access denied.", "danger")
        return redirect(url_for("home.home"))

    total_products = Product.query.filter_by(
        farmer_id=current_user.id
    ).count()

    products = Product.query.filter_by(
        farmer_id=current_user.id
    ).order_by(
        Product.id.desc()
    ).limit(5).all()

    from models.review import Review
    from models.order import Order
    from models.bargaining import BargainingSession

    total_reviews = db.session.query(Review).join(Product).filter(Product.farmer_id == current_user.id).count()

    buyer_ids_orders = db.session.query(Order.buyer_id).filter(Order.farmer_id == current_user.id).distinct().all()
    buyer_ids_bargains = db.session.query(BargainingSession.buyer_id).join(Product).filter(Product.farmer_id == current_user.id).distinct().all()
    unique_buyer_ids = set([b[0] for b in buyer_ids_orders] + [b[0] for b in buyer_ids_bargains])
    total_contacts = len(unique_buyer_ids)

    set_voice_message(session, "voice_farmer_dashboard", fallback="Welcome back. Use My Products to list fresh produce or see buyer orders.")
    return render_template(
        "farmer/dashboard.html",
        total_products=total_products,
        products=products,
        total_reviews=total_reviews,
        total_contacts=total_contacts
    )


# ---------------------------------------
# Customer Reviews
# ---------------------------------------
@farmer_bp.route("/reviews")
@login_required
def reviews():
    if current_user.role != "farmer":
        flash("Access denied.", "danger")
        return redirect(url_for("home.home"))

    from models.review import Review
    from models.product import Product

    reviews = db.session.query(Review).join(Product).filter(Product.farmer_id == current_user.id).order_by(Review.created_at.desc()).all()

    return render_template("farmer/reviews.html", reviews=reviews)


# ---------------------------------------
# Buyer Contacts
# ---------------------------------------
@farmer_bp.route("/contacts")
@login_required
def contacts():
    if current_user.role != "farmer":
        flash("Access denied.", "danger")
        return redirect(url_for("home.home"))

    from models.order import Order
    from models.bargaining import BargainingSession
    from models.user import User
    from models.product import Product

    buyer_ids_orders = [b[0] for b in db.session.query(Order.buyer_id).filter(Order.farmer_id == current_user.id).distinct().all()]
    buyer_ids_bargains = [b[0] for b in db.session.query(BargainingSession.buyer_id).join(Product).filter(Product.farmer_id == current_user.id).distinct().all()]

    unique_buyer_ids = set(buyer_ids_orders + buyer_ids_bargains)

    if unique_buyer_ids:
        buyers = User.query.filter(User.id.in_(unique_buyer_ids)).all()
    else:
        buyers = []

    return render_template("farmer/contacts.html", buyers=buyers)


# ---------------------------------------
# My Products
# ---------------------------------------
@farmer_bp.route("/products")
@login_required
def my_products():

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
# Add Product
# ---------------------------------------
# Add Product
# ---------------------------------------
@farmer_bp.route("/product/add", methods=["GET", "POST"])
@login_required
@farmer_verification_required
def add_product():

    if not current_user.district_id or not current_user.address:
        flash(
            "Please enter your address details in your profile first before listing a product.",
            "warning"
        )
        return redirect(
            url_for("farmer.edit_profile")
        )

    categories = Category.query.all()

    if request.method == "POST":

        form_data = request.form
        title = (form_data.get("title") or form_data.get("product_name") or "").strip()
        category_id = form_data.get("category_id") or form_data.get("category")
        try:
            price = Decimal((form_data.get("price") or "").strip())
            quantity = int((form_data.get("quantity") or "").strip())
            min_price = Decimal((form_data.get("min_price") or "0.00").strip() or "0.00")
        except (InvalidOperation, TypeError, ValueError):
            flash(get_translated_voice_text("invalid_product_numbers", lang=session.get("lang")), "danger")
            return render_template("farmer/add_product.html", categories=categories, form_data=form_data)

        if not title or not category_id or price <= 0 or quantity <= 0 or not form_data.get("unit") or min_price < 0:
            flash(get_translated_voice_text("complete_product_details", lang=session.get("lang")), "danger")
            return render_template("farmer/add_product.html", categories=categories, form_data=form_data)

        image = request.files.get("image")

        filename = ""

        if image and image.filename:
            filename = secure_filename(
                image.filename
            )

            image.save(
                os.path.join(
                    "static/uploads",
                    filename
                )
            )


        product = Product(
            farmer_id=current_user.id,
            title=title,
            category_id=category_id,
            price=price,
            quantity=quantity,
            unit=form_data.get("unit"),
            description=form_data.get("description"),
            district_id=current_user.district_id,
            taluka_id=current_user.taluka_id,
            village_id=current_user.village_id,
            image=filename,
            allow_bargaining=form_data.get("allow_bargaining") == "1",
            min_price=min_price
        )


        db.session.add(product)
        db.session.commit()


        flash(
            "Product added successfully.",
            "success"
        )
        set_voice_message(session, "voice_product_added", fallback="Product added successfully.")

        return redirect(
            url_for("farmer.my_products")
        )


    set_voice_message(session, "voice_add_product", fallback="Complete the product details and submit to list it for buyers.")
    return render_template(
        "farmer/add_product.html",
        categories=categories,
        form_data={}
    )


# ---------------------------------------
# Edit Product
# ---------------------------------------
@farmer_bp.route("/product/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_product(id):

    product = Product.query.get_or_404(id)


    if product.farmer_id != current_user.id:
        flash(
            "Unauthorized access.",
            "danger"
        )

        return redirect(
            url_for("farmer.my_products")
        )


    categories = Category.query.all()


    if request.method == "POST":

        product.title = request.form.get("title") or request.form.get("product_name")
        product.category_id = request.form.get("category_id") or request.form.get("category")
        product.price = request.form.get("price")
        product.quantity = request.form.get("quantity")
        product.unit = request.form.get("unit")
        product.description = request.form.get("description")
        product.district_id = current_user.district_id
        product.taluka_id = current_user.taluka_id
        product.village_id = current_user.village_id
        product.allow_bargaining = request.form.get("allow_bargaining") == "1"
        product.min_price = float(request.form.get("min_price", "0.00") or "0.00")


        image = request.files.get("image")


        if image and image.filename:

            filename = secure_filename(
                image.filename
            )

            image.save(
                os.path.join(
                    "static/uploads",
                    filename
                )
            )

            product.image = filename


        db.session.commit()

        flash(
            "Product updated successfully.",
            "success"
        )
        set_voice_message(session, "voice_product_updated", fallback="Product updated successfully.")

        return redirect(
            url_for("farmer.my_products")
        )


    return render_template(
        "farmer/edit_product.html",
        product=product,
        categories=categories
    )


# ---------------------------------------
# Delete Product
# ---------------------------------------
@farmer_bp.route("/product/delete/<int:id>")
@login_required
def delete_product(id):

    product = Product.query.get_or_404(id)

    if product.farmer_id != current_user.id:
        flash("Unauthorized access.", "danger")
        return redirect(url_for("farmer.my_products"))

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
        return redirect(url_for("farmer.my_products"))

    flash("Product deleted successfully.", "success")
    set_voice_message(session, "voice_product_deleted", fallback="Product deleted successfully.")
    return redirect(url_for("farmer.my_products"))


# ---------------------------------------
# Farmer Profile
# ---------------------------------------
@farmer_bp.route("/profile")
@login_required
def profile():

    return render_template(
        "farmer/profile.html",
        farmer=current_user
    )


# ---------------------------------------
# Edit Profile
# ---------------------------------------
@farmer_bp.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():

    if request.method == "POST":

        current_user.full_name = request.form.get(
            "full_name"
        )

        current_user.phone = request.form.get(
            "phone"
        )

        current_user.address = request.form.get(
            "address"
        )

        district_id = request.form.get("district_id")
        taluka_id = request.form.get("taluka_id")
        village_id = request.form.get("village_id")

        current_user.district_id = int(district_id) if district_id and str(district_id).isdigit() else None
        current_user.taluka_id = int(taluka_id) if taluka_id and str(taluka_id).isdigit() else None
        current_user.village_id = int(village_id) if village_id and str(village_id).isdigit() else None

        db.session.commit()

        flash(
            "Profile updated successfully.",
            "success"
        )
        set_voice_message(session, "voice_profile_updated", fallback="Profile updated successfully.")

        return redirect(
            url_for("farmer.profile")
        )

    districts = District.query.order_by(District.name).all()
    talukas = Taluka.query.filter_by(district_id=current_user.district_id).order_by(Taluka.name).all() if current_user.district_id else []
    villages = Village.query.filter_by(taluka_id=current_user.taluka_id).order_by(Village.name).all() if current_user.taluka_id else []

    set_voice_message(session, "voice_edit_profile", fallback="Update your profile address and contact details so buyers can reach you.")
    return render_template(
        "farmer/edit_profile.html",
        farmer=current_user,
        districts=districts,
        talukas=talukas,
        villages=villages
    )

# ---------------------------------------
# Received Orders
# ---------------------------------------
from models.order import Order

@farmer_bp.route("/orders")
@login_required
def received_orders():
    if current_user.role != "farmer":
        return redirect(url_for("home.home"))
        
    orders = Order.query.filter_by(farmer_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template("farmer/orders.html", orders=orders)


# ---------------------------------------
# Product Details
# ---------------------------------------
@farmer_bp.route("/product/<int:id>")
@login_required
def product_details(id):

    product = Product.query.get_or_404(id)


    if product.farmer_id != current_user.id:

        flash(
            "Unauthorized access.",
            "danger"
        )

        return redirect(
            url_for("farmer.my_products")
        )


    return render_template(
        "farmer/product_details.html",
        product=product
    )

# ---------------------------------------
# Update Order Status
# ---------------------------------------
@farmer_bp.route("/orders/<int:order_id>/status", methods=["POST"])
@login_required
def update_order_status(order_id):
    if current_user.role != "farmer":
        flash("Access denied.", "danger")
        return redirect(url_for("home.home"))

    order = Order.query.get_or_404(order_id)
    if order.farmer_id != current_user.id:
        flash("Unauthorized access.", "danger")
        return redirect(url_for("farmer.received_orders"))

    new_status = request.form.get("status")
    valid_statuses = Order.valid_statuses()
    if new_status not in valid_statuses:
        flash("Invalid order status selected.", "danger")
        return redirect(url_for("farmer.received_orders"))

    order.status = new_status
    if new_status == "Cancelled":
        order.payment_status = "Refunded" if order.payment_status == "Paid" else "Cancelled"
    elif new_status == "Delivered":
        order.payment_status = "Paid" if order.payment_status == "Pending" and order.payment_method == "online_payment" else order.payment_status

    db.session.commit()

    notification = Notification(
        user_id=order.buyer_id,
        title="Order Status Updated",
        message=f"Your order #ORD-{order.id} status is now {new_status}.",
        link=url_for("buyer.my_orders")
    )
    db.session.add(notification)
    db.session.commit()

    flash("Order status updated successfully.", "success")
    return redirect(url_for("farmer.received_orders"))