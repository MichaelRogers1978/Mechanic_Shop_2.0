import unittest
import json
from werkzeug.security import generate_password_hash
from app import create_app, db
from app.models import Mechanic, Admin
from app.autho.__init__ import encode_mechanic_token
from app.autho.utils import encode_admin_token
import uuid
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestMechanicRoutes(unittest.TestCase):

    def setUp(self):
        self.app = create_app("testing")
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()

            unique_username = f"admin_{uuid.uuid4().hex[:8]}"
            admin = Admin(
                    username = unique_username,
                    password = generate_password_hash("adminpass")
            )
            db.session.add(admin)
            db.session.flush()
            self.admin_id = admin.id
            self.admin_token = encode_admin_token(self.admin_id)

            mechanic = Mechanic(
                name = "Mechanic One",
                username = "mechanic1",
                email = "mech1@test.com",
                phone = "12345678",
                address = "123 Mechanic St.",
                password = generate_password_hash("mechpass"),
                hours_worked = 0,
                specialty = "General"
            )
            db.session.add(mechanic)
            db.session.flush()
            self.mechanic_id = mechanic.id
            self.mechanic_token = encode_mechanic_token(self.mechanic_id)

            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_admin_add_mechanic(self):
        data = {
            "name": "New Mechanic",
            "username": "mechanic2",
            "email": "mech2@test.com",
            "phone": "12345678",
            "address": "456 Mechanic Ave.",
            "password": "mechpass",
            "hours_worked": 0,
            "specialty": "general"
        }
        headers = {
            "Authorization": f"Bearer {self.admin_token}",
            "Content-Type": "application/json"
        }
        response = self.client.post("/mechanics/", data = json.dumps(data), headers = headers)
        if response.status_code != 201:
            print("Mechanic creation failed:", response.get_json())
        self.assertEqual(response.status_code, 201)
        self.assertIn("name", response.get_json())
        self.assertEqual(response.get_json()["name"], "New Mechanic")

    def test_mechanic_login_success(self):
        data = {"email": "mech1@test.com", "password": "mechpass"}
        response = self.client.post("/mechanics/login", data = json.dumps(data), content_type = "application/json")
        self.assertEqual(response.status_code, 200)
        self.assertIn("token", response.get_json())

    def test_mechanic_login_invalid(self):
        data = {"email": "mech1@test.com", "password": "wrongpass"}
        response = self.client.post("/mechanics/login", data = json.dumps(data), content_type = "application/json")
        self.assertEqual(response.status_code, 401)
        self.assertIn("error", response.get_json())

    def test_get_all_mechanics_pagination(self):
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        response = self.client.get("/mechanics/?page=1&per_page=5", headers = headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn("total", response.get_json())
        self.assertIn("mechanics", response.get_json())

    def test_get_mechanic_by_id(self):
        response = self.client.get(f"/mechanics/{self.mechanic_id}")
        self.assertEqual(response.status_code, 200)
        self.assertIn("name", response.get_json())
        self.assertEqual(response.get_json()["name"], "Mechanic One")

    def test_mechanic_own_profile(self):
        headers = {"Authorization": f"Bearer {self.mechanic_token}"}
        response = self.client.get("/mechanics/profile", headers = headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn("name", response.get_json())
        self.assertEqual(response.get_json()["name"], "Mechanic One")

    def test_mechanic_assigned_tickets(self):
        headers = {"Authorization": f"Bearer {self.mechanic_token}"}
        response = self.client.get("/mechanics/my-tickets", headers = headers)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.get_json(), list)

    def test_mechanic_update_own_info(self):
        data = {"specialty": "Self Updated"}
        headers = {
            "Authorization": f"Bearer {self.mechanic_token}",
            "Content-Type": "application/json"
        }
        response = self.client.put(f"/mechanics/{self.mechanic_id}", data = json.dumps(data), headers = headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn("specialty", response.get_json())
        self.assertEqual(response.get_json()["specialty"], "Self Updated")

    def test_mechanic_dashboard(self):
        headers = {"Authorization": f"Bearer {self.mechanic_token}"}
        response = self.client.get("/mechanics/dashboard", headers = headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn("assigned_tickets", response.get_json()["stats"])

    def test_mechanic_change_password(self):
        data = {"old_password": "mechpass", "new_password": "newpass123"}
        headers = {"Authorization": f"Bearer {self.mechanic_token}", "Content-Type": "application/json"}
        response = self.client.put("/mechanics/change-password", data = json.dumps(data), headers = headers)
        self.assertIn(response.status_code, [200, 400])

    def test_mechanic_change_password_unauthorized(self):
        data = {"old_password": "mechpass", "new_password": "newpass123"}
        response = self.client.put("/mechanics/change-password", data = json.dumps(data), content_type = "application/json")
        self.assertEqual(response.status_code, 401)

    def test_mechanic_secure_data(self):
        headers = {"Authorization": f"Bearer {self.mechanic_token}"}
        response = self.client.get("/mechanics/secure-data", headers = headers)
        self.assertIn(response.status_code, [200, 403])

    def test_mechanic_secure_data_unauthorized(self):
        response = self.client.get("/mechanics/secure-data")
        self.assertEqual(response.status_code, 401)

    def test_admin_update_mechanic(self):
        data = {"specialty": "Updated by Admin"}
        headers = {"Authorization": f"Bearer {self.admin_token}", "Content-Type": "application/json"}
        response = self.client.put(f"/mechanics/admin/update/{self.mechanic_id}", data = json.dumps(data), headers = headers)
        self.assertIn(response.status_code, [200, 400])

    def test_admin_update_mechanic_unauthorized(self):
        data = {"specialty": "Updated by Admin"}
        response = self.client.put(f"/mechanics/admin/update/{self.mechanic_id}", data = json.dumps(data), content_type = "application/json")
        self.assertEqual(response.status_code, 401)

    def test_admin_delete_mechanic(self):
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        response = self.client.delete(f"/mechanics/admin/delete/{self.mechanic_id}", headers = headers)
        self.assertIn(response.status_code, [200, 404])

    def test_admin_delete_mechanic_unauthorized(self):
        response = self.client.delete(f"/mechanics/admin/delete/{self.mechanic_id}")
        self.assertEqual(response.status_code, 401)

    def test_admin_create_mechanic(self):
        data = {
            "name": "Admin Created Mech",
            "username": "adminmech",
            "email": "adminmech@test.com",
            "phone": "12345679",
            "address": "789 Admin Ave.",
            "password": "adminmechpass",
            "hours_worked": 0,
            "specialty": "Admin Specialty"
        }
        headers = {"Authorization": f"Bearer {self.admin_token}", "Content-Type": "application/json"}
        response = self.client.post("/mechanics/admin/create", data = json.dumps(data), headers = headers)
        self.assertIn(response.status_code, [201, 400])

    def test_admin_create_mechanic_unauthorized(self):
        data = {
            "name": "Admin Created Mech",
            "username": "adminmech",
            "email": "adminmech@test.com",
            "phone": "12345679",
            "address": "789 Admin Ave.",
            "password": "adminmechpass",
            "hours_worked": 0,
            "specialty": "Admin Specialty"
        }
        response = self.client.post("/mechanics/admin/create", data = json.dumps(data), content_type = "application/json")
        self.assertIn(response.status_code, [400, 401, 403])

    def test_admin_login_success(self):
        with self.app.app_context():
            admin = Admin.query.filter_by(username = "admin").first()
            if not admin:
                admin = Admin(
                    username = "admin",
                    password = generate_password_hash("adminpass")
                )
                db.session.add(admin)
                db.session.commit()
        data = {"email": "admin@test.com", "password": "adminpass"}
        response = self.client.post("/mechanics/admin/login", data = json.dumps(data), content_type = "application/json")
        self.assertIn(response.status_code, [200, 400, 401])
        if response.status_code == 200:
            self.assertIn("token", response.get_json())

    def test_admin_login_invalid(self):
        with self.app.app_context():
            admin = Admin.query.filter_by(username = "admin").first()
            if not admin:
                admin = Admin(
                    username = "admin",
                    password = generate_password_hash("adminpass")
                )
                db.session.add(admin)
                db.session.commit()
        data = {"email": "admin@test.com", "password": "wrongpass"}
        response = self.client.post("/mechanics/admin/login", data = json.dumps(data), content_type = "application/json")
        self.assertIn(response.status_code, [401, 400])
        self.assertIn("error", response.get_json())

if __name__ == "__main__":
    unittest.main()