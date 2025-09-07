import unittest
import json
from werkzeug.security import generate_password_hash
from app import create_app, db
from app.models import Mechanic, Inventory
from app.autho.__init__ import encode_mechanic_token
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class InventoryRoutesTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app("testing")
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()

            mechanic = Mechanic(
                name = "Test Mechanic",
                username = "mechtest",
                email = "mech@test.com",
                phone = "55512345",
                address = "123 Inventory Rd.",
                password = generate_password_hash("mechpass"),
                hours_worked = 0,
                specialty = "General"
            )
            db.session.add(mechanic)

            part = Inventory(
                name = "Brake Pad",
                price = 49.99,
                quantity = 15
            )
            db.session.add(part)
            db.session.commit()

            self.mechanic_id = mechanic.id
            self.part_id = part.id
            self.mechanic_token = encode_mechanic_token(self.mechanic_id)

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_get_parts_public(self):
        response = self.client.get("/inventory/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Brake Pad", response.get_data(as_text = True))

    def test_get_part_public(self):
        response = self.client.get(f"/inventory/{self.part_id}")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Brake Pad", response.get_data(as_text = True))

    def test_search_parts_public(self):
        response = self.client.get("/inventory/search?q=Brake")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Brake Pad", response.get_data(as_text = True))

    def test_search_parts_public_no_query(self):
        response = self.client.get("/inventory/search")
        self.assertEqual(response.status_code, 400)
        self.assertIn("Search query required", response.get_data(as_text = True))

    def test_mechanic_add_part(self):
        data = {
            "name": "Oil Filter",
            "price": 9.99,
            "quantity": 25
        }
        headers = {
            "Authorization": f"Bearer {self.mechanic_token}",
            "Content-Type": "application/json"
        }
        response = self.client.post("/inventory/", data = json.dumps(data), headers = headers)
        self.assertEqual(response.status_code, 201)
        self.assertIn("Oil Filter", response.get_data(as_text = True))

    def test_mechanic_add_part_duplicate(self):
        data = {
            "name": "Brake Pad",
            "price": 39.99,
            "quantity": 10
        }
        headers = {"Authorization": f"Bearer {self.mechanic_token}"}
        response = self.client.post("/inventory/", data = json.dumps(data), headers = headers, content_type = "application/json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("already exists", response.get_data(as_text = True))

    def test_mechanic_get_parts(self):
        headers = {"Authorization": f"Bearer {self.mechanic_token}"}
        response = self.client.get("/inventory/mechanic/", headers = headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Brake Pad", response.get_data(as_text = True))

    def test_mechanic_get_part(self):
        headers = {"Authorization": f"Bearer {self.mechanic_token}"}
        response = self.client.get(f"/inventory/mechanic/{self.part_id}", headers = headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Brake Pad", response.get_data(as_text = True))

    def test_mechanic_search_part(self):
        headers = {"Authorization": f"Bearer {self.mechanic_token}"}
        response = self.client.get("/inventory/mechanic/search?q=Brake Pad", headers = headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Brake Pad", response.get_data(as_text = True))

    def test_mechanic_search_not_found(self):
        headers = {"Authorization": f"Bearer {self.mechanic_token}"}
        response = self.client.get("/inventory/mechanic/search?q=XYZ", headers = headers)
        self.assertEqual(response.status_code, 404)
        
    def test_mechanic_low_stock(self):
        headers = {"Authorization": f"Bearer {self.mechanic_token}"}
        response = self.client.get("/inventory/low-stock?threshold=20", headers = headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Brake Pad", response.get_data(as_text = True))

    def test_mechanic_update_part(self):
        data = {"quantity": 50}
        headers = {
            "Authorization": f"Bearer {self.mechanic_token}",
            "Content-Type": "application/json"
        }
        response = self.client.put(f"/inventory/{self.part_id}", data = json.dumps(data), headers = headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn("50", response.get_data(as_text = True))

    def test_mechanic_delete_part(self):
        headers = {"Authorization": f"Bearer {self.mechanic_token}"}
        response = self.client.delete(f"/inventory/{self.part_id}", headers = headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn("deleted successfully", response.get_data(as_text = True))

    def test_mechanic_get_parts_unauthorized(self):
        response = self.client.get("/inventory/mechanic/")
        self.assertEqual(response.status_code, 401)

    def test_mechanic_get_part_unauthorized(self):
        response = self.client.get(f"/inventory/mechanic/{self.part_id}")
        self.assertEqual(response.status_code, 401)

    def test_mechanic_search_unauthorized(self):
        response = self.client.get("/inventory/mechanic/search?q = Brake Pad")
        self.assertEqual(response.status_code, 401)

    def test_mechanic_low_stock_unauthorized(self):
        response = self.client.get("/inventory/low-stock?threshold = 20")
        self.assertEqual(response.status_code, 401)

    def test_mechanic_add_part_unauthorized(self):
        data = {"name": "Unauthorized Part", "price": 5.99, "quantity": 10}
        response = self.client.post("/inventory/", data = json.dumps(data), content_type = "application/json")
        self.assertEqual(response.status_code, 401)

    def test_mechanic_update_part_unauthorized(self):
        data = {"quantity": 99}
        response = self.client.put(f"/inventory/{self.part_id}", data = json.dumps(data), content_type = "application/json")
        self.assertEqual(response.status_code, 401)

    def test_mechanic_delete_part_unauthorized(self):
        response = self.client.delete(f"/inventory/{self.part_id}")
        self.assertEqual(response.status_code, 401)

    def test_mechanic_update_nonexistent_part(self):
        headers = {"Authorization": f"Bearer {self.mechanic_token}", "Content-Type": "application/json"}
        response = self.client.put("/inventory/9999", data = json.dumps({"quantity": 10}), headers = headers)
        if response.status_code != 404:
            print("Update nonexistent part failed:", response.get_json())
        self.assertEqual(response.status_code, 404)

    def test_mechanic_delete_nonexistent_part(self):
        headers = {"Authorization": f"Bearer {self.mechanic_token}", "Content-Type": "application/json"}
        response = self.client.delete("/inventory/9999", headers = headers)
        if response.status_code != 404:
            print("Delete nonexistent part failed:", response.get_json())
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()