from models import db

class District(db.Model):

    __tablename__ = "districts"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )


class Taluka(db.Model):

    __tablename__ = "talukas"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    district_id = db.Column(
        db.Integer,
        nullable=False
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )


class Village(db.Model):

    __tablename__ = "villages"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    district_id = db.Column(
        db.Integer,
        nullable=False
    )

    taluka_id = db.Column(
        db.Integer,
        nullable=False
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )