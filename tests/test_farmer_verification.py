import io
import unittest

from config import Config
Config.SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"

from app import create_app
from models import db
from models.user import User
from models.farmer_verification import FarmerVerification
from werkzeug.security import generate_password_hash


class FarmerVerificationTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config.update(TESTING=True, SQLALCHEMY_DATABASE_URI="sqlite:///:memory:", WTF_CSRF_ENABLED=False)
        self.client = self.app.test_client()
        self.context = self.app.app_context()
        self.context.push()
        db.drop_all()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def captcha_answer(self, path):
        self.client.get(path)
        with self.client.session_transaction() as session:
            return session["captcha_answer"]

    def login_admin(self):
        response = self.client.post("/admin/login", data={"email": "farmerlink87@gmail.com", "password": "farmlink@123"})
        self.assertEqual(response.status_code, 302)
        return User.query.filter_by(role="admin").first()

    def register_farmer(self):
        answer = self.captcha_answer("/auth/register")
        response = self.client.post("/auth/register", data={
            "user_type": "farmer",
            "full_name": "Ramesh Patel",
            "mobile": "9999999999",
            "email": "ramesh@example.com",
            "password": "password",
            "confirm_password": "password",
            "captcha_answer": answer,
            "land_document_712": (io.BytesIO(b"\x89PNG\r\n\x1a\nvalid-712"), "anything-712.png"),
            "land_document_8a": (io.BytesIO(b"\x89PNG\r\n\x1a\nvalid-8a"), "anything-8a.png"),
        }, content_type="multipart/form-data")
        self.assertEqual(response.status_code, 302)
        with self.client.session_transaction() as session:
            otp = session["otp_code"]
        return self.client.post("/auth/verify-otp", data={"otp_code": otp})

    def test_registration_creates_pending_verification_and_blocks_login(self):
        response = self.register_farmer()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/auth/verification-status")
        farmer = User.query.filter_by(email="ramesh@example.com").one()
        verification = FarmerVerification.query.filter_by(user_id=farmer.id).one()
        self.assertEqual(verification.status, "PENDING")
        self.assertTrue(verification.document_712_path.replace("\\", "/").startswith("verification_documents/"))
        self.assertTrue(verification.document_8a_path.replace("\\", "/").startswith("verification_documents/"))

        answer = self.captcha_answer("/auth/login")
        blocked = self.client.post("/auth/login", data={"username": farmer.email, "password": "password", "captcha_answer": answer})
        self.assertEqual(blocked.status_code, 302)
        self.assertEqual(blocked.headers["Location"], "/auth/verification-status")

    def test_admin_can_view_document_approve_and_farmer_can_login(self):
        self.register_farmer()
        verification = FarmerVerification.query.one()
        self.login_admin()

        listed = self.client.get("/admin/farmer-verifications")
        self.assertEqual(listed.status_code, 200)
        document_712 = self.client.get(f"/admin/farmer-verification/{verification.id}/document?type=7/12")
        self.assertEqual(document_712.status_code, 200)
        self.assertTrue(document_712.data.startswith(b"\x89PNG"))
        document_8a = self.client.get(f"/admin/farmer-verification/{verification.id}/document?type=8-A")
        self.assertEqual(document_8a.status_code, 200)
        self.assertTrue(document_8a.data.startswith(b"\x89PNG"))

        approved = self.client.post(f"/admin/farmer-verification/{verification.id}/approve")
        self.assertEqual(approved.status_code, 302)
        self.assertEqual(FarmerVerification.query.one().status, "APPROVED")

    def test_non_admin_cannot_access_verification_routes(self):
        verification = FarmerVerification(user_id=1, document_type="7/12 and 8-A", document_path="verification_documents/missing.png", survey_number="", status="PENDING")
        self.assertEqual(self.client.get("/admin/farmer-verifications").status_code, 302)

    def test_registration_rejects_pdf_documents(self):
        answer = self.captcha_answer("/auth/register")
        response = self.client.post("/auth/register", data={
            "user_type": "farmer",
            "full_name": "PDF Farmer",
            "mobile": "8888888888",
            "email": "pdf-farmer@example.com",
            "password": "password",
            "confirm_password": "password",
            "captcha_answer": answer,
            "land_document_712": (io.BytesIO(b"%PDF-1.7\n7/12 pages"), "land-712.pdf"),
            "land_document_8a": (io.BytesIO(b"%PDF-1.7\n8-A pages"), "land-8a.pdf"),
        }, content_type="multipart/form-data", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        with self.client.session_transaction() as session:
            self.assertNotIn("otp_code", session)
        self.assertIn(b"Only JPG, JPEG, PNG, and WEBP land document images are allowed.", response.data)

    def test_registration_accepts_webp_camera_documents(self):
        answer = self.captcha_answer("/auth/register")
        webp_header = b"RIFF" + b"\x00\x00\x00\x00" + b"WEBP" + b"VP8 "
        response = self.client.post("/auth/register", data={
            "user_type": "farmer",
            "full_name": "WebP Farmer",
            "mobile": "7777777777",
            "email": "webp-farmer@example.com",
            "password": "password",
            "confirm_password": "password",
            "captcha_answer": answer,
            "land_document_712": (io.BytesIO(webp_header), "land-712.webp"),
            "land_document_8a": (io.BytesIO(webp_header), "land-8a.webp"),
        }, content_type="multipart/form-data")
        self.assertEqual(response.status_code, 302)
        with self.client.session_transaction() as session:
            otp = session["otp_code"]
        self.client.post("/auth/verify-otp", data={"otp_code": otp})
        verification = FarmerVerification.query.filter_by(document_type="7/12 and 8-A").one()
        self.assertTrue(verification.document_712_path.endswith(".webp"))
        self.assertTrue(verification.document_8a_path.endswith(".webp"))


if __name__ == "__main__":
    unittest.main()
