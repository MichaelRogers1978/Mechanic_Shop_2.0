import unittest
import uuid
import json
from sqlalchemy import text
from werkzeug.security import generate_password_hash
from app import create_app, db
from app.models import Customer, Admin
from app.autho.__init__ import encode_customer_token 
from app.autho.utils import encode_admin_token
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class CustomerRoutesTestCase(unittest.TestCase):

    def setUp(self):
        os.environ["SECRET_KEY"] = "super-secret-key"
        self.app = create_app("testing")
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()

            unique_username = f"adminuser_{uuid.uuid4().hex[:8]}"
            admin = Admin(
                username = unique_username,
                password = generate_password_hash("adminpass")
            )
            db.session.add(admin)

            unique_customer_email = f"customer_{uuid.uuid4().hex[:8]}@test.com"
            customer = Customer(
                name = "John Doe",
                email = unique_customer_email,
                phone = "1234567890",
                address = "1234 Test. St.",
                password = generate_password_hash("customerpass")
            )
            db.session.add(customer)
            db.session.commit()

            self.admin_id = admin.id
            self.customer_id = customer.id
            self.admin_token = encode_admin_token(self.admin_id)
            self.customer_token = encode_customer_token(self.customer_id)

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()

            db.drop_all()


    def test_customer_login_success(self):
        with self.app.app_context():
            email = Customer.query.get(self.customer_id).email
        data = {
            "email": email,
            "password": "customerpass"
        }
        response = self.client.post("/customers/login", data = json.dumps(data), content_type = "application/json")
        self.assertEqual(response.status_code, 200)
        self.assertIn("token", response.get_data(as_text = True))

    def test_customer_login_invalid_password(self):
        with self.app.app_context():
            email = Customer.query.get(self.customer_id).email
        data = {
            "email": email,
            "password": "wrongpass"
        }
        response = self.client.post("/customers/login", data = json.dumps(data), content_type = "application/json")
        self.assertEqual(response.status_code, 401)
        self.assertIn("Invalid email or password", response.get_data(as_text = True))

    def test_get_own_profile(self):
        headers = {"Authorization": f"Bearer {self.customer_token}"}
        response = self.client.get(f"/customers/{self.customer_id}", headers = headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn("John Doe", response.get_data(as_text = True))

    def test_customer_cannot_view_other_profile(self):
        with self.app.app_context():
            second_customer = Customer(
                name = "Jane Doe",
                email = f"jane_{uuid.uuid4().hex[:8]}@test.com",
                phone = "5555555555",
                address = "5678 Test St.",
                password = generate_password_hash("janepass")
            )
            db.session.add(second_customer)
            db.session.commit()
            second_customer_id = second_customer.id

        headers = {"Authorization": f"Bearer {self.customer_token}"}
        response = self.client.get(f"/customers/{second_customer_id}", headers = headers)
        self.assertEqual(response.status_code, 403)

    def test_admin_get_customers(self):
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        response = self.client.get("/customers/?page = 1&per_page = 5", headers = headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn("total", response.get_data(as_text=True))

    def test_admin_update_customer(self):
        data = {"name": "Updated Name"}
        headers = {
            "Authorization": f"Bearer {self.admin_token}",
            "Content-Type": "application/json"
        }
        response = self.client.put(f"/customers/admin/update/{self.customer_id}", data = json.dumps(data), headers = headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Updated Name", response.get_data(as_text = True))

    def test_customer_update_profile(self):
        data = {"name": "New Customer Name"}
        headers = {
            "Authorization": f"Bearer {self.customer_token}",
            "Content-Type": "application/json"
        }
        response = self.client.put(f"/customers/{self.customer_id}", data = json.dumps(data), headers = headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn("New Customer Name", response.get_data(as_text = True))

    def test_admin_delete_customer(self):
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        response = self.client.delete(f"/customers/admin/delete/{self.customer_id}", headers = headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn("deleted successfully", response.get_data(as_text = True))

    def test_add_customer(self):
        data = {
            "name": "New Customer",
            "email": f"new_{uuid.uuid4().hex[:8]}@test.com",
            "phone": "5555555555",
            "address": "789 New St.",
            "password": "newpassword"
            }
        headers = {
            "Authorization": f"Bearer {self.admin_token}",
            "Content-Type": "application/json"
        }
        headers = {
            "Authorization": f"Bearer {self.admin_token}",
            "Content-Type": "application/json"
        }
        response = self.client.post("/customers/", data = json.dumps(data), headers = headers)
        if response.status_code != 201:
            print("Response status:", response.status_code)
            print("Response data:", response.get_data(as_text = True))
        self.assertEqual(response.status_code, 201)
        self.assertIn("New Customer", response.get_data(as_text = True))

    def test_register_customer(self):
        data = {
            "name": "Registered Customer",
            "email": f"reg_{uuid.uuid4().hex[:8]}@test.com",
            "phone": "5555555556",
            "address": "123 Register St.",
            "password": "passwordddd"
        }
        response = self.client.post("/customers/register", data = json.dumps(data), content_type = "application/json")
        self.assertEqual(response.status_code, 201)
        self.assertIn("Registered Customer", response.get_data(as_text = True))

    def test_get_my_tickets(self):
        headers = {"Authorization": f"Bearer {self.customer_token}"}
        response = self.client.get("/customers/my-tickets", headers = headers)
        self.assertIn(response.status_code, [200, 404])

    def test_get_my_tickets_unauthorized(self):
        response = self.client.get("/customers/my-tickets")
        self.assertEqual(response.status_code, 401)

    def test_admin_get_customer_by_id(self):
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        response = self.client.get(f"/customers/admin/{self.customer_id}", headers = headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn("John Doe", response.get_data(as_text = True))

    def test_admin_get_customer_by_id_unauthorized(self):
        response = self.client.get(f"/customers/admin/{self.customer_id}")
        self.assertEqual(response.status_code, 401)

    def test_admin_update_customer_unauthorized(self):
        data = {"name": "Should Fail"}
        response = self.client.put(f"/customers/admin/update/{self.customer_id}", data = json.dumps(data), content_type = "application/json")
        self.assertEqual(response.status_code, 401)

    def test_customer_update_profile_unauthorized(self):
        data = {"name": "Should Fail"}
        response = self.client.put(f"/customers/{self.customer_id}", data = json.dumps(data), content_type = "application/json")
        self.assertEqual(response.status_code, 401)

    def test_admin_delete_customer_unauthorized(self):
        response = self.client.delete(f"/customers/admin/delete/{self.customer_id}")
        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()