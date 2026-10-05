from sqlalchemy import event

from models import db


class Product(db.Model):

    __tablename__ = "products"


    id = db.Column(
        db.Integer,
        primary_key=True
    )


    farmer_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )


    category_id = db.Column(
        db.Integer,
        db.ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False
    )


    title = db.Column(
        db.String(150),
        nullable=False
    )


    description = db.Column(
        db.Text
    )


    price = db.Column(
        db.Numeric(10, 2),
        nullable=False
    )


    quantity = db.Column(
        db.Integer,
        nullable=False
    )


    unit = db.Column(
        db.String(20)
    )


    image = db.Column(
        db.String(255)
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


    status = db.Column(
        db.Enum(
            "Available",
            "Sold"
        ),
        default="Available"
    )


    allow_bargaining = db.Column(
        db.Boolean,
        default=False
    )


    min_price = db.Column(
        db.Numeric(10, 2),
        default=0.00
    )


    created_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )



    # Relationships
    category = db.relationship(
        'Category',
        primaryjoin='Product.category_id == Category.id',
        backref=db.backref('products_list', lazy=True, cascade='all, delete-orphan')
    )
    farmer = db.relationship('User', primaryjoin='Product.farmer_id == User.id', backref=db.backref('products_list', lazy=True))
    district = db.relationship('District', primaryjoin='Product.district_id == District.id')
    taluka = db.relationship('Taluka', primaryjoin='Product.taluka_id == Taluka.id')
    village = db.relationship('Village', primaryjoin='Product.village_id == Village.id')



    def sync_status_from_quantity(self):
        try:
            quantity_value = int(self.quantity or 0)
        except (TypeError, ValueError):
            quantity_value = 0

        self.status = "Sold" if quantity_value <= 0 else "Available"
        return self


    @staticmethod
    def sync_all_statuses():
        for product in Product.query.all():
            product.sync_status_from_quantity()

        db.session.commit()


    # -------------------------------
    # Add Product
    # -------------------------------
    @staticmethod
    def add(data):

        product = Product(
            farmer_id=data["farmer_id"],
            category_id=data["category_id"],
            title=data["title"],
            description=data.get("description"),
            price=data["price"],
            quantity=data["quantity"],
            unit=data.get("unit"),
            image=data.get("image"),
            district_id=data.get("district_id"),
            taluka_id=data.get("taluka_id"),
            village_id=data.get("village_id"),
            status=data.get(
                "status",
                "Available"
            ),
            allow_bargaining=data.get("allow_bargaining", False),
            min_price=data.get("min_price", 0.00)
        )


        product.sync_status_from_quantity()
        db.session.add(product)
        db.session.commit()


        return product


    # -------------------------------
    # Get All Products
    # -------------------------------
    @staticmethod
    def get_all():

        return Product.query.order_by(
            Product.id.desc()
        ).all()


    # -------------------------------
    # Get Product By ID
    # -------------------------------
    @staticmethod
    def get_by_id(product_id):

        return Product.query.get(
            product_id
        )


    # -------------------------------
    # Delete Product
    # -------------------------------
    @staticmethod
    def delete(product_id):

        product = Product.query.get(
            product_id
        )

        if product:

            db.session.delete(product)
            db.session.commit()

            return True

        return False


@event.listens_for(db.session, "before_commit")
def sync_product_statuses_before_commit(session):
    for obj in list(session.new) + list(session.dirty):
        if isinstance(obj, Product):
            obj.sync_status_from_quantity()