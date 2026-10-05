from models import db
from flask_login import UserMixin


class User(UserMixin, db.Model):

    __tablename__ = "users"


    id = db.Column(
        db.Integer,
        primary_key=True
    )


    full_name = db.Column(
        db.String(150),
        nullable=False
    )


    email = db.Column(
        db.String(150),
        unique=True,
        nullable=False
    )


    phone = db.Column(
        db.String(15),
        unique=True,
        nullable=False
    )


    password = db.Column(
        db.String(255),
        nullable=False
    )


    role = db.Column(
        db.Enum(
            "admin",
            "farmer",
            "buyer"
        ),
        default="buyer"
    )


    district_id = db.Column(
        db.Integer,
        db.ForeignKey("districts.id")
    )


    taluka_id = db.Column(
        db.Integer,
        db.ForeignKey("talukas.id")
    )


    village_id = db.Column(
        db.Integer,
        db.ForeignKey("villages.id")
    )


    address = db.Column(
        db.Text
    )


    profile_image = db.Column(
        db.String(255)
    )


    is_verified = db.Column(
        db.Boolean,
        default=False
    )


    created_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )
    # Relationships
    district = db.relationship('District', primaryjoin='User.district_id == District.id')
    taluka = db.relationship('Taluka', primaryjoin='User.taluka_id == Taluka.id')
    village = db.relationship('Village', primaryjoin='User.village_id == Village.id')


    @staticmethod
    def create(data):

        user = User(
            full_name=data["full_name"],
            email=data["email"],
            phone=data["phone"],
            password=data["password"],
            role=data.get(
                "role",
                "buyer"
            ),
            district_id=data.get(
                "district_id"
            ),
            taluka_id=data.get(
                "taluka_id"
            ),
            village_id=data.get(
                "village_id"
            )
        )


        db.session.add(user)
        db.session.commit()


        return user


    @staticmethod
    def get_by_email(email):

        return User.query.filter_by(
            email=email
        ).first()


    @staticmethod
    def get_all():

        return User.query.all()