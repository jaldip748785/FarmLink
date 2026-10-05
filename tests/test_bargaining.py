import unittest
from datetime import datetime, timedelta
from decimal import Decimal

# Override database URI configuration before importing app
from config import Config
Config.SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"

from app import create_app
from models import db
from models.user import User
from models.product import Product
from models.bargaining import BargainingSession, BargainingOffer
from models.order import Order
from models.category import Category
from werkzeug.security import generate_password_hash
from flask import session

class FarmLinkBargainingTests(unittest.TestCase):

    def setUp(self):
        # Set up a test application with in-memory SQLite DB
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.app.config["WTF_CSRF_ENABLED"] = False
        
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

        db.create_all()
        self.seed_database()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def seed_database(self):
        # Create or fetch Category
        self.category = Category.query.filter_by(name="Vegetables").first()
        if not self.category:
            self.category = Category(name="Vegetables", description="Fresh green vegetables")
            db.session.add(self.category)
            db.session.commit()

        # Create Users
        self.farmer = User(
            full_name="Rajesh Patel",
            email="farmer@farmlink.com",
            phone="9876543210",
            password=generate_password_hash("password123"),
            role="farmer"
        )
        self.buyer = User(
            full_name="Dinesh Kumar",
            email="buyer@farmlink.com",
            phone="8765432109",
            password=generate_password_hash("password123"),
            role="buyer"
        )
        db.session.add(self.farmer)
        db.session.add(self.buyer)
        db.session.commit()

        # Create Product
        self.product = Product(
            farmer_id=self.farmer.id,
            category_id=self.category.id,
            title="Tomato",
            price=Decimal("30.00"),
            quantity=500,
            unit="Kg",
            status="Available",
            allow_bargaining=True,
            min_price=Decimal("24.00")
        )
        db.session.add(self.product)
        db.session.commit()

    def login_user(self, email):
        # Bypass OTP for test speed by directly inserting session values
        # Since auth.py requires verify-otp, we can log in with a helper login call or use direct session manipulation.
        # But wait, auth.py has standard login, but it sets OTP session and redirects to verify-otp.
        # Let's mock log-in by logging in using the client session!
        with self.client.session_transaction() as sess:
            user = User.query.filter_by(email=email).first()
            sess["_user_id"] = str(user.id)
            sess["role"] = user.role
            sess["_fresh"] = True

    # ---------------------------------------------------------
    # Buyer Test Cases
    # ---------------------------------------------------------
    def test_buyer_create_valid_offer(self):
        self.login_user("buyer@farmlink.com")
        response = self.client.post(
            f"/buyer/bargain/start/{self.product.id}",
            data={"quantity": 50, "offer_price": "25.00", "message": "Can you offer ₹25?"},
            follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)

        # Check BargainingSession created
        session = BargainingSession.query.first()
        self.assertIsNotNone(session)
        self.assertEqual(session.status, "PENDING")
        self.assertEqual(session.quantity, 50)
        self.assertEqual(session.listed_price, Decimal("30.00"))

        # Check Initial Offer created
        offer = BargainingOffer.query.first()
        self.assertIsNotNone(offer)
        self.assertEqual(offer.offer_price, Decimal("25.00"))
        self.assertEqual(offer.offer_type, "INITIAL")

    def test_buyer_invalid_offer_too_low(self):
        self.login_user("buyer@farmlink.com")
        # min_price is ₹24. Buyer offers ₹23. Should reject.
        response = self.client.post(
            f"/buyer/bargain/start/{self.product.id}",
            data={"quantity": 50, "offer_price": "23.00", "message": "Offer too low"},
            follow_redirects=True
        )
        # Check no session created
        self.assertIsNone(BargainingSession.query.first())

    def test_buyer_invalid_offer_exceeds_stock(self):
        self.login_user("buyer@farmlink.com")
        # stock is 500. Buyer asks for 600.
        response = self.client.post(
            f"/buyer/bargain/start/{self.product.id}",
            data={"quantity": 600, "offer_price": "25.00", "message": "More than stock"},
            follow_redirects=True
        )
        self.assertIsNone(BargainingSession.query.first())

    # ---------------------------------------------------------
    # Farmer & Counter Offer Test Cases
    # ---------------------------------------------------------
    def test_farmer_counter_offer(self):
        # Create an initial session
        bargain_session = BargainingSession(
            product_id=self.product.id,
            buyer_id=self.buyer.id,
            farmer_id=self.farmer.id,
            quantity=50,
            listed_price=self.product.price,
            status="PENDING",
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        db.session.add(bargain_session)
        db.session.commit()

        initial_offer = BargainingOffer(
            session_id=bargain_session.id,
            sender_id=self.buyer.id,
            receiver_id=self.farmer.id,
            offer_price=Decimal("25.00"),
            quantity=50,
            total_amount=Decimal("1250.00"),
            offer_type="INITIAL",
            status="PENDING"
        )
        db.session.add(initial_offer)
        db.session.commit()

        # Login as farmer
        self.login_user("farmer@farmlink.com")

        # Submit counter offer of ₹28
        response = self.client.post(
            f"/bargain/session/{bargain_session.id}/offer",
            data={"quantity": 50, "offer_price": "28.00", "message": "Can you do ₹28?"},
            follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)

        # Check DB states
        self.assertEqual(bargain_session.status, "NEGOTIATING")
        
        # Verify previous offer marked countered
        self.assertEqual(initial_offer.status, "COUNTERED")

        # Verify new offer log created
        counter = BargainingOffer.query.filter_by(offer_type="COUNTER").first()
        self.assertIsNotNone(counter)
        self.assertEqual(counter.offer_price, Decimal("28.00"))
        self.assertEqual(counter.sender_id, self.farmer.id)

    # ---------------------------------------------------------
    # Accept and Order Integration Test Cases
    # ---------------------------------------------------------
    def test_accept_deal_and_checkout(self):
        # Create negotiation session
        bargain_session = BargainingSession(
            product_id=self.product.id,
            buyer_id=self.buyer.id,
            farmer_id=self.farmer.id,
            quantity=50,
            listed_price=self.product.price,
            status="NEGOTIATING",
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        db.session.add(bargain_session)
        db.session.commit()

        # Farmer sent counter offer of ₹27
        farmer_counter = BargainingOffer(
            session_id=bargain_session.id,
            sender_id=self.farmer.id,
            receiver_id=self.buyer.id,
            offer_price=Decimal("27.00"),
            quantity=50,
            total_amount=Decimal("1350.00"),
            offer_type="COUNTER",
            status="PENDING"
        )
        db.session.add(farmer_counter)
        db.session.commit()

        # Login as Buyer
        self.login_user("buyer@farmlink.com")

        # Accept Farmer's Counter Offer
        response = self.client.post(
            f"/bargain/session/{bargain_session.id}/accept",
            follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)

        # Verify DB states
        self.assertEqual(bargain_session.status, "ACCEPTED")
        self.assertEqual(bargain_session.final_price, Decimal("27.00"))
        self.assertEqual(farmer_counter.status, "ACCEPTED")

        # Verify order draft created
        order = Order.query.first()
        self.assertIsNotNone(order)
        self.assertEqual(order.status, "Pending")
        self.assertEqual(order.negotiated_price, Decimal("27.00"))
        self.assertEqual(order.total_amount, Decimal("1350.00"))

        # Pay and Checkout Order
        response = self.client.post(
            f"/order/checkout/{order.id}",
            data={"payment_method": "online_payment"},
            follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)

        # Verify product stock reduction (500 - 50 = 450)
        self.assertEqual(self.product.quantity, 450)

        # Verify order status
        self.assertEqual(order.status, "Confirmed")

        # Verify bargaining session is completed
        self.assertEqual(bargain_session.status, "COMPLETED")

    # ---------------------------------------------------------
    # Expiration and Expiry Protection Test Cases
    # ---------------------------------------------------------
    def test_bargain_session_expired(self):
        # Create an expired session (time in past)
        bargain_session = BargainingSession(
            product_id=self.product.id,
            buyer_id=self.buyer.id,
            farmer_id=self.farmer.id,
            quantity=50,
            listed_price=self.product.price,
            status="PENDING",
            expires_at=datetime.utcnow() - timedelta(hours=1) # Expired 1 hour ago
        )
        db.session.add(bargain_session)
        db.session.commit()

        initial_offer = BargainingOffer(
            session_id=bargain_session.id,
            sender_id=self.buyer.id,
            receiver_id=self.farmer.id,
            offer_price=Decimal("25.00"),
            quantity=50,
            total_amount=Decimal("1250.00"),
            offer_type="INITIAL",
            status="PENDING"
        )
        db.session.add(initial_offer)
        db.session.commit()

        # Login as farmer and view session details, triggering dynamic check_expiration()
        self.login_user("farmer@farmlink.com")
        response = self.client.get(
            f"/bargain/session/{bargain_session.id}",
            follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)

        # Check DB states updated to EXPIRED
        updated_session = db.session.get(BargainingSession, bargain_session.id)
        updated_offer = db.session.get(BargainingOffer, initial_offer.id)
        self.assertEqual(updated_session.status, "EXPIRED")
        self.assertEqual(updated_offer.status, "EXPIRED")

        # Try to post counter offer (should reject)
        response_counter = self.client.post(
            f"/bargain/session/{bargain_session.id}/offer",
            data={"quantity": 50, "offer_price": "28.00"},
            follow_redirects=True
        )
        self.assertEqual(BargainingOffer.query.filter_by(offer_type="COUNTER").count(), 0)

    # ---------------------------------------------------------
    # Access Protection Test Case
    # ---------------------------------------------------------
    def test_unauthorized_access_protection(self):
        # Create a session between Rajesh Patel and Dinesh Kumar
        bargain_session = BargainingSession(
            product_id=self.product.id,
            buyer_id=self.buyer.id,
            farmer_id=self.farmer.id,
            quantity=50,
            listed_price=self.product.price,
            status="PENDING",
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        db.session.add(bargain_session)
        
        # Create a third user (hacker)
        hacker = User(
            full_name="Hacker",
            email="hacker@farmlink.com",
            phone="0000000001",
            password=generate_password_hash("password123"),
            role="buyer"
        )
        db.session.add(hacker)
        db.session.commit()

        # Login as hacker
        self.login_user("hacker@farmlink.com")

        # Access negotiation session details (should redirect and show Access Denied flash)
        response = self.client.get(f"/bargain/session/{bargain_session.id}")
        self.assertEqual(response.status_code, 302) # Redirect to home
        
if __name__ == "__main__":
    unittest.main()
