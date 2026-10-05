from collections import defaultdict
from datetime import date, timedelta

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from models import db
from models.product import Product
from models.category import Category
from models.location import District, Taluka, Village
from models.user import User
from models.notification import Notification
from models.cart import CartItem
from models.order import Order
from models.apmc_rate import APMCRate


buyer_bp = Blueprint("buyer", __name__)


# ---------------------------------------
# Public APMC Market Rates for Buyers
# ---------------------------------------
@buyer_bp.route("/apmc/rates")
@login_required
def apmc_rates():
    period = request.args.get("period", "today")
    selected_date = date.today()

    if period == "yesterday":
        selected_date -= timedelta(days=1)
    elif period == "date":
        try:
            selected_date = date.fromisoformat(request.args.get("date", ""))
        except ValueError:
            period = "today"
            selected_date = date.today()
    else:
        period = "today"

    rates = APMCRate.query.filter(
        APMCRate.rate_date == selected_date
    ).order_by(
        APMCRate.id.desc()
    ).all()
    category_groups = defaultdict(list)
    for rate in rates:
        category_groups[rate.category.name if rate.category else "Uncategorized"].append(rate)

    return render_template(
        "buyer/apmc_rates.html",
        rates=rates,
        category_groups=dict(sorted(category_groups.items())),
        today=date.today(),
        yesterday=date.today() - timedelta(days=1),
        period=period,
        selected_date=selected_date
    )


# ---------------------------------------
# Buyer Dashboard
# ---------------------------------------
@buyer_bp.route("/dashboard")
@login_required
def dashboard():

    if current_user.role != "buyer":
        flash("Access denied.", "danger")
        return redirect(url_for("home.home"))

    total_products = Product.query.count()
    total_categories = Category.query.count()

    latest_products = Product.query.order_by(
        Product.id.desc()
    ).limit(8).all()

    return render_template(
        "buyer/dashboard.html",
        total_products=total_products,
        total_categories=total_categories,
        latest_products=latest_products
    )


# ---------------------------------------
# Browse Products
# ---------------------------------------
@buyer_bp.route("/products")
@login_required
def products():

    products = Product.query.order_by(
        Product.id.desc()
    ).all()

    return render_template(
        "buyer/products.html",
        products=products
    )


# ---------------------------------------
# Product Details
# ---------------------------------------
@buyer_bp.route("/product/<int:product_id>")
@login_required
def product_details(product_id):

    product = Product.query.get_or_404(product_id)

    return render_template(
        "buyer/product_details.html",
        product=product
    )


# ---------------------------------------
# Search Products
# ---------------------------------------
@buyer_bp.route("/search")
@login_required
def search():

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
        "buyer/search_results.html",
        products=products,
        keyword=keyword
    )


# ---------------------------------------
# Filter Products
# ---------------------------------------
@buyer_bp.route("/filter")
@login_required
def filter_products():

    category_id = request.args.get("category")
    district_id = request.args.get("district")
    taluka_id = request.args.get("taluka")
    village_id = request.args.get("village")

    query = Product.query


    if category_id:
        query = query.filter_by(
            category_id=category_id
        )

    if district_id:
        query = query.filter_by(
            district_id=district_id
        )

    if taluka_id:
        query = query.filter_by(
            taluka_id=taluka_id
        )

    if village_id:
        query = query.filter_by(
            village_id=village_id
        )


    products = query.all()

    categories = Category.query.all()
    districts = District.query.all()
    talukas = Taluka.query.all()
    villages = Village.query.all()


    return render_template(
        "buyer/filter_products.html",
        products=products,
        categories=categories,
        districts=districts,
        talukas=talukas,
        villages=villages
    )


# ---------------------------------------
# Farmer Profile
# ---------------------------------------
@buyer_bp.route("/farmer/<int:farmer_id>")
@login_required
def farmer_profile(farmer_id):

    farmer = User.query.get_or_404(
        farmer_id
    )

    products = Product.query.filter_by(
        farmer_id=farmer.id
    ).all()


    return render_template(
        "buyer/farmer_profile.html",
        farmer=farmer,
        products=products
    )


# ---------------------------------------
# Contact Farmer
# ---------------------------------------
@buyer_bp.route("/contact/<int:farmer_id>")
@login_required
def contact_farmer(farmer_id):

    farmer = User.query.get_or_404(
        farmer_id
    )

    return render_template(
        "buyer/contact_farmer.html",
        farmer=farmer
    )


# ---------------------------------------
# Favourite Products
# ---------------------------------------
@buyer_bp.route("/favourites")
@login_required
def favourites():

    flash(
        "Favourite feature will be available soon.",
        "info"
    )

    return render_template(
        "buyer/favourites.html"
    )


# ---------------------------------------
# Buyer Profile
# ---------------------------------------
@buyer_bp.route("/profile")
@login_required
def profile():

    return render_template(
        "buyer/profile.html",
        buyer=current_user
    )


# ---------------------------------------
# Update Buyer Profile
# ---------------------------------------
@buyer_bp.route("/profile/edit", methods=["GET", "POST"])
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

        return redirect(
            url_for("buyer.profile")
        )

    districts = District.query.order_by(District.name).all()
    talukas = Taluka.query.filter_by(district_id=current_user.district_id).order_by(Taluka.name).all() if current_user.district_id else []
    villages = Village.query.filter_by(taluka_id=current_user.taluka_id).order_by(Village.name).all() if current_user.taluka_id else []

    return render_template(
        "buyer/edit_profile.html",
        buyer=current_user,
        districts=districts,
        talukas=talukas,
        villages=villages
    )

# ---------------------------------------
# Shopping Cart
# ---------------------------------------
@buyer_bp.route("/cart")
@login_required
def cart():
    cart_items = CartItem.query.filter_by(buyer_id=current_user.id).all()
    
    total_amount = sum(item.product.price * item.quantity for item in cart_items)
    
    return render_template(
        "buyer/cart.html",
        cart_items=cart_items,
        total_amount=total_amount
    )

@buyer_bp.route("/cart/add/<int:product_id>", methods=["POST"])
@login_required
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    quantity = int(request.form.get("quantity", 1))
    
    if quantity > product.quantity:
        flash(f"Only {product.quantity} {product.unit} available.", "danger")
        return redirect(request.referrer or url_for('buyer.product_details', product_id=product_id))
        
    cart_item = CartItem.query.filter_by(buyer_id=current_user.id, product_id=product_id).first()
    
    if cart_item:
        if cart_item.quantity + quantity > product.quantity:
            flash(f"Cannot add more than available stock.", "danger")
        else:
            cart_item.quantity += quantity
            db.session.commit()
            flash("Cart updated.", "success")
    else:
        new_item = CartItem(buyer_id=current_user.id, product_id=product_id, quantity=quantity)
        db.session.add(new_item)
        db.session.commit()
        flash("Added to cart.", "success")
        
    return redirect(request.referrer or url_for('buyer.cart'))

@buyer_bp.route("/cart/remove/<int:cart_item_id>", methods=["POST"])
@login_required
def remove_from_cart(cart_item_id):
    item = CartItem.query.get_or_404(cart_item_id)
    if item.buyer_id == current_user.id:
        db.session.delete(item)
        db.session.commit()
        flash("Item removed from cart.", "success")
    return redirect(url_for('buyer.cart'))

@buyer_bp.route("/cart/update/<int:cart_item_id>", methods=["POST"])
@login_required
def update_cart(cart_item_id):
    item = CartItem.query.get_or_404(cart_item_id)
    if item.buyer_id == current_user.id:
        qty = int(request.form.get("quantity", 1))
        if qty <= 0:
            db.session.delete(item)
            flash("Item removed.", "success")
        elif qty > item.product.quantity:
            flash(f"Only {item.product.quantity} available.", "danger")
        else:
            item.quantity = qty
            flash("Cart updated.", "success")
        db.session.commit()
    return redirect(url_for('buyer.cart'))

# ---------------------------------------
# Checkout & Orders
# ---------------------------------------
@buyer_bp.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    cart_items = CartItem.query.filter_by(buyer_id=current_user.id).all()
    if not cart_items:
        flash("Your cart is empty.", "warning")
        return redirect(url_for('buyer.cart'))

    total_amount = sum(item.product.price * item.quantity for item in cart_items)

    if request.method == "POST":
        payment_method = request.form.get("payment_method", "cash_on_delivery")
        payment_status = "Paid" if payment_method == "online_payment" else "Pending"

        for item in cart_items:
            if item.quantity > item.product.quantity:
                flash(f"Not enough stock for {item.product.title}.", "danger")
                return redirect(url_for('buyer.cart'))

            order = Order(
                product_id=item.product_id,
                buyer_id=current_user.id,
                farmer_id=item.product.farmer_id,
                quantity=item.quantity,
                original_price=item.product.price,
                total_amount=item.product.price * item.quantity,
                status="Pending" if payment_method != "online_payment" else "Confirmed",
                payment_method=payment_method,
                payment_status=payment_status,
                negotiated_price=item.product.price
            )
            db.session.add(order)

            item.product.quantity = max(0, item.product.quantity - item.quantity)
            if item.product.quantity == 0:
                item.product.status = "Sold"

            db.session.delete(item)

            notif_farmer = Notification(
                user_id=item.product.farmer_id,
                title="New Order Received!",
                message=f"Buyer {current_user.full_name} has placed an order for {item.quantity} {item.product.unit} of {item.product.title}. Total: ₹{item.product.price * item.quantity}.",
                link=url_for("farmer.received_orders")
            )
            notif_buyer = Notification(
                user_id=current_user.id,
                title="Order Placed Successfully!",
                message=f"Your order for {item.quantity} {item.product.unit} of {item.product.title} has been placed successfully. Total: ₹{item.product.price * item.quantity}.",
                link=url_for("buyer.my_orders")
            )
            db.session.add(notif_farmer)
            db.session.add(notif_buyer)

        db.session.commit()
        flash("Order placed successfully!", "success")
        return redirect(url_for('buyer.my_orders'))

    return render_template("buyer/checkout.html", cart_items=cart_items, total_amount=total_amount)

@buyer_bp.route("/orders")
@login_required
def my_orders():
    orders = Order.query.filter_by(buyer_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template("buyer/orders.html", orders=orders)