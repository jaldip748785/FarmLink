import unittest
from datetime import date, timedelta
from decimal import Decimal

from config import Config
Config.SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"

from app import create_app
from models import db
from models.user import User
from models.product import Product
from models.category import Category
from models.order import Order
from models.review import Review
from models.bargaining import BargainingSession, BargainingOffer
from models.apmc_rate import APMCRate
from models.location import District, Taluka, Village
from werkzeug.security import generate_password_hash
from app import create_app, seed_default_location_data, seed_default_category_data


class FarmLinkCoreWorkflowTests(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.app.config.update(TESTING=True, SQLALCHEMY_DATABASE_URI="sqlite:///:memory:", WTF_CSRF_ENABLED=False)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.drop_all()
        db.create_all()
        self.seed_data()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def seed_data(self):
        category = Category(name="Vegetables", description="Fresh vegetables")
        db.session.add(category)
        db.session.commit()

        farmer = User(full_name="Farmer One", email="farmer@example.com", phone="1111111111", password=generate_password_hash("password"), role="farmer")
        buyer = User(full_name="Buyer One", email="buyer@example.com", phone="2222222222", password=generate_password_hash("password"), role="buyer")
        db.session.add_all([farmer, buyer])
        db.session.commit()

        self.category = category
        self.farmer = farmer
        self.buyer = buyer

        product = Product(farmer_id=farmer.id, category_id=category.id, title="Fresh Tomatoes", price=Decimal("30.00"), quantity=100, unit="Kg", status="Available", allow_bargaining=True, min_price=Decimal("24.00"))
        db.session.add(product)
        db.session.commit()
        self.product = product

    def login_user(self, email):
        user = User.query.filter_by(email=email).first()
        with self.client.session_transaction() as sess:
            sess["_user_id"] = str(user.id)
            sess["_fresh"] = True

    def login_admin(self):
        admin_user = User.query.filter_by(role="admin").first()
        if not admin_user:
            admin_user = User(
                full_name="Administrator",
                email="farmerlink87@gmail.com",
                phone="0000000000",
                password=generate_password_hash("farmlink@123"),
                role="admin"
            )
            db.session.add(admin_user)
            db.session.commit()

        with self.client.session_transaction() as sess:
            sess["_user_id"] = str(admin_user.id)
            sess["_fresh"] = True
            sess["admin_id"] = 1
            sess["admin_name"] = admin_user.full_name

    def test_home_page_shows_latest_products_from_database(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Fresh Tomatoes", response.data)

    def test_buyer_can_view_admin_published_apmc_rates(self):
        rate = APMCRate(
            commodity_name="Tomato",
            market_name="Rajkot APMC",
            state="Gujarat",
            modal_price=Decimal("30.00"),
            minimum_price=Decimal("25.00"),
            maximum_price=Decimal("35.00"),
            unit="kg"
        )
        db.session.add(rate)
        db.session.commit()
        self.login_user("buyer@example.com")

        response = self.client.get("/buyer/apmc/rates")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Rajkot APMC", response.data)
        self.assertIn(b"Today", response.data)

    def test_farmer_can_view_the_same_published_apmc_rates(self):
        rate = APMCRate(
            commodity_name="Wheat",
            market_name="Rajkot APMC",
            modal_price=Decimal("40.00"),
            minimum_price=Decimal("35.00"),
            maximum_price=Decimal("45.00"),
            unit="kg"
        )
        db.session.add(rate)
        db.session.commit()
        self.login_user("farmer@example.com")

        response = self.client.get("/farmer/apmc/rates", follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Wheat", response.data)
        self.assertIn(b"/buyer/apmc/rates", response.data)

    def test_buyer_can_filter_apmc_rates_by_yesterday_and_specific_date(self):
        yesterday_rate = APMCRate(
            commodity_name="Onion",
            market_name="Rajkot APMC",
            modal_price=Decimal("20.00"),
            minimum_price=Decimal("15.00"),
            maximum_price=Decimal("25.00"),
            unit="kg",
            rate_date=date.today() - timedelta(days=1)
        )
        db.session.add(yesterday_rate)
        db.session.commit()
        self.login_user("buyer@example.com")
        with self.client.session_transaction() as session:
            session["lang"] = "gu"

        yesterday_response = self.client.get("/buyer/apmc/rates?period=yesterday")
        specific_response = self.client.get(
            "/buyer/apmc/rates?period=date&date=" + (date.today() - timedelta(days=1)).isoformat()
        )

        self.assertIn(b"Onion", yesterday_response.data)
        self.assertIn(b"Onion", specific_response.data)
        self.assertIn("ગઈકાલે".encode("utf-8"), yesterday_response.data)

    def test_home_apmc_link_does_not_point_to_admin_panel(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"/buyer/apmc/rates", response.data)
        self.assertNotIn(b"/admin/apmc/rates", response.data)

    def test_selected_language_is_used_on_buyer_dashboard(self):
        self.login_user("buyer@example.com")

        response = self.client.get(
            "/switch-language/gu",
            headers={"Referer": "/buyer/dashboard"},
            follow_redirects=True
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("સ્વાગત છે, ખરીદનાર!".encode("utf-8"), response.data)
        self.assertIn(b"Gujarati", response.data)

        with self.client.session_transaction() as session:
            self.assertEqual(session["lang"], "gu")

    def test_add_product_rejects_empty_numeric_fields_without_server_error(self):
        self.farmer.address = "Farm Road"
        self.farmer.district_id = 1
        db.session.commit()
        self.login_user("farmer@example.com")
        product_count_before = Product.query.filter_by(farmer_id=self.farmer.id).count()

        with self.client.session_transaction() as session:
            session["lang"] = "gu"

        response = self.client.post("/farmer/product/add", data={})

        self.assertEqual(response.status_code, 200)
        self.assertIn("કૃપા કરીને યોગ્ય કિંમત".encode("utf-8"), response.data)
        self.assertEqual(Product.query.filter_by(farmer_id=self.farmer.id).count(), product_count_before)

    def test_zero_quantity_products_are_not_shown_as_available(self):
        self.product.quantity = 0
        self.product.status = "Available"
        db.session.commit()

        self.assertEqual(self.product.status, "Sold")
        self.assertEqual(Product.query.get(self.product.id).status, "Sold")

        response = self.client.get("/")
        self.assertNotIn(b"Fresh Tomatoes", response.data)

    def test_registration_page_shows_location_dropdowns_when_seed_data_exists(self):
        seed_default_location_data(self.app)

        response = self.client.get("/auth/register")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Ahmedabad", response.data)

    def test_default_categories_are_seeded_for_add_product_dropdown(self):
        db.drop_all()
        db.create_all()

        seed_default_category_data(self.app)

        self.assertGreater(Category.query.count(), 0)

    def test_buyer_can_submit_review_after_purchase(self):
        order = Order(
            product_id=self.product.id,
            buyer_id=self.buyer.id,
            farmer_id=self.farmer.id,
            quantity=2,
            original_price=self.product.price,
            total_amount=Decimal("60.00"),
            status="Paid"
        )
        db.session.add(order)
        db.session.commit()

        self.login_user("buyer@example.com")

        response = self.client.post(
            "/api/reviews",
            json={"product_id": self.product.id, "rating": 5, "comment": "Excellent quality"},
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Review.query.count(), 1)
        review = Review.query.first()
        self.assertEqual(review.comment, "Excellent quality")
        self.assertEqual(review.author_id, self.buyer.id)

        page_response = self.client.get(f"/buyer/product/{self.product.id}")
        self.assertIn(b"Excellent quality", page_response.data)

    def test_admin_login_works_with_requested_credentials(self):
        response = self.client.post(
            "/admin/login",
            data={
                "email": "farmerlink87@gmail.com",
                "password": "farmlink@123"
            },
            follow_redirects=False
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/admin/dashboard")

        with self.client.session_transaction() as session:
            self.assertEqual(session["admin_id"], 1)

    def test_admin_dashboard_requires_an_authenticated_admin_user(self):
        with self.client.session_transaction() as session:
            session["admin_id"] = 1

        response = self.client.get("/admin/dashboard", follow_redirects=False)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/admin/login")

    def test_admin_account_cannot_be_deleted(self):
        admin_user = User(
            full_name="Administrator",
            email="farmerlink87@gmail.com",
            phone="0000000000",
            password=generate_password_hash("farmlink@123"),
            role="admin"
        )
        db.session.add(admin_user)
        db.session.commit()

        self.assertIsNotNone(admin_user)
        self.login_admin()

        response = self.client.get(f"/admin/user/delete/{admin_user.id}", follow_redirects=False)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/admin/users")
        self.assertEqual(User.query.filter_by(id=admin_user.id).count(), 1)

    def test_farmer_with_products_can_be_deleted_without_error(self):
        farmer = User(
            full_name="Farmer Delete",
            email="farmer-delete@example.com",
            phone="3333333333",
            password=generate_password_hash("password"),
            role="farmer"
        )
        db.session.add(farmer)
        db.session.commit()

        product = Product(
            farmer_id=farmer.id,
            category_id=self.category.id,
            title="Delete Me",
            price=Decimal("20.00"),
            quantity=10,
            unit="Kg",
            status="Available",
            allow_bargaining=True,
            min_price=Decimal("15.00")
        )
        db.session.add(product)
        db.session.commit()

        self.login_admin()

        response = self.client.get(f"/admin/user/delete/{farmer.id}", follow_redirects=False)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/admin/users")
        self.assertEqual(User.query.filter_by(id=farmer.id).count(), 0)
        self.assertEqual(Product.query.filter_by(id=product.id).count(), 0)

    def test_admin_can_delete_category_that_has_products_without_error(self):
        self.login_admin()

        response = self.client.get(f"/admin/category/delete/{self.category.id}", follow_redirects=False)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/admin/categories")
        self.assertEqual(Category.query.filter_by(id=self.category.id).count(), 0)
        self.assertEqual(Product.query.filter_by(id=self.product.id).count(), 0)

    def test_farmer_can_delete_product_with_bargaining_records_without_error(self):
        self.login_user("farmer@example.com")

        bargaining_session = BargainingSession(
            product_id=self.product.id,
            buyer_id=self.buyer.id,
            farmer_id=self.farmer.id,
            quantity=1,
            listed_price=self.product.price,
            status="PENDING"
        )
        db.session.add(bargaining_session)
        db.session.commit()

        bargaining_offer = BargainingOffer(
            session_id=bargaining_session.id,
            sender_id=self.buyer.id,
            receiver_id=self.farmer.id,
            offer_price=Decimal("25.00"),
            quantity=1,
            total_amount=Decimal("25.00"),
            message="Offer",
            offer_type="INITIAL",
            status="PENDING"
        )
        db.session.add(bargaining_offer)
        db.session.commit()

        response = self.client.get(f"/farmer/product/delete/{self.product.id}", follow_redirects=False)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/farmer/products")
        self.assertEqual(Product.query.filter_by(id=self.product.id).count(), 0)
        self.assertEqual(BargainingSession.query.filter_by(id=bargaining_session.id).count(), 0)
        self.assertEqual(BargainingOffer.query.filter_by(id=bargaining_offer.id).count(), 0)

    def test_admin_can_add_apmc_rates(self):
        self.login_admin()

        response = self.client.post(
            "/admin/apmc/rate/add",
            data={
                "commodity_name": "Tomato",
                "category_id": str(self.category.id),
                "market_name": "Pune",
                "state": "Maharashtra",
                "district_id": "",
                "modal_price": "35",
                "minimum_price": "30",
                "maximum_price": "40",
                "unit": "kg",
                "rate_date": "2026-07-31",
                "source": "AGMARKNET"
            },
            follow_redirects=False
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/admin/apmc/rates")
        self.assertEqual(APMCRate.query.count(), 1)
        self.assertEqual(APMCRate.query.first().category_id, self.category.id)

    def test_admin_can_add_village_for_any_district_and_taluka(self):
        district = District(name="Surat")
        db.session.add(district)
        db.session.commit()
        taluka = Taluka(district_id=district.id, name="Bardoli")
        db.session.add(taluka)
        db.session.commit()
        self.login_admin()

        response = self.client.post(
            "/admin/location/add",
            data={
                "location_type": "village",
                "district_id": str(district.id),
                "taluka_id": str(taluka.id),
                "name": "Kikvada"
            },
            follow_redirects=False
        )

        self.assertEqual(response.status_code, 302)
        village = Village.query.filter_by(name="Kikvada").first()
        self.assertIsNotNone(village)
        self.assertEqual(village.district_id, district.id)
        self.assertEqual(village.taluka_id, taluka.id)

        page_response = self.client.get("/admin/locations")
        self.assertIn(b"Kikvada", page_response.data)

    def test_category_table_opens_apmc_form_for_that_category(self):
        self.login_admin()

        response = self.client.get(f"/admin/apmc/rate/add?category_id={self.category.id}")

        self.assertEqual(response.status_code, 200)
        self.assertIn(f'value="{self.category.id}" selected'.encode("utf-8"), response.data)

        categories_response = self.client.get("/admin/categories")
        self.assertIn(f"/admin/apmc/rate/add?category_id={self.category.id}".encode("utf-8"), categories_response.data)

    def test_login_rejects_invalid_captcha(self):
        self.client.get("/auth/login")

        response = self.client.post(
            "/auth/login",
            data={
                "username": "farmer@example.com",
                "password": "password",
                "captcha_answer": "999"
            },
            follow_redirects=False
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Captcha is invalid", response.data)
        self.assertNotIn(b"Login successful.", response.data)

    def test_register_rejects_invalid_captcha(self):
        self.client.get("/auth/register")

        response = self.client.post(
            "/auth/register",
            data={
                "full_name": "New User",
                "email": "newuser@example.com",
                "mobile": "6666666666",
                "password": "password123",
                "confirm_password": "password123",
                "user_type": "buyer",
                "district": "",
                "taluka": "",
                "village": "",
                "address": "Test address",
                "captcha_answer": "999"
            },
            follow_redirects=False
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Captcha is invalid", response.data)
        self.assertEqual(User.query.filter_by(email="newuser@example.com").count(), 0)

    def test_admin_edit_rejects_duplicate_phone(self):
        user = User(
            full_name="Existing User",
            email="existing@example.com",
            phone="4444444444",
            password=generate_password_hash("password"),
            role="buyer"
        )
        db.session.add(user)
        db.session.commit()

        target = User(
            full_name="Target User",
            email="target@example.com",
            phone="5555555555",
            password=generate_password_hash("password"),
            role="buyer"
        )
        db.session.add(target)
        db.session.commit()

        self.login_admin()

        response = self.client.post(
            f"/admin/user/edit/{target.id}",
            data={
                "full_name": target.full_name,
                "email": target.email,
                "phone": "4444444444",
                "role": target.role
            },
            follow_redirects=False
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/admin/users")
        self.assertEqual(User.query.get(target.id).phone, "5555555555")


if __name__ == "__main__":
    unittest.main()
