from functools import wraps

from flask import flash
from flask import redirect
from flask import url_for

from flask_login import current_user


def admin_required(view):

    @wraps(view)
    def wrapped(*args, **kwargs):

        if not current_user.is_authenticated:
            flash("Please login first.", "warning")
            return redirect(url_for("auth.login"))

        if current_user.role != "admin":
            flash("Access denied.", "danger")
            return redirect(url_for("home.index"))

        return view(*args, **kwargs)

    return wrapped


def farmer_required(view):

    @wraps(view)
    def wrapped(*args, **kwargs):

        if not current_user.is_authenticated:
            flash("Please login first.", "warning")
            return redirect(url_for("auth.login"))

        if current_user.role != "farmer":
            flash("Only farmers can access this page.", "danger")
            return redirect(url_for("home.index"))

        return view(*args, **kwargs)

    return wrapped


def buyer_required(view):

    @wraps(view)
    def wrapped(*args, **kwargs):

        if not current_user.is_authenticated:
            flash("Please login first.", "warning")
            return redirect(url_for("auth.login"))

        if current_user.role != "buyer":
            flash("Only buyers can access this page.", "danger")
            return redirect(url_for("home.index"))

        return view(*args, **kwargs)

    return wrapped