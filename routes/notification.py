from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db
from models.notification import Notification

notification_bp = Blueprint("notification", __name__)

@notification_bp.route("/notifications")
@login_required
def list_notifications():
    # Fetch notifications for current user
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
    
    # Mark them as read upon viewing
    unread_notifications = [n for n in notifications if not n.is_read]
    if unread_notifications:
        for n in unread_notifications:
            n.is_read = True
        db.session.commit()
        
    return render_template("notifications.html", notifications=notifications)

@notification_bp.route("/notifications/mark-read", methods=["POST"])
@login_required
def mark_all_read():
    unread = Notification.query.filter_by(user_id=current_user.id, is_read=False).all()
    for n in unread:
        n.is_read = True
    db.session.commit()
    flash("All notifications marked as read.", "success")
    return redirect(url_for("notification.list_notifications"))
