from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
import json
from werkzeug.security import generate_password_hash, check_password_hash
from models import db
from models.user import User
from models.location import District
from models.farmer_verification import FarmerVerification
from utils.verification_upload import save_verification_documents
import random
import string

from utils.otp import create_otp_session, check_otp_code, clear_otp_session
from utils.voice import set_voice_message


auth_bp = Blueprint("auth", __name__)


def build_captcha():
    chars = string.ascii_uppercase + string.digits
    question = "".join(random.choice(chars) for _ in range(6))

    session["captcha_question"] = question
    session["captcha_answer"] = question
    return question


def validate_captcha(submitted_answer):
    expected_answer = session.get("captcha_answer")
    submitted_value = str(submitted_answer or "").strip()
    return expected_answer is not None and submitted_value == expected_answer


# ---------------------------------------
# Register
# ---------------------------------------
@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    if current_user.is_authenticated:
        return redirect(url_for("home.index"))

    if request.method == "POST":

        captcha_answer = request.form.get("captcha_answer")
        if not validate_captcha(captcha_answer):
            flash("Captcha is invalid.", "danger")
            captcha_question = build_captcha()
            districts = District.query.order_by(District.name).all()
            return render_template("auth/register.html", districts=districts, captcha_question=captcha_question)

        full_name = request.form.get("full_name")
        email = request.form.get("email")
        phone = request.form.get("mobile")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        role = request.form.get("user_type")
        district_id = request.form.get("district")
        taluka_id = request.form.get("taluka")
        village_id = request.form.get("village")
        address = request.form.get("address")

        if role not in {"farmer", "buyer"}:
            flash("Please select a valid account type.", "danger")
            return redirect(url_for("auth.register"))

        document_712_paths = []
        document_8a_paths = []
        if role == "farmer":
            try:
                document_712_paths = save_verification_documents(request.files.getlist("land_document_712"))
                document_8a_paths = save_verification_documents(request.files.getlist("land_document_8a"))
            except ValueError as error:
                flash(str(error), "danger")
                return redirect(url_for("auth.register"))

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("auth.register"))

        existing_email = User.query.filter_by(
            email=email
        ).first()

        if existing_email:
            flash("Email already registered.", "warning")
            return redirect(url_for("auth.register"))

        existing_phone = User.query.filter_by(
            phone=phone
        ).first()

        if existing_phone:
            flash("Phone number already registered.", "warning")
            return redirect(url_for("auth.register"))

        hashed_password = generate_password_hash(password)

        pending_user = {
            "full_name": full_name,
            "email": email,
            "phone": phone,
            "password": hashed_password,
            "role": role,
            "district_id": int(district_id) if district_id and str(district_id).isdigit() else None,
            "taluka_id": int(taluka_id) if taluka_id and str(taluka_id).isdigit() else None,
            "village_id": int(village_id) if village_id and str(village_id).isdigit() else None,
            "address": address
        }
        if role == "farmer":
            pending_user.update({
                "document_712_paths": document_712_paths,
                "document_8a_paths": document_8a_paths,
            })

        otp_code = create_otp_session(
            purpose="registration",
            target=email,
            extra_data=pending_user
        )

        flash(
            f"A 6-digit confirmation code has been sent to {email}. Please check your email / mobile.",
            "info"
        )
        set_voice_message(session, "voice_code_sent", fallback="Confirmation code sent. Please check your email or mobile.")

        return redirect(
            url_for("auth.verify_otp")
        )

    districts = District.query.order_by(District.name).all()
    captcha_question = build_captcha()
    return render_template(
        "auth/register.html",
        districts=districts,
        captcha_question=captcha_question
    )


