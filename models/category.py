from models import db


class Category(db.Model):

    __tablename__ = "categories"


    id = db.Column(
        db.Integer,
        primary_key=True
    )


    name = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )


    description = db.Column(
        db.Text
    )


    created_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )


    @staticmethod
    def get_all():

        return Category.query.order_by(
            Category.name
        ).all()