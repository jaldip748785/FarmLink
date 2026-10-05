from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_required, current_user
from models import db
from models.order import Order
from models.product import Product
from models.bargaining import BargainingSession
from models.notification import Notification
from utils.voice import set_voice_message

order_bp = Blueprint("order", __name__)

@order_bp.route("/checkout/<int:order_id>", methods=["GET", "POST"])
@login_required
def checkout(order_id):
    order = Order.query.get_or_404(order_id)

    if order.buyer_id != current_user.id:
        flash("Unauthorized access.", "danger")
        return redirect(url_for("home.index"))

    if order.status in ["Pending Payment", "Pending", "Paid", "Completed"]:
        if order.payment_status == "Paid" or order.status in ["Paid", "Completed"]:
            flash("Order is already paid or cancelled.", "warning")
            return redirect(url_for("order.success", order_id=order.id))

    if order.status in ["Confirmed", "Processing", "Shipped", "Out for Delivery", "Delivered", "Cancelled"]:
        flash("Order is already in progress or completed.", "warning")
        return redirect(url_for("buyer.my_orders"))

    product = Product.query.get(order.product_id)
    if not product:
        flash("Product no longer exists.", "danger")
        return redirect(url_for("buyer.dashboard"))

    if request.method == "POST":
        if product.quantity < order.quantity:
            flash(f"Insufficient stock. Only {product.quantity} {product.unit} available.", "danger")
            return redirect(url_for("order.checkout", order_id=order.id))

        payment_method = request.form.get("payment_method", "cash_on_delivery")
        order.payment_method = payment_method
        order.payment_status = "Paid" if payment_method == "online_payment" else "Pending"
        order.status = "Confirmed"

        product.quantity -= order.quantity
        if product.quantity <= 0:
            product.quantity = 0
            product.status = "Sold"

        if order.bargaining_session_id:
            bargain_session = BargainingSession.query.get(order.bargaining_session_id)
            if bargain_session:
                bargain_session.status = "COMPLETED"

        db.session.commit()

        notif_farmer = Notification(
            user_id=order.farmer_id,
            title="New Order Received!",
            message=f"Buyer {current_user.full_name} has placed an order for {order.quantity} {product.unit} of {product.title} at ₹{order.negotiated_price or order.original_price}/{product.unit}. Total: ₹{order.total_amount}.",
            link=url_for("farmer.received_orders")
        )
        notif_buyer = Notification(
            user_id=order.buyer_id,
            title="Order Confirmed!",
            message=f"Your order for {order.quantity} {product.unit} of {product.title} has been confirmed. Total: ₹{order.total_amount}.",
            link=url_for("buyer.my_orders")
        )
        db.session.add(notif_farmer)
        db.session.add(notif_buyer)
        db.session.commit()

        flash("Order completed successfully!", "success")
        set_voice_message(session, "voice_order_success", fallback="Order completed successfully.")
        return redirect(url_for("order.success", order_id=order.id))

    return render_template("order/checkout.html", order=order, product=product)

@order_bp.route("/success/<int:order_id>")
@login_required
def success(order_id):
    order = Order.query.get_or_404(order_id)
    if order.buyer_id != current_user.id:
        flash("Unauthorized access.", "danger")
        return redirect(url_for("home.index"))
    return render_template("order/success.html", order=order)