# ---------------------------------------
# Login
# ---------------------------------------
@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:

        if current_user.role == "farmer":
            if not current_user.district_id or not current_user.address:
                flash("Please enter your address details to complete your profile.", "info")
                return redirect(url_for("farmer.edit_profile"))
            return redirect(
                url_for("farmer.dashboard")
            )

        elif current_user.role == "buyer":
            if not current_user.district_id or not current_user.address:
                flash("Please enter your address details to complete your profile.", "info")
                return redirect(url_for("buyer.edit_profile"))
            return redirect(
                url_for("buyer.dashboard")
            )

        elif current_user.role == "admin":
            return redirect(
                url_for("admin.dashboard")
            )


    if request.method == "POST":

        captcha_answer = request.form.get("captcha_answer")
        if not validate_captcha(captcha_answer):
            flash("Captcha is invalid.", "danger")
            captcha_question = build_captcha()
            return render_template("auth/login.html", captcha_question=captcha_question)

        username = request.form.get("username")
        password = request.form.get("password")

        from routes.admin import get_admin_credentials
        admin_email, admin_password = get_admin_credentials()

        if (username == "admin" or username == admin_email) and password == admin_password:
            logout_user()
            session.pop("admin_id", None)
            session.pop("admin_name", None)

            admin_user = User.query.filter_by(role="admin").first()
            if admin_user:
                login_user(admin_user)
            session["admin_id"] = 1
            session["admin_name"] = "Administrator"
            flash("Admin Login Successful!", "success")
            return redirect(url_for("admin.dashboard"))

        user = User.query.filter(
            (User.email == username) | (User.phone == username)
        ).first()


        if user and check_password_hash(
            user.password,
            password
        ):

            if user.role == "farmer":
                verification = FarmerVerification.query.filter_by(user_id=user.id).first()
                if verification and verification.status != "APPROVED":
                    session["verification_user_id"] = user.id
                    return redirect(url_for("auth.verification_status"))

            otp_code = create_otp_session(
                purpose="login",
                target=user.email,
                extra_data={"user_id": user.id}
            )

            flash(
                f"A 6-digit confirmation code has been sent to {user.email}. Please check your email / mobile.",
                "info"
            )
            set_voice_message(session, "voice_code_sent", fallback="Confirmation code sent. Please check your email or mobile.")

            return redirect(
                url_for("auth.verify_otp")
            )


        flash(
            "Invalid email/mobile or password.",
            "danger"
        )
        set_voice_message(session, "voice_login_failed", fallback="Login failed. Please check your details and try again.")


    captcha_question = build_captcha()
    return render_template(
        "auth/login.html",
        captcha_question=captcha_question
    )


# ---------------------------------------
# Verify OTP / Confirmation Code
# ---------------------------------------
@auth_bp.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():

    purpose = session.get("otp_purpose")
    target = session.get("otp_target")

    if not purpose or not target:
        flash("No active verification session. Please login or register.", "warning")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        submitted_code = request.form.get("otp_code")
        is_valid, error_msg = check_otp_code(submitted_code)

        if not is_valid:
            if "expired" in error_msg.lower():
                set_voice_message(session, "voice_otp_expired", fallback="આ OTP ની સમય મર્યાદા પૂરી થઈ ગઈ છે. કૃપા કરીને નવો OTP મેળવો.")
            else:
                set_voice_message(session, "voice_otp_wrong", fallback="OTP સાચો નથી. કૃપા કરીને ફરીથી સાચો OTP નાખો.")
            flash(error_msg, "danger")
            return render_template(
                "auth/verify_otp.html",
                otp_target=target
            )

        if purpose == "registration":
            data = session.get("otp_data")
            if data:
                user = User(
                    full_name=data.get("full_name"),
                    email=data.get("email"),
                    phone=data.get("phone"),
                    password=data.get("password"),
                    role=data.get("role"),
                    district_id=data.get("district_id"),
                    taluka_id=data.get("taluka_id"),
                    village_id=data.get("village_id"),
                    address=data.get("address"),
                    is_verified=True
                )
                db.session.add(user)
                db.session.flush()
                if data.get("role") == "farmer":
                    verification = FarmerVerification(
                        user_id=user.id,
                        document_type="7/12 and Adhar card",
                        document_path=data.get("document_712_paths")[0],
                        survey_number="",
                        document_712_path=data.get("document_712_paths")[0],
                        document_8a_path=data.get("document_8a_paths")[0],
                        document_712_paths=json.dumps(data.get("document_712_paths")),
                        document_8a_paths=json.dumps(data.get("document_8a_paths")),
                        status="PENDING"
                    )
                    db.session.add(verification)
                    session["verification_user_id"] = user.id
                db.session.commit()
                clear_otp_session()
                if data.get("role") == "farmer":
                    flash("Registration submitted successfully. Your land details are under Admin verification.", "success")
                    return redirect(url_for("auth.verification_status"))
                flash("Registration confirmed and account verified! Please login.", "success")
                set_voice_message(session, "voice_registration_success", fallback="Registration complete. Please log in to continue.")
                return redirect(url_for("auth.login"))

        elif purpose == "login":
            data = session.get("otp_data")
            if data and data.get("user_id"):
                user = User.query.get(data.get("user_id"))
                if user:
                    logout_user()
                    session.pop("admin_id", None)
                    session.pop("admin_name", None)
                    login_user(user)
                    clear_otp_session()
                    flash("Login successful.", "success")
                    set_voice_message(session, "voice_login_success", fallback="Login successful. Welcome to FarmLink.")

                    if user.role == "farmer":
                        if not user.district_id or not user.address:
                            flash("Please enter your address details to complete your profile.", "info")
                            return redirect(url_for("farmer.edit_profile"))
                        return redirect(url_for("farmer.dashboard"))

                    elif user.role == "buyer":
                        if not user.district_id or not user.address:
                            flash("Please enter your address details to complete your profile.", "info")
                            return redirect(url_for("buyer.edit_profile"))
                        return redirect(url_for("buyer.dashboard"))

                    elif user.role == "admin":
                        return redirect(url_for("admin.dashboard"))

                    return redirect(url_for("home.index"))

        clear_otp_session()
        flash("Verification completed.", "info")
        return redirect(url_for("auth.login"))

    return render_template(
        "auth/verify_otp.html",
        otp_target=target
    )


@auth_bp.route("/verification-status")
def verification_status():
    user_id = session.get("verification_user_id")
    if not user_id:
        return redirect(url_for("auth.login"))
    verification = FarmerVerification.query.filter_by(user_id=user_id).first()
    if not verification:
        flash("No farmer verification request was found.", "warning")
        return redirect(url_for("auth.login"))
    return render_template("auth/verification_status.html", verification=verification)


# ---------------------------------------
# Resend OTP
# ---------------------------------------
@auth_bp.route("/resend-otp")
def resend_otp():

    purpose = session.get("otp_purpose")
    target = session.get("otp_target")
    data = session.get("otp_data")

    if not purpose or not target:
        flash("No active verification session.", "warning")
        return redirect(url_for("auth.login"))

    new_code = create_otp_session(
        purpose=purpose,
        target=target,
        extra_data=data
    )

    flash("A new confirmation code has been generated.", "info")
    set_voice_message(session, "voice_code_sent", fallback="A new confirmation code has been generated.")
    return redirect(url_for("auth.verify_otp"))


# ---------------------------------------
# Logout
# ---------------------------------------
@auth_bp.route("/logout")
@login_required
def logout():

    logout_user()
    session.pop("admin_id", None)
    session.pop("admin_name", None)

    flash(
        "You have been logged out.",
        "success"
    )
    set_voice_message(session, "voice_logout", fallback="You have been logged out.")

    return redirect(
        url_for("home.index")
    )


# ---------------------------------------
# Profile
# ---------------------------------------
@auth_bp.route("/profile")
@login_required
def profile():

    if current_user.role == "farmer":
        return redirect(url_for("farmer.profile"))
    elif current_user.role == "buyer":
        return redirect(url_for("buyer.profile"))
    elif current_user.role == "admin":
        return redirect(url_for("admin.dashboard"))

    return redirect(url_for("home.index"))


# ---------------------------------------
# Change Password
# ---------------------------------------
@auth_bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():

    if request.method == "POST":

        current_password = request.form.get(
            "current_password"
        )

        new_password = request.form.get(
            "new_password"
        )

        confirm_password = request.form.get(
            "confirm_password"
        )


        if not check_password_hash(
            current_user.password,
            current_password
        ):
            flash(
                "Current password is incorrect.",
                "danger"
            )

            return redirect(
                url_for("auth.change_password")
            )


        if new_password != confirm_password:
            flash(
                "Passwords do not match.",
                "danger"
            )

            return redirect(
                url_for("auth.change_password")
            )


        current_user.password = generate_password_hash(
            new_password
        )

        db.session.commit()


        flash(
            "Password updated successfully.",
            "success"
        )
        set_voice_message(session, "voice_password_updated", fallback="Password updated successfully.")

        return redirect(
            url_for("auth.profile")
        )


    return render_template(
        "auth/change_password.html"
    )


# ---------------------------------------
# Forgot Password
# ---------------------------------------
@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        user = User.query.filter_by(email=email).first()
        if not user:
            flash("No account found for that email.", "danger")
            return redirect(url_for("auth.forgot_password"))

        code = create_otp_session(purpose="password_reset", target=user.email, extra_data={"user_id": user.id})
        flash(f"A verification code has been sent to {user.email}.", "info")
        session["password_reset_target"] = user.email
        return redirect(url_for("auth.reset_password_otp"))

    return render_template("auth/forgot_password.html")


@auth_bp.route("/reset-password-otp", methods=["GET", "POST"])
def reset_password_otp():
    if request.method == "POST":
        submitted_code = request.form.get("otp_code")
        is_valid, error_msg = check_otp_code(submitted_code)
        if not is_valid:
            flash(error_msg, "danger")
            return render_template("auth/reset_password_otp.html")

        if session.get("otp_purpose") != "password_reset":
            flash("The password reset session is invalid.", "danger")
            return redirect(url_for("auth.login"))

        clear_otp_session()
        session["password_reset_ready"] = True
        return redirect(url_for("auth.set_new_password"))

    return render_template("auth/reset_password_otp.html")


@auth_bp.route("/set-new-password", methods=["GET", "POST"])
def set_new_password():
    if not session.get("password_reset_ready"):
        flash("Please complete the reset code step first.", "warning")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")
        if len(new_password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return render_template("auth/set_new_password.html")
        if new_password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("auth/set_new_password.html")

        user_id = session.get("otp_data", {}).get("user_id") if session.get("otp_data") else None
        if not user_id:
            flash("Reset session is invalid.", "danger")
            return redirect(url_for("auth.forgot_password"))

        user = User.query.get(user_id)
        if user:
            user.password = generate_password_hash(new_password)
            db.session.commit()

        session.pop("password_reset_ready", None)
        session.pop("password_reset_target", None)
        flash("Your password has been reset. Please log in again.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/set_new_password.html")