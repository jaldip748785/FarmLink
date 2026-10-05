from flask import Blueprint, render_template, redirect, url_for, flash, request, session, abort
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from decimal import Decimal
from models import db
from models.product import Product
from models.bargaining import BargainingSession, BargainingOffer
from models.order import Order
from models.notification import Notification

bargaining_bp = Blueprint("bargaining", __name__)

@bargaining_bp.route("/switch-language/<lang>")
def switch_language(lang):
    if lang in ["en", "hi", "gu"]:
        session["lang"] = lang
    # Safely redirect back
    ref = request.referrer
    if ref and ("/switch-language/" not in ref):
        return redirect(ref)
    return redirect(url_for("home.index"))

# ---------------------------------------
# Start Bargaining (Buyer Initiates Offer)
# ---------------------------------------
@bargaining_bp.route("/buyer/bargain/start/<int:product_id>", methods=["POST"])
@login_required
def start_bargain(product_id):
    if current_user.role != "buyer":
        flash("Only buyers can make bargaining offers.", "danger")
        return redirect(url_for("buyer.product_details", product_id=product_id))

    product = Product.query.get_or_404(product_id)
    if product.status != "Available":
        flash("This product is no longer available.", "warning")
        return redirect(url_for("buyer.product_details", product_id=product_id))

    if not product.allow_bargaining:
        flash("Bargaining is not enabled for this product.", "warning")
        return redirect(url_for("buyer.product_details", product_id=product_id))

    try:
        quantity = int(request.form.get("quantity", 0))
        offer_price = Decimal(request.form.get("offer_price", "0"))
    except (ValueError, TypeError):
        flash("Invalid quantity or price value.", "danger")
        return redirect(url_for("buyer.product_details", product_id=product_id))

    # Basic Validations
    if quantity <= 0:
        flash("Quantity must be greater than 0.", "danger")
        return redirect(url_for("buyer.product_details", product_id=product_id))

    if quantity > product.quantity:
        flash(f"Requested quantity exceeds available stock ({product.quantity} {product.unit} available).", "danger")
        return redirect(url_for("buyer.product_details", product_id=product_id))

    if offer_price <= 0:
        flash("Offer price must be greater than ₹0.", "danger")
        return redirect(url_for("buyer.product_details", product_id=product_id))

    # Safeguard: Prevent buyer from bargaining with their own product (if applicable)
    if product.farmer_id == current_user.id:
        flash("You cannot negotiate on your own products.", "danger")
        return redirect(url_for("buyer.product_details", product_id=product_id))

    # Smart Bargaining Rules: Buyer Offer >= Minimum Allowed Offer
    if offer_price < product.min_price:
        flash("Your offer price is too low for the seller to negotiate. Please offer a higher price.", "warning")
        return redirect(url_for("buyer.product_details", product_id=product_id))

    message = request.form.get("message", "").strip()

    # Check if a session already exists between this buyer and farmer for this product
    existing_session = BargainingSession.query.filter_by(
        product_id=product.id,
        buyer_id=current_user.id,
        farmer_id=product.farmer_id
    ).filter(BargainingSession.status.in_(["PENDING", "NEGOTIATING"])).first()

    if existing_session:
        # Check expiration dynamically
        if not existing_session.check_expiration():
            flash("You already have an active negotiation session for this product.", "info")
            return redirect(url_for("bargaining.session_details", session_id=existing_session.id))

    # Create new Bargaining Session
    expires_at = datetime.utcnow() + timedelta(hours=24)
    bargain_session = BargainingSession(
        product_id=product.id,
        buyer_id=current_user.id,
        farmer_id=product.farmer_id,
        quantity=quantity,
        listed_price=product.price,
        status="PENDING",
        expires_at=expires_at
    )
    db.session.add(bargain_session)
    db.session.commit() # commit to get ID

    # Create Initial Offer
    total_amount = offer_price * quantity
    initial_offer = BargainingOffer(
        session_id=bargain_session.id,
        sender_id=current_user.id,
        receiver_id=product.farmer_id,
        offer_price=offer_price,
        quantity=quantity,
        total_amount=total_amount,
        message=message,
        offer_type="INITIAL",
        status="PENDING",
        expires_at=expires_at
    )
    db.session.add(initial_offer)
    db.session.commit()

    # Send Notification to Farmer
    notif = Notification(
        user_id=product.farmer_id,
        title="New Bargaining Request!",
        message=f"Buyer {current_user.full_name} has proposed an offer of ₹{offer_price}/{product.unit} for {quantity} {product.unit} of {product.title}.",
        link=url_for("bargaining.session_details", session_id=bargain_session.id)
    )
    # Send Notification to Buyer
    notif_buyer = Notification(
        user_id=current_user.id,
        title="Offer Submitted",
        message=f"Your offer of ₹{offer_price}/{product.unit} for {quantity} {product.unit} of {product.title} has been sent to seller {product.farmer.full_name}.",
        link=url_for("bargaining.session_details", session_id=bargain_session.id)
    )
    db.session.add(notif)
    db.session.add(notif_buyer)
    db.session.commit()

    flash("Bargaining initiated successfully!", "success")
    return redirect(url_for("bargaining.session_details", session_id=bargain_session.id))


# ---------------------------------------
# Bargain Session Chat & Details
# ---------------------------------------
@bargaining_bp.route("/bargain/session/<int:session_id>")
@login_required
def session_details(session_id):
    bargain_session = BargainingSession.query.get_or_404(session_id)

    # Security: Ensure only the buyer or farmer of this session can access it
    if current_user.id not in [bargain_session.buyer_id, bargain_session.farmer_id]:
        flash("Access Denied.", "danger")
        return redirect(url_for("home.index"))

    # Update expiration status dynamically
    bargain_session.check_expiration()

    # Fetch history of offers
    offers = BargainingOffer.query.filter_by(session_id=bargain_session.id).order_by(BargainingOffer.created_at.asc()).all()

    # Private recommendation calculation for the farmer
    suggestion = None
    if current_user.id == bargain_session.farmer_id and bargain_session.status in ["PENDING", "NEGOTIATING"]:
        # Find latest buyer offer
        latest_buyer_offer = BargainingOffer.query.filter_by(session_id=bargain_session.id, sender_id=bargain_session.buyer_id).order_by(BargainingOffer.created_at.desc()).first()
        if latest_buyer_offer:
            B = latest_buyer_offer.offer_price
            L = bargain_session.listed_price
            M = bargain_session.product.min_price
            
            # Simple formula to suggest a nice price range
            sug_min = max(B + Decimal("1.00"), M)
            sug_max = max(B + Decimal("2.00"), M + (L - M) * Decimal("0.5"))
            if sug_min < L:
                suggestion = f"₹{sug_min:.0f} - ₹{sug_max:.0f}/{bargain_session.product.unit}"
            else:
                suggestion = f"₹{L:.0f}/{bargain_session.product.unit} (listed price)"

    return render_template(
        "bargain_chat.html",
        session=bargain_session,
        offers=offers,
        suggestion=suggestion
    )


# ---------------------------------------
# Send Counter Offer / Response
# ---------------------------------------
@bargaining_bp.route("/bargain/session/<int:session_id>/offer", methods=["POST"])
@login_required
def counter_offer(session_id):
    bargain_session = BargainingSession.query.get_or_404(session_id)

    # Check access
    if current_user.id not in [bargain_session.buyer_id, bargain_session.farmer_id]:
        flash("Access Denied.", "danger")
        return redirect(url_for("home.index"))

    # Check active state
    if bargain_session.check_expiration() or bargain_session.status not in ["PENDING", "NEGOTIATING"]:
        flash("Negotiation is closed or expired.", "warning")
        return redirect(url_for("bargaining.session_details", session_id=session_id))

    try:
        offer_price = Decimal(request.form.get("offer_price", "0"))
        quantity = int(request.form.get("quantity", bargain_session.quantity))
    except (ValueError, TypeError):
        flash("Invalid counter-offer input.", "danger")
        return redirect(url_for("bargaining.session_details", session_id=session_id))

    if offer_price <= 0:
        flash("Offer price must be greater than ₹0.", "danger")
        return redirect(url_for("bargaining.session_details", session_id=session_id))

    # Stock validation
    if quantity <= 0 or quantity > bargain_session.product.quantity:
        flash(f"Quantity must be between 1 and available stock ({bargain_session.product.quantity} {bargain_session.product.unit} available).", "danger")
        return redirect(url_for("bargaining.session_details", session_id=session_id))

    # Verify min price for buyer
    if current_user.id == bargain_session.buyer_id and offer_price < bargain_session.product.min_price:
        flash("Your offer price is too low for the seller to negotiate. Please offer a higher price.", "warning")
        return redirect(url_for("bargaining.session_details", session_id=session_id))

    # Mark all previous pending offers for this session as COUNTERED
    pending_offers = BargainingOffer.query.filter_by(session_id=bargain_session.id, status="PENDING").all()
    for po in pending_offers:
        po.status = "COUNTERED"

    # Set new role parameters
    if current_user.id == bargain_session.buyer_id:
        sender_id = bargain_session.buyer_id
        receiver_id = bargain_session.farmer_id
        notif_user_id = bargain_session.farmer_id
        notif_title = "New Counter Offer Received"
        notif_msg = f"Buyer {current_user.full_name} has countered with ₹{offer_price}/{bargain_session.product.unit} for {quantity} {bargain_session.product.unit}."
    else:
        sender_id = bargain_session.farmer_id
        receiver_id = bargain_session.buyer_id
        notif_user_id = bargain_session.buyer_id
        notif_title = "Seller Sent Counter Offer"
        notif_msg = f"Seller {current_user.full_name} has countered with ₹{offer_price}/{bargain_session.product.unit} for {quantity} {bargain_session.product.unit}."

    # Update session status and variables
    bargain_session.status = "NEGOTIATING"
    bargain_session.quantity = quantity
    expires_at = datetime.utcnow() + timedelta(hours=24)
    bargain_session.expires_at = expires_at
    bargain_session.updated_at = datetime.utcnow()

    # Create new offer
    total_amount = offer_price * quantity
    message = request.form.get("message", "").strip()
    new_offer = BargainingOffer(
        session_id=bargain_session.id,
        sender_id=sender_id,
        receiver_id=receiver_id,
        offer_price=offer_price,
        quantity=quantity,
        total_amount=total_amount,
        message=message,
        offer_type="COUNTER",
        status="PENDING",
        expires_at=expires_at
    )
    db.session.add(new_offer)
    db.session.commit()

    # Send Notification to counterpart
    notif = Notification(
        user_id=notif_user_id,
        title=notif_title,
        message=notif_msg,
        link=url_for("bargaining.session_details", session_id=bargain_session.id)
    )
    db.session.add(notif)
    db.session.commit()

    flash("Counter offer submitted successfully.", "success")
    return redirect(url_for("bargaining.session_details", session_id=bargain_session.id))


# ---------------------------------------
# Accept Negotiation Offer
# ---------------------------------------
@bargaining_bp.route("/bargain/session/<int:session_id>/accept", methods=["POST"])
@login_required
def accept_offer(session_id):
    bargain_session = BargainingSession.query.get_or_404(session_id)

    # Check access
    if current_user.id not in [bargain_session.buyer_id, bargain_session.farmer_id]:
        flash("Access Denied.", "danger")
        return redirect(url_for("home.index"))

    # Check status
    if bargain_session.check_expiration() or bargain_session.status not in ["PENDING", "NEGOTIATING"]:
        flash("Negotiation is closed or expired.", "warning")
        return redirect(url_for("bargaining.session_details", session_id=session_id))

    # Get the latest pending offer
    latest_offer = BargainingOffer.query.filter_by(session_id=bargain_session.id, status="PENDING").order_by(BargainingOffer.created_at.desc()).first()
    if not latest_offer:
        flash("No active offer found to accept.", "warning")
        return redirect(url_for("bargaining.session_details", session_id=session_id))

    # Safety double-check: cannot accept your own offer
    if latest_offer.sender_id == current_user.id:
        flash("You cannot accept your own offer. You must wait for the other party to respond.", "warning")
        return redirect(url_for("bargaining.session_details", session_id=session_id))

    # Double check stock
    if bargain_session.quantity > bargain_session.product.quantity:
        flash(f"Cannot accept deal. Available stock ({bargain_session.product.quantity}) is less than agreed quantity ({bargain_session.quantity}).", "danger")
        return redirect(url_for("bargaining.session_details", session_id=session_id))

    # Accept Offer and Session
    latest_offer.status = "ACCEPTED"
    bargain_session.status = "ACCEPTED"
    bargain_session.final_price = latest_offer.offer_price
    bargain_session.updated_at = datetime.utcnow()

    # Create Draft Order
    order = Order(echo "# FarmLink" >> README.md
        product_id=bargain_session.product_id,
        buyer_id=bargain_session.buyer_id,
        farmer_id=bargain_session.farmer_id,
        quantity=bargain_session.quantity,
        original_price=bargain_session.product.price,
        negotiated_price=bargain_session.final_price,
        total_amount=latest_offer.total_amount,
        bargaining_session_id=bargain_session.id,
        status="Pending",
        payment_method="cash_on_delivery",
        payment_status="Pending"
    )
    db.session.add(order)
    db.session.commit() # Commit to get order.id

    # Create Acceptance Offer Log (to show in log timeline)
    acceptance_log = BargainingOffer(
        session_id=bargain_session.id,
        sender_id=current_user.id,
        receiver_id=latest_offer.sender_id,
        offer_price=bargain_session.final_price,
        quantity=bargain_session.quantity,
        total_amount=latest_offer.total_amount,
        message="Deal accepted!",
        offer_type="ACCEPTANCE",
        status="ACCEPTED",
        created_at=datetime.utcnow()
    )
    db.session.add(acceptance_log)

    # Notifications
    if current_user.id == bargain_session.buyer_id:
        # Buyer accepted farmer's offer
        notif_user_id = bargain_session.farmer_id
        notif_title = "Counter Offer Accepted!"
        notif_msg = f"Buyer {current_user.full_name} accepted your counter offer of ₹{bargain_session.final_price}/{bargain_session.product.unit} for {bargain_session.quantity} {bargain_session.product.unit} of {bargain_session.product.title}. Checkout order created."
        notification_link = url_for("order.checkout", order_id=order.id)
    else:
        # Farmer accepted buyer's offer
        notif_user_id = bargain_session.buyer_id
        notif_title = "Bargain Offer Accepted!"
        notif_msg = f"Seller {current_user.full_name} accepted your offer of ₹{bargain_session.final_price}/{bargain_session.product.unit} for {bargain_session.quantity} {bargain_session.product.unit} of {bargain_session.product.title}. You can now proceed to checkout."
        notification_link = url_for("order.checkout", order_id=order.id)

    notif = Notification(
        user_id=notif_user_id,
        title=notif_title,
        message=notif_msg,
        link=notification_link
    )
    db.session.add(notif)
    db.session.commit()

    flash("Deal Accepted successfully! Order draft generated.", "success")
    return redirect(url_for("bargaining.session_details", session_id=bargain_session.id))


# ---------------------------------------
# Reject Negotiation Offer
# ---------------------------------------
@bargaining_bp.route("/bargain/session/<int:session_id>/reject", methods=["POST"])
@login_required
def reject_offer(session_id):
    bargain_session = BargainingSession.query.get_or_404(session_id)

    # Check access
    if current_user.id not in [bargain_session.buyer_id, bargain_session.farmer_id]:
        flash("Access Denied.", "danger")
        return redirect(url_for("home.index"))

    # Check status
    if bargain_session.check_expiration() or bargain_session.status not in ["PENDING", "NEGOTIATING"]:
        flash("Negotiation is closed or expired.", "warning")
        return redirect(url_for("bargaining.session_details", session_id=session_id))

    latest_offer = BargainingOffer.query.filter_by(session_id=bargain_session.id, status="PENDING").order_by(BargainingOffer.created_at.desc()).first()
    if latest_offer:
        latest_offer.status = "REJECTED"

    bargain_session.status = "REJECTED"
    bargain_session.updated_at = datetime.utcnow()

    # Log rejection offer record
    rejection_log = BargainingOffer(
        session_id=bargain_session.id,
        sender_id=current_user.id,
        receiver_id=latest_offer.sender_id if latest_offer else (bargain_session.farmer_id if current_user.id == bargain_session.buyer_id else bargain_session.buyer_id),
        offer_price=Decimal("0.00"),
        quantity=bargain_session.quantity,
        total_amount=Decimal("0.00"),
        message="Offer rejected.",
        offer_type="REJECTION",
        status="REJECTED",
        created_at=datetime.utcnow()
    )
    db.session.add(rejection_log)

    # Notification
    other_party_id = bargain_session.farmer_id if current_user.id == bargain_session.buyer_id else bargain_session.buyer_id
    notif = Notification(
        user_id=other_party_id,
        title="Bargain Offer Rejected",
        message=f"{current_user.full_name} has rejected the offer on {bargain_session.product.title}.",
        link=url_for("bargaining.session_details", session_id=bargain_session.id)
    )
    db.session.add(notif)
    db.session.commit()

    flash("Negotiation rejected.", "warning")
    return redirect(url_for("bargaining.session_details", session_id=session_id))


# ---------------------------------------
# Cancel Negotiation
# ---------------------------------------
@bargaining_bp.route("/bargain/session/<int:session_id>/cancel", methods=["POST"])
@login_required
def cancel_offer(session_id):
    bargain_session = BargainingSession.query.get_or_404(session_id)

    # Check access
    if current_user.id not in [bargain_session.buyer_id, bargain_session.farmer_id]:
        flash("Access Denied.", "danger")
        return redirect(url_for("home.index"))

    # Check status
    if bargain_session.check_expiration() or bargain_session.status not in ["PENDING", "NEGOTIATING"]:
        flash("Negotiation is closed or expired.", "warning")
        return redirect(url_for("bargaining.session_details", session_id=session_id))

    latest_offer = BargainingOffer.query.filter_by(session_id=bargain_session.id, status="PENDING").order_by(BargainingOffer.created_at.desc()).first()
    if latest_offer:
        latest_offer.status = "CANCELLED"

    bargain_session.status = "CANCELLED"
    bargain_session.updated_at = datetime.utcnow()

    # Log cancellation
    cancellation_log = BargainingOffer(
        session_id=bargain_session.id,
        sender_id=current_user.id,
        receiver_id=bargain_session.farmer_id if current_user.id == bargain_session.buyer_id else bargain_session.buyer_id,
        offer_price=Decimal("0.00"),
        quantity=bargain_session.quantity,
        total_amount=Decimal("0.00"),
        message="Negotiation cancelled.",
        offer_type="CANCEL",
        status="CANCELLED",
        created_at=datetime.utcnow()
    )
    db.session.add(cancellation_log)

    # Notification
    other_party_id = bargain_session.farmer_id if current_user.id == bargain_session.buyer_id else bargain_session.buyer_id
    notif = Notification(
        user_id=other_party_id,
        title="Bargain Session Cancelled",
        message=f"{current_user.full_name} has cancelled the negotiation session on {bargain_session.product.title}.",
        link=url_for("bargaining.session_details", session_id=bargain_session.id)
    )
    db.session.add(notif)
    db.session.commit()

    flash("Negotiation cancelled.", "warning")
    return redirect(url_for("bargaining.session_details", session_id=session_id))


# ---------------------------------------
# Buyer Dashbaord: My Bargains
# ---------------------------------------
@bargaining_bp.route("/buyer/bargains")
@login_required
def buyer_bargains():
    if current_user.role != "buyer":
        flash("Access Denied.", "danger")
        return redirect(url_for("home.index"))

    status_filter = request.args.get("status", "all")
    query = BargainingSession.query.filter_by(buyer_id=current_user.id)
    
    # Process dynamically pending expirations
    sessions = query.all()
    for s in sessions:
        s.check_expiration()

    if status_filter != "all":
        query = query.filter_by(status=status_filter.upper())

    sessions = query.order_by(BargainingSession.updated_at.desc()).all()
    return render_template("buyer/bargains.html", sessions=sessions, current_filter=status_filter)


# ---------------------------------------
# Farmer Dashboard: Bargaining Requests
# ---------------------------------------
@bargaining_bp.route("/farmer/bargains")
@login_required
def farmer_bargains():
    if current_user.role != "farmer":
        flash("Access Denied.", "danger")
        return redirect(url_for("home.index"))

    status_filter = request.args.get("status", "all")
    query = BargainingSession.query.filter_by(farmer_id=current_user.id)
    
    # Process dynamically pending expirations
    sessions = query.all()
    for s in sessions:
        s.check_expiration()

    if status_filter != "all":
        query = query.filter_by(status=status_filter.upper())

    sessions = query.order_by(BargainingSession.updated_at.desc()).all()
    return render_template("farmer/bargains.html", sessions=sessions, current_filter=status_filter)
