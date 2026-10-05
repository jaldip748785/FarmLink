import os
from datetime import datetime
from pathlib import Path
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app, send_file
from functools import wraps
from werkzeug.security import generate_password_hash

from models.user import User
from models.product import Product
from models.category import Category
from models.location import District, Taluka, Village
from models.bargaining import BargainingSession, BargainingOffer
from models import db
from models.apmc_rate import APMCRate
from models.farmer_verification import FarmerVerification
from models.notification import Notification
from utils.apmc_sync import sync_apmc_rates_from_api


from flask_login import login_user, logout_user, current_user


admin_bp = Blueprint(
    "admin",
    __name__,
    template_folder="../templates/admin"
)


def get_admin_credentials():
    email = os.getenv("ADMIN_EMAIL", current_app.config.get("ADMIN_EMAIL", "farmerlink87@gmail.com"))
    password = os.getenv("ADMIN_PASSWORD", current_app.config.get("ADMIN_PASSWORD", "farmlink@123"))
    return email, password


def is_valid_admin_login(username, password):
    admin_email, admin_password = get_admin_credentials()
    normalized_username = (username or "").strip().lower()
    normalized_email = (admin_email or "").strip().lower()
    normalized_password = (password or "").strip()
    expected_password = (admin_password or "").strip()
    return normalized_username in {normalized_email, "admin"} and normalized_password.lower() == expected_password.lower()


def get_admin_user():
    admin_email, _ = get_admin_credentials()
    admin_user = User.query.filter_by(role="admin").first()
    if not admin_user:
        admin_user = User.query.filter_by(email=admin_email).first()
    if admin_user and admin_user.role != "admin":
        admin_user.role = "admin"
        db.session.commit()
    return admin_user


def update_env_variable(key, value):
    env_path = ".env"
    lines = []
    found = False
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        for i, line in enumerate(lines):
            if line.startswith(f"{key}="):
                lines[i] = f"{key}={value}\n"
                found = True
                break
    if not found:
        lines.append(f"{key}={value}\n")
    
    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    
    os.environ[key] = str(value)


# ---------------------------------------
# Admin Login Required Decorator
# ---------------------------------------
def admin_login_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):

        if not current_user.is_authenticated or current_user.role != "admin":
            logout_user()
            session.pop("admin_id", None)
            session.pop("admin_name", None)
            flash("Please login as Admin.", "warning")
            return redirect(url_for("admin.login"))

        return f(*args, **kwargs)

    return decorated_function


# ---------------------------------------
# Admin Login
# ---------------------------------------
@admin_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username") or request.form.get("email")
        password = request.form.get("password")

        if is_valid_admin_login(username, password):

            logout_user()
            session.pop("admin_id", None)
            session.pop("admin_name", None)

            admin_user = get_admin_user()
            if not admin_user:
                admin_user = User(
                    full_name="Administrator",
                    email=get_admin_credentials()[0],
                    phone="0000000000",
                    password=generate_password_hash(get_admin_credentials()[1]),
                    role="admin"
                )
                db.session.add(admin_user)
                db.session.commit()
            if admin_user:
                login_user(admin_user)

            session["admin_id"] = 1
            session["admin_name"] = admin_user.full_name if admin_user else "Administrator"

            flash("Login Successful!", "success")

            return redirect(
                url_for("admin.dashboard")
            )

        flash(
            "Invalid Username or Password.",
            "danger"
        )

    return render_template(
        "admin/login.html"
    )


# ---------------------------------------
# Logout
# ---------------------------------------
@admin_bp.route("/logout")
def logout():

    logout_user()
    session.pop("admin_id", None)
    session.pop("admin_name", None)

    flash(
        "Logged out successfully.",
        "success"
    )

    return redirect(
        url_for("admin.login")
    )


# ---------------------------------------
# Dashboard
# ---------------------------------------
@admin_bp.route("/dashboard")
@admin_login_required
def dashboard():

    total_users = User.query.count()
    total_farmers = User.query.filter_by(role="farmer").count()
    total_buyers = User.query.filter_by(role="buyer").count()
    total_products = Product.query.count()
    total_categories = Category.query.count()
    pending_verifications = FarmerVerification.query.filter_by(status="PENDING").count()
    recent_products = Product.query.order_by(Product.id.desc()).limit(5).all()

    return render_template(
        "admin/dashboard.html",
        total_users=total_users,
        total_farmers=total_farmers,
        total_buyers=total_buyers,
        total_products=total_products,
        total_categories=total_categories,
        recent_products=recent_products,
        pending_verifications=pending_verifications
    )


@admin_bp.route("/farmer-verifications")
@admin_login_required
def farmer_verifications():
    verifications = FarmerVerification.query.order_by(FarmerVerification.submitted_at.desc()).all()
    return render_template("admin/farmer_verifications.html", verifications=verifications)


@admin_bp.route("/farmer-verification/<int:verification_id>")
@admin_login_required
def farmer_verification_detail(verification_id):
    verification = FarmerVerification.query.get_or_404(verification_id)
    return render_template("admin/farmer_verification_detail.html", verification=verification)


@admin_bp.route("/farmer-verification/<int:verification_id>/document")
@admin_login_required
def farmer_verification_document(verification_id):
    verification = FarmerVerification.query.get_or_404(verification_id)
    document_type = request.args.get("type", "7/12")
    document_paths = verification.uploaded_8a_documents if document_type in {"8-A", "Adhar card"} else verification.uploaded_712_documents
    document_index = request.args.get("index", 0, type=int)
    if document_index < 0 or document_index >= len(document_paths):
        document_index = 0
    document_relative_path = document_paths[document_index]
    if not document_relative_path:
        document_relative_path = verification.document_path
    document_root = (Path(current_app.instance_path) / "verification_documents").resolve()
    document_path = (Path(current_app.instance_path) / document_relative_path).resolve()
    if document_root not in document_path.parents or not document_path.is_file():
        flash("The verification document is unavailable.", "danger")
        return redirect(url_for("admin.farmer_verification_detail", verification_id=verification.id))
    return send_file(document_path, as_attachment=False)


@admin_bp.route("/farmer-verification/<int:verification_id>/approve", methods=["POST"])
@admin_login_required
def approve_farmer_verification(verification_id):
    verification = FarmerVerification.query.get_or_404(verification_id)
    verification.status = "APPROVED"
    verification.reviewed_at = datetime.utcnow()
    verification.reviewed_by = current_user.id
    verification.rejection_reason = None
    db.session.add(Notification(
        user_id=verification.user_id,
        title="Farmer verification approved",
        message="Your farmer verification has been approved. You can now login.",
        link=url_for("auth.login")
    ))
    db.session.commit()
    flash("Farmer verification approved successfully.", "success")
    return redirect(url_for("admin.farmer_verification_detail", verification_id=verification.id))


@admin_bp.route("/farmer-verification/<int:verification_id>/reject", methods=["POST"])
@admin_login_required
def reject_farmer_verification(verification_id):
    verification = FarmerVerification.query.get_or_404(verification_id)
    reason = (request.form.get("rejection_reason") or "").strip()
    if not reason:
        flash("A rejection reason is required.", "danger")
        return redirect(url_for("admin.farmer_verification_detail", verification_id=verification.id))
    verification.status = "REJECTED"
    verification.reviewed_at = datetime.utcnow()
    verification.reviewed_by = current_user.id
    verification.rejection_reason = reason
    db.session.add(Notification(
        user_id=verification.user_id,
        title="Farmer verification rejected",
        message="Your farmer verification request was rejected. Please check the reason.",
        link=url_for("auth.verification_status")
    ))
    db.session.commit()
    flash("Farmer verification rejected successfully.", "success")
    return redirect(url_for("admin.farmer_verification_detail", verification_id=verification.id))


# ---------------------------------------
# Manage Users
# ---------------------------------------
@admin_bp.route("/users")
@admin_login_required
def users():

    users_list = User.query.order_by(
        User.id.desc()
    ).all()

    return render_template(
        "admin/users.html",
        users=users_list
    )


# ---------------------------------------
# Add User
# ---------------------------------------
@admin_bp.route("/user/add", methods=["GET", "POST"])
@admin_login_required
def add_user():

    districts = District.query.order_by(District.name).all()

    if request.method == "POST":

        full_name = request.form.get("full_name") or "Administrator"
        email = request.form.get("email")
        phone = request.form.get("phone") or "9099909990    "
        password = request.form.get("password")
        role = request.form.get("role", "buyer")

        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "warning")
            return redirect(url_for("admin.add_user"))

        user = User(
            full_name=full_name,
            email=email,
            phone=phone,
            password=generate_password_hash(password),
            role=role
        )

        db.session.add(user)
        db.session.commit()

        flash("User added successfully.", "success")
        return redirect(url_for("admin.users"))

    return render_template(
        "admin/add_user.html",
        districts=districts
    )


