import unittest
import json
from werkzeug.security import generate_password_hash
from app import create_app, db
from app.models import Customer, Mechanic, ServiceTicket, Inventory
from app.autho.__init__ import encode_token, encode_mechanic_token
from app.autho.utils import encode_admin_token
import sys
import os
from tests.base import BaseTestCase

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestServiceTicketRoutes(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.create_test_ticket()
        
def create_test_ticket(self):
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    
    customer = Customer(
        name = "John Doe",
        email = f"john{unique_id}@test.com",
        password = generate_password_hash("pass123"),
        phone = "12345670",
        address = "589 Help Way"
    )
    db.session.add(customer)
    
    mechanic = Mechanic(
        name = "Jane Mechanic",
        username = f"janemech{unique_id}",
        email = f"jane{unique_id}@test.com",
        phone = "123456788",
        address = "456 Mechanic Ave",
        password = generate_password_hash("mech123"),
        hours_worked = 0,
        specialty = "Engine"
        )
    db.session.add(mechanic)

    part = Inventory(
        name = "Test Part",
        price = 19.99,
        quantity = 10
    )
    db.session.add(part)
    db.session.flush()

    ticket = ServiceTicket(description = "Oil change", status="open", customer_id = customer.id)
    ticket.mechanics.append(mechanic)
    ticket.parts.append(part)
    db.session.add(ticket)
    db.session.commit()

    self.customer_id = customer.id
    self.mechanic_id = mechanic.id
    self.ticket_id = ticket.id
    self.part_id = part.id
    self.customer_token = encode_token(self.customer_id)
    self.mechanic_token = encode_mechanic_token(self.mechanic_id)
    self.admin_token = encode_admin_token(1)

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_get_single_ticket_admin(self):
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        response = self.client.get(f"/service-tickets/{self.ticket_id}", headers = headers)
        self.assertEqual(response.status_code, 200)

    def test_get_single_ticket_unauthorized(self):
        response = self.client.get(f"/service-tickets/{self.ticket_id}")
        self.assertEqual(response.status_code, 401)

    def test_get_ticket_mechanics_mechanic(self):
        headers = {"Authorization": f"Bearer {self.mechanic_token}"}
        response = self.client.get(f"/service-tickets/{self.ticket_id}/mechanics", headers = headers)
        self.assertEqual(response.status_code, 200)

    def test_get_ticket_mechanics_unauthorized(self):
        response = self.client.get(f"/service-tickets/{self.ticket_id}/mechanics")
        self.assertEqual(response.status_code, 401)

    def test_get_mechanic_ticket_count_admin(self):
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        response = self.client.get(f"/service-tickets/mechanic/{self.mechanic_id}/count", headers = headers)
        self.assertEqual(response.status_code, 200)

    def test_get_mechanic_ticket_count_unauthorized(self):
        response = self.client.get(f"/service-tickets/mechanic/{self.mechanic_id}/count")
        self.assertEqual(response.status_code, 401)

    def test_get_customer_ticket_count_admin(self):
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        response = self.client.get(f"/service-tickets/customer/{self.customer_id}/count", headers = headers)
        self.assertEqual(response.status_code, 200)

    def test_get_customer_ticket_count_unauthorized(self):
        response = self.client.get(f"/service-tickets/customer/{self.customer_id}/count")
        self.assertEqual(response.status_code, 401)

    def test_get_my_assigned_tickets_mechanic(self):
        headers = {"Authorization": f"Bearer {self.mechanic_token}"}
        response = self.client.get("/service-tickets/mechanic/my-tickets", headers = headers)
        self.assertEqual(response.status_code, 200)

    def test_get_my_assigned_tickets_unauthorized(self):
        response = self.client.get("/service-tickets/mechanic/my-tickets")
        self.assertEqual(response.status_code, 401)

    def test_add_part_to_ticket_mechanic(self):
        headers = {"Authorization": f"Bearer {self.mechanic_token}"}
        inventory_id = self.part_id
        response = self.client.put(f"/service-tickets/{self.ticket_id}/add-part/{inventory_id}", headers = headers)
        self.assertIn(response.status_code, [200, 404])

    def test_add_part_to_ticket_unauthorized(self):
        inventory_id = self.part_id
        response = self.client.put(f"/service-tickets/{self.ticket_id}/add-part/{inventory_id}")
        self.assertEqual(response.status_code, 401)

    def test_remove_part_from_ticket_mechanic(self):
        headers = {"Authorization": f"Bearer {self.mechanic_token}"}
        inventory_id = self.part_id
        response = self.client.put(
            f"/service-tickets/{self.ticket_id}/remove-part/{inventory_id}",
            headers=headers,
            json = {"mechanic_id": self.mechanic_id}
        )
        self.assertIn(response.status_code, [200, 404])

    def test_remove_part_from_ticket_unauthorized(self):
        inventory_id = self.part_id
        response = self.client.put(f"/service-tickets/{self.ticket_id}/remove-part/{inventory_id}")
        self.assertEqual(response.status_code, 401)

    def test_update_ticket_status_admin(self):
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        data = {"status": "completed"}
        response = self.client.put(f"/service-tickets/{self.ticket_id}/status", data = json.dumps(data), headers = headers, content_type = "application/json")
        self.assertIn(response.status_code, [200, 400])

    def test_update_ticket_status_unauthorized(self):
        data = {"status": "completed"}
        response = self.client.put(f"/service-tickets/{self.ticket_id}/status", data = json.dumps(data), content_type = "application/json")
        self.assertEqual(response.status_code, 401)

    def test_update_ticket_details_admin(self):
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        data = {"description": "Updated desc"}
        response = self.client.put(f"/service-tickets/{self.ticket_id}/update", data = json.dumps(data), headers = headers, content_type = "application/json")
        self.assertIn(response.status_code, [200, 400])

    def test_update_ticket_details_unauthorized(self):
        data = {"description": "Updated desc"}
        response = self.client.put(f"/service-tickets/{self.ticket_id}/update", data = json.dumps(data), content_type = "application/json")
        self.assertEqual(response.status_code, 401)

    def test_create_service_ticket(self):
        data = {
            "description": "Brake repair",
            "status": "open",
            "customer_id": self.customer_id
        }
        headers = {
            "Authorization": f"Bearer {self.mechanic_token}",
            "Content-Type": "application/json"
        }
        response = self.client.post("/service-tickets/mechanic/create", data = json.dumps(data), headers = headers)
        self.assertEqual(response.status_code, 201)
        self.assertIn("Brake repair", response.get_data(as_text = True))

    def test_create_ticket_missing_field(self):
        data = {"status": "open"}
        headers = {"Authorization": f"Bearer {self.mechanic_token}"}
        response = self.client.post("/service-tickets/mechanic/create", data = json.dumps(data), headers = headers, content_type = "application/json")
        self.assertEqual(response.status_code, 400)

    def test_get_all_tickets(self):
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        response = self.client.get("/service-tickets/", headers = headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Oil change", response.get_data(as_text = True))

    def test_assign_mechanic_to_ticket(self):
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        response = self.client.put(f"/service-tickets/{self.ticket_id}/assign-mechanic/{self.mechanic_id}", headers = headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn("assigned", response.get_data(as_text = True))

    def test_remove_mechanic_from_ticket(self):
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        self.client.put(f"/service-tickets/{self.ticket_id}/assign-mechanic/{self.mechanic_id}", headers = headers)
        response = self.client.put(f"/service-tickets/{self.ticket_id}/remove-mechanic/{self.mechanic_id}", headers = headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn("removed", response.get_data(as_text = True))

    def test_update_ticket_add_and_remove_mechanics(self):
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        data = {
            "add_ids": [self.mechanic_id],
            "remove_ids": []
        }
        response = self.client.put(f"/service-tickets/{self.ticket_id}/update", data = json.dumps(data), headers = headers, content_type = "application/json")
        self.assertEqual(response.status_code, 200)
        self.assertIn("updated", response.get_data(as_text = True))

    def test_delete_ticket(self):
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        response = self.client.delete(f"/service-tickets/{self.ticket_id}", headers = headers)
        self.assertIn(response.status_code, [404, 405])

    def test_get_my_tickets(self):
        headers = {"Authorization": f"Bearer {self.customer_token}"}
        response = self.client.get("/service-tickets/customer/my-tickets", headers = headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Oil change", response.get_data(as_text = True))


if __name__ == "__main__":
    unittest.main()