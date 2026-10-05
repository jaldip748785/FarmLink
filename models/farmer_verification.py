import json
from datetime import datetime

from models import db


class FarmerVerification(db.Model):
    __tablename__ = "farmer_verifications"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )

    document_type = db.Column(
        db.String(50),
        nullable=False
    )

    document_path = db.Column(
        db.String(255),
        nullable=False
    )

    survey_number = db.Column(
        db.String(100),
        nullable=False
    )

    document_712_path = db.Column(
        db.String(255),
        nullable=True
    )

    document_8a_path = db.Column(
        db.String(255),
        nullable=True
    )

    document_712_paths = db.Column(
        db.Text,
        nullable=True
    )

    document_8a_paths = db.Column(
        db.Text,
        nullable=True
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="PENDING"
    )

    submitted_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    reviewed_at = db.Column(
        db.DateTime
    )

    reviewed_by = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.id",
            ondelete="SET NULL"
        )
    )

    rejection_reason = db.Column(
        db.Text
    )

    farmer = db.relationship(
        "User",
        foreign_keys=[user_id],
        backref=db.backref(
            "farmer_verification",
            uselist=False,
            cascade="all, delete-orphan"
        )
    )

    reviewer = db.relationship(
        "User",
        foreign_keys=[reviewed_by]
    )

    @property
    def uploaded_712_documents(self):
        return self._parse_document_paths(
            self.document_712_paths,
            self.document_712_path
        )

    @property
    def uploaded_8a_documents(self):
        return self._parse_document_paths(
            self.document_8a_paths,
            self.document_8a_path
        )

    @staticmethod
    def _parse_document_paths(
        paths_json,
        fallback_path
    ):
        try:
            paths = (
                json.loads(paths_json)
                if paths_json
                else []
            )

        except (
            TypeError,
            json.JSONDecodeError
        ):
            paths = []

        return paths or (
            [fallback_path]
            if fallback_path
            else []
        )