# ---------------------------------------
# Edit User
# ---------------------------------------
@admin_bp.route("/user/edit/<int:user_id>", methods=["GET", "POST"])
@admin_login_required
def edit_user(user_id):

    user = User.query.get_or_404(user_id)
    districts = District.query.order_by(District.name).all()
    talukas = Taluka.query.filter_by(district_id=user.district_id).order_by(Taluka.name).all() if user.district_id else []
    villages = Village.query.filter_by(taluka_id=user.taluka_id).order_by(Village.name).all() if user.taluka_id else []

    if request.method == "POST":

        new_phone = (request.form.get("phone") or "").strip()
        existing_phone_user = User.query.filter(User.id != user.id, User.phone == new_phone).first() if new_phone else None
        if existing_phone_user:
            flash("Phone number already exists for another user.", "warning")
            return redirect(url_for("admin.users"))

        user.full_name = request.form.get("full_name") or user.full_name
        user.email = request.form.get("email") or user.email
        user.phone = new_phone or user.phone
        user.role = request.form.get("role") or user.role

        new_password = request.form.get("password")
        if new_password:
            user.password = generate_password_hash(new_password)

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash("The user could not be updated because of a data conflict.", "danger")
            return redirect(url_for("admin.users"))

        flash("User details updated successfully.", "success")
        return redirect(url_for("admin.users"))

    return render_template(
        "admin/edit_user.html",
        user=user,
        districts=districts,
        talukas=talukas,
        villages=villages
    )


# ---------------------------------------
# Delete User
# ---------------------------------------
@admin_bp.route("/user/delete/<int:user_id>")
@admin_login_required
def delete_user(user_id):

    user = User.query.get_or_404(user_id)

    if user.role == "admin" or user.email == get_admin_credentials()[0]:
        flash("The administrator account cannot be deleted.", "warning")
        return redirect(url_for("admin.users"))

    try:
        if user.role == "farmer":
            for product in list(user.products_list):
                for session_obj in list(product.sessions):
                    for offer in list(session_obj.offers):
                        db.session.delete(offer)
                    db.session.delete(session_obj)
                db.session.delete(product)

        if user.role == "buyer":
            for session_obj in list(user.buyer_sessions):
                for offer in list(session_obj.offers):
                    db.session.delete(offer)
                db.session.delete(session_obj)

        for session_obj in list(user.farmer_sessions):
            for offer in list(session_obj.offers):
                db.session.delete(offer)
            db.session.delete(session_obj)

        db.session.delete(user)
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash("The user could not be deleted because related records are still attached.", "danger")
        return redirect(url_for("admin.users"))

    flash(
        "User deleted successfully.",
        "success"
    )

    return redirect(
        url_for("admin.users")
    )


# ---------------------------------------
# Manage APMC Rates
# ---------------------------------------
@admin_bp.route("/apmc/rates")
@admin_login_required
def apmc_rates():
    rates = APMCRate.query.order_by(APMCRate.rate_date.desc(), APMCRate.id.desc()).all()
    return render_template(
        "admin/apmc_rates.html",
        rates=rates,
        api_key=current_app.config.get("OGD_API_KEY", "") or os.getenv("OGD_API_KEY", "")
    )


@admin_bp.route("/apmc/rate/add", methods=["GET", "POST"])
@admin_login_required
def add_apmc_rate():
    districts = District.query.order_by(District.name).all()
    categories = Category.query.order_by(Category.name).all()
    selected_category_id = request.args.get("category_id", "")

    if request.method == "POST":
        try:
            rate_date_value = request.form.get("rate_date") or None
            rate_date = None
            if rate_date_value:
                from datetime import datetime
                rate_date = datetime.strptime(rate_date_value, "%Y-%m-%d").date()
            rate = APMCRate(
                commodity_name=request.form.get("commodity_name", "").strip(),
                market_name=request.form.get("market_name", "").strip(),
                state=request.form.get("state", "").strip(),
                category_id=request.form.get("category_id") or None,
                district_id=request.form.get("district_id") or None,
                modal_price=float(request.form.get("modal_price", 0) or 0),
                minimum_price=float(request.form.get("minimum_price", 0) or 0),
                maximum_price=float(request.form.get("maximum_price", 0) or 0),
                unit=request.form.get("unit", "kg").strip() or "kg",
                rate_date=rate_date,
                source=request.form.get("source", "AGMARKNET").strip() or "AGMARKNET"
            )
            db.session.add(rate)
            db.session.commit()
            flash("APMC rate added successfully.", "success")
            return redirect(url_for("admin.apmc_rates"))
        except Exception:
            db.session.rollback()
            flash("The APMC rate could not be saved. Please review the values and try again.", "danger")
            return redirect(url_for("admin.apmc_rates"))

    return render_template(
        "admin/add_apmc_rate.html",
        districts=districts,
        categories=categories,
        selected_category_id=selected_category_id
    )


@admin_bp.route("/apmc/sync", methods=["POST"])
@admin_login_required
def sync_apmc_rates():
    try:
        result = sync_apmc_rates_from_api()
        flash(f"APMC data synced successfully. Imported {result['imported']} and updated {result['updated']} rates.", "success")
    except Exception as exc:
        flash(f"APMC sync failed: {exc}", "danger")
    return redirect(url_for("admin.apmc_rates"))


# ---------------------------------------
# Manage Products
# ---------------------------------------
@admin_bp.route("/products")
@admin_login_required
def products():

    products_list = Product.query.order_by(
        Product.id.desc()
    ).all()

    return render_template(
        "admin/products.html",
        products=products_list
    )


# ---------------------------------------
# Add Product (Admin)
# ---------------------------------------
@admin_bp.route("/product/add", methods=["GET", "POST"])
@admin_login_required
def add_product():

    categories = Category.query.order_by(Category.name).all()
    farmers = User.query.filter_by(role="farmer").all()

    if request.method == "POST":

        farmer_id = request.form.get("farmer_id")
        farmer = User.query.get(farmer_id) if farmer_id else None

        image = request.files.get("image")
        filename = ""
        if image and image.filename:
            from werkzeug.utils import secure_filename
            filename = secure_filename(image.filename)
            image.save(os.path.join("static/uploads", filename))

        product = Product(
            farmer_id=int(farmer_id) if farmer_id else None,
            title=request.form.get("title"),
            category_id=request.form.get("category_id"),
            price=request.form.get("price"),
            quantity=request.form.get("quantity"),
            unit=request.form.get("unit"),
            description=request.form.get("description"),
            district_id=farmer.district_id if farmer else None,
            taluka_id=farmer.taluka_id if farmer else None,
            village_id=farmer.village_id if farmer else None,
            status=request.form.get("status", "Available"),
            image=filename,
            allow_bargaining=request.form.get("allow_bargaining") == "1",
            min_price=float(request.form.get("min_price", "0.00") or "0.00")
        )

        db.session.add(product)
        db.session.commit()

        flash("Product added successfully.", "success")
        return redirect(url_for("admin.products"))

    return render_template(
        "admin/add_product.html",
        categories=categories,
        farmers=farmers
    )


# ---------------------------------------
# Edit Product (Admin)
# ---------------------------------------
@admin_bp.route("/product/edit/<int:product_id>", methods=["GET", "POST"])
@admin_login_required
def edit_product(product_id):

    product = Product.query.get_or_404(product_id)
    categories = Category.query.order_by(Category.name).all()
    farmers = User.query.filter_by(role="farmer").all()

    if request.method == "POST":

        product.title = request.form.get("title")
        product.category_id = request.form.get("category_id")
        product.farmer_id = request.form.get("farmer_id")
        product.price = request.form.get("price")
        product.quantity = request.form.get("quantity")
        product.unit = request.form.get("unit")
        product.description = request.form.get("description")
        product.status = request.form.get("status")
        product.allow_bargaining = request.form.get("allow_bargaining") == "1"
        product.min_price = float(request.form.get("min_price", "0.00") or "0.00")

        farmer = User.query.get(product.farmer_id) if product.farmer_id else None
        if farmer:
            product.district_id = farmer.district_id
            product.taluka_id = farmer.taluka_id
            product.village_id = farmer.village_id

        image = request.files.get("image")
        if image and image.filename:
            from werkzeug.utils import secure_filename
            filename = secure_filename(image.filename)
            image.save(os.path.join("static/uploads", filename))
            product.image = filename

        db.session.commit()

        flash("Product updated successfully.", "success")
        return redirect(url_for("admin.products"))

    return render_template(
        "admin/edit_product.html",
        product=product,
        categories=categories,
        farmers=farmers
    )


# ---------------------------------------
# Delete Product
# ---------------------------------------
@admin_bp.route("/product/delete/<int:product_id>")
@admin_login_required
def delete_product(product_id):

    product = Product.query.get_or_404(product_id)

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
        return redirect(url_for("admin.products"))

    flash("Product deleted successfully.", "success")
    return redirect(url_for("admin.products"))


# ---------------------------------------
# Locations
# ---------------------------------------
@admin_bp.route("/locations")
@admin_login_required
def locations():
    return render_template(
        "admin/locations.html",
        districts=District.query.order_by(District.name).all(),
        talukas=Taluka.query.order_by(Taluka.district_id, Taluka.name).all(),
        villages=Village.query.order_by(Village.district_id, Village.taluka_id, Village.name).all()
    )


@admin_bp.route("/location/add", methods=["POST"])
@admin_login_required
def add_location():
    location_type = request.form.get("location_type")
    name = (request.form.get("name") or "").strip()

    if not name:
        flash("Location name is required.", "warning")
        return redirect(url_for("admin.locations"))

    try:
        if location_type == "district":
            db.session.add(District(name=name))
        elif location_type == "taluka":
            district_id = request.form.get("district_id")
            if not district_id:
                raise ValueError("District is required for a taluka.")
            db.session.add(Taluka(district_id=district_id, name=name))
        elif location_type == "village":
            district_id = request.form.get("district_id")
            taluka_id = request.form.get("taluka_id")
            if not district_id or not taluka_id:
                raise ValueError("District and taluka are required for a village.")
            db.session.add(Village(district_id=district_id, taluka_id=taluka_id, name=name))
        else:
            raise ValueError("Select a valid location type.")

        db.session.commit()
        flash("Location added successfully.", "success")
    except Exception:
        db.session.rollback()
        flash("This location already exists or the submitted details are invalid.", "danger")

    return redirect(url_for("admin.locations"))


# ---------------------------------------
# Categories
# ---------------------------------------
@admin_bp.route("/categories")
@admin_login_required
def categories():

    categories = Category.query.order_by(
        Category.name
    ).all()

    return render_template(
        "admin/categories.html",
        categories=categories
    )


# ---------------------------------------
# Add Category
# ---------------------------------------
@admin_bp.route("/category/add", methods=["GET", "POST"])
@admin_login_required
def add_category():

    if request.method == "POST":

        category = Category(
            name=request.form.get("name"),
            description=request.form.get("description")
        )

        db.session.add(category)
        db.session.commit()

        flash(
            "Category added successfully.",
            "success"
        )

        return redirect(
            url_for("admin.categories")
        )

    return render_template(
        "admin/add_category.html"
    )


# ---------------------------------------
# Edit Category
# ---------------------------------------
@admin_bp.route("/category/edit/<int:id>", methods=["GET", "POST"])
@admin_login_required
def edit_category(id):

    category = Category.query.get_or_404(id)

    if request.method == "POST":

        category.name = request.form.get("name")
        category.description = request.form.get("description")

        db.session.commit()

        flash(
            "Category updated successfully.",
            "success"
        )

        return redirect(
            url_for("admin.categories")
        )

    return render_template(
        "admin/edit_category.html",
        category=category
    )


# ---------------------------------------
# Delete Category
# ---------------------------------------
@admin_bp.route("/category/delete/<int:id>")
@admin_login_required
def delete_category(id):

    category = Category.query.get_or_404(id)

    try:
        for product in list(category.products_list):
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

        db.session.delete(category)
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash("The category could not be deleted because related records are still attached.", "danger")
        return redirect(url_for("admin.categories"))

    flash(
        "Category deleted successfully.",
        "success"
    )

    return redirect(
        url_for("admin.categories")
    )



# ---------------------------------------
# Settings
# ---------------------------------------
@admin_bp.route("/settings", methods=["GET", "POST"])
@admin_login_required
def settings():

    admin_email, admin_password = get_admin_credentials()

    if request.method == "POST":

        new_email = request.form.get("email")
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        if current_password != admin_password:
            flash("Current password is incorrect.", "danger")
            return redirect(url_for("admin.settings"))

        if new_password:
            if new_password != confirm_password:
                flash("New passwords do not match.", "danger")
                return redirect(url_for("admin.settings"))
            update_env_variable("ADMIN_PASSWORD", new_password)
            current_app.config["ADMIN_PASSWORD"] = new_password

        if new_email and new_email != admin_email:
            update_env_variable("ADMIN_EMAIL", new_email)
            current_app.config["ADMIN_EMAIL"] = new_email

        # Also sync with User model if an admin record exists in DB
        admin_user = User.query.filter_by(role="admin").first()
        if admin_user:
            if new_email:
                admin_user.email = new_email
            if new_password:
                admin_user.password = generate_password_hash(new_password)
            db.session.commit()

        flash("Admin email and password updated successfully!", "success")
        return redirect(url_for("admin.settings"))

    return render_template(
        "admin/settings.html",
        admin_email=admin_email
    )


# ---------------------------------------
# Bargaining Analytics (Admin)
# ---------------------------------------
@admin_bp.route("/bargaining")
@admin_login_required
def bargaining_analytics():
    from models.bargaining import BargainingSession
    from sqlalchemy import func

    # Total and status counts
    total_negotiations = BargainingSession.query.count()
    active_negotiations = BargainingSession.query.filter(BargainingSession.status.in_(["PENDING", "NEGOTIATING"])).count()
    successful_negotiations = BargainingSession.query.filter(BargainingSession.status.in_(["ACCEPTED", "COMPLETED"])).count()
    rejected_negotiations = BargainingSession.query.filter_by(status="REJECTED").count()
    expired_negotiations = BargainingSession.query.filter_by(status="EXPIRED").count()

    # Average discounts and prices
    avg_discount = 0.0
    avg_negotiated_price = 0.0
    
    successful_sessions = BargainingSession.query.filter(BargainingSession.status.in_(["ACCEPTED", "COMPLETED"])).all()
    if successful_sessions:
        total_discount = sum(float(s.listed_price - s.final_price) for s in successful_sessions if s.final_price)
        total_final_price = sum(float(s.final_price) for s in successful_sessions if s.final_price)
        avg_discount = total_discount / len(successful_sessions)
        avg_negotiated_price = total_final_price / len(successful_sessions)

    # Top products, active farmers, active buyers
    top_products = db.session.query(
        BargainingSession.product_id,
        func.count(BargainingSession.id).label("count")
    ).group_by(BargainingSession.product_id).order_by(db.text("count DESC")).limit(5).all()

    top_products_list = []
    for pid, count in top_products:
        product = Product.query.get(pid)
        if product:
            top_products_list.append({"product": product, "count": count})

    top_farmers = db.session.query(
        BargainingSession.farmer_id,
        func.count(BargainingSession.id).label("count")
    ).group_by(BargainingSession.farmer_id).order_by(db.text("count DESC")).limit(5).all()

    top_farmers_list = []
    for fid, count in top_farmers:
        farmer = User.query.get(fid)
        if farmer:
            top_farmers_list.append({"farmer": farmer, "count": count})

    top_buyers = db.session.query(
        BargainingSession.buyer_id,
        func.count(BargainingSession.id).label("count")
    ).group_by(BargainingSession.buyer_id).order_by(db.text("count DESC")).limit(5).all()

    top_buyers_list = []
    for bid, count in top_buyers:
        buyer = User.query.get(bid)
        if buyer:
            top_buyers_list.append({"buyer": buyer, "count": count})

    return render_template(
        "admin/bargaining_analytics.html",
        total_negotiations=total_negotiations,
        active_negotiations=active_negotiations,
        successful_negotiations=successful_negotiations,
        rejected_negotiations=rejected_negotiations,
        expired_negotiations=expired_negotiations,
        avg_discount=avg_discount,
        avg_negotiated_price=avg_negotiated_price,
        top_products=top_products_list,
        top_farmers=top_farmers_list,
        top_buyers=top_buyers_list
    )


