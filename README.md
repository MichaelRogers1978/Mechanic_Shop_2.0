Mechanic_Shop API:

Mechanic_Shop API is a scalable, full-featured RESTful API backend system for managing operations 
in an auto repair shop. It supports mechanic assignments, customer records, service tickets, and 
inventory parts with secure authentication and advanced query capabilities. Designed for 
maintainability and CI/CD deployment.

Built using Flask with modular architecture, the system emphasizes maintianability, reproducibility, and CI/CD deployment via GitHub Actions and Render 

1. Clone the repo  
2. Create a '.env' file with required secrets  
3. Run 'flask run' or use 'gunicorn' for production  
4. Access Swagger docs at '/docs'

  Blueprint Architecture

    Blueprints: 
      
      - mechanics, customers, service tickets, inventory
      - Each contians __init.py, routes.py, and schemas.py

    Registration: 

      - Registered in app/__init__.py with URL prefixes:
      - /mechanics, /service_tickets, /customers, /inventory
    
    Schemas: 

      - Defined using SQLAlchemyAutoSchema for serialization

    Mechanic Routes: 

      method                       Endpoint                 Description

    POST      /mechanics                                  Create a new mechanic
    GET       /mechanics                                  Retrieve all mechanics
    GET       /mechanics/<id>                             Retrieve mechanic by ID
    PUT       /mechanics/<id>                             Update mechanic by ID
    DELETE    /mechanics/admin/delete/<id>                Delete mechanic by ID

    Service Ticket Routes: 

      method                       Endpoint                 Description

    POST      /service-tickets/mechanic/create            Mechanic creates a new service ticket
    GET       /service-tickets                            Retrieve all service tickets
    GET       /service-tickets/<ticket_id>                Retrieve service ticket by ID
    PUT       /service-tickets/<ticket_id>/
                  assign-mechanic/<mechanic_id>           Assign mechanic to a ticket
    PUT       /service-tickets/<ticket_id>/
                  remove-mechanic/<mechanic_id>           Remove mechanic from a ticket

      Customer Routes: 

        method                       Endpoint                 Description

         POST                           /                 Create a new customer
         GET                            /                 Retrieve all customers
         GET                            /<id>             Retrieve customer by ID
         PUT                            /<id>             Update customer by ID
         DELETE                         /<id>             Delete customer by ID

      Inventory Routes: 

        method                       Endpoint                 Description

         POST                           /                 Add new inventory item
         GET                            /                 Retrieve all inventory items
         GET                            /<id>             Retrieve inventory item by ID
         PUT                            /<id>             Update inventory item by ID
         DELETE                         /<id>             Delete inventory item by ID

  Advance Features

    Rate limit and Caching:

      - Flask-Limiter: Applied to selected routes
      - Flask-Cachnig: Optimizes performance on frequent queries

    Token Authentication:

      - Customer Login:
        - POST/login: Return JWT after validation of credentials
      - Protected Route:
        - GET/mytickets: Returns tickets for authenticated customer
      - Decorators: 
        - @token_required: Validates token and passes customer_id
        
    Advance Queries:

      - PUT/<ticket_id>/edit: Add/remove mechanics from a ticket
      - GET/customers?page=1: Paginated customer list

  Inventory Integration

    Inventory Model:
      - Feilds: id, name, price
      - Many-to-many relationship with Service Ticket

    Inventory Routes: 

        method                       Endpoint                 Description

         POST                           /                 Create a new part
         GET                            /                 Retrieve all parts
         PUT                            /<id>             Update part details
         DELETE                         /<id>             Delete part from inventory

    Ticket-Part Integration

      - Ticket Part Integration:

        -PUT/ticket_id/add-part/<part_id>: Add part to service ticket     
  
  Documentation and Testing

    Swagger Documentation:
    
      - Built with Flask-Swagger and Flask-Swagger-UI

      - Each route includes:
        - Path, method, tag, summary, description
        - Security (for token routes)
        - Parameters and response definitions

    Unit Testing: 

      - Located in test/ folder

      - Files: test_mechanic, test_customers, test_inventory, test_service_tickets

      - Each route has:
        - Positive and negative

      - Run tests with:
        - python -m unittest discover -s app/tests

  Deployment and CI/CD

    Deployment to Render:

      - PostgreSQL database hosted on Render

      - Production config passed to create_app() in flask_app.py

      - Sensitive data stored in .env and accessed via os.environ

      - .env added to .gitignore

      - Swagger host updated to live API base URL

    CI/CD Pipeline:

     - GitHub Actions wrorkflow in .github/workflows/main.yaml

     - Jobs:
       - test: Runs unit tests
       - deploy: Deploys to Render (depending on test)

    - Secrets:
      - RENDER_SERVICE_ID, RENDER_API_KEY stored in GitHub

    Technologies Used:

      - Flask, SQLAlchemy, Marshmallow

      - Flask-Limiter, Flask-Caching

      - python-jose, gunicorn, plycopg2

      - Swagger UI, unittest

      - Render, GitHub Actions

## Reflections ##

Creating this project taught me the importance of migration integrity, secret hygiene, and
 reproducible environments. Cleaning up legacy folder structures and stabilizing CI/CD pipelines 
 pushed me to rethink how I document and validate project health. CI failures became my 
 compass - they pointed to architectural blind spots I hadn't considered. Debugging wasn't just 
 a fix, it was a revelation. I’ve since adopted defensive coding practices and automated tests 
 to catch regressions early. 

Key learnings:
- Avoid tracking '.env' files—rotate secrets and use '.gitignore' religiously.
- Validate migrations with test coverage to prevent schema drift.
- CI failures often reveal deeper architectural issues—embrace the debugging.

This project reflects my persistence, resilince and commitment to maintainable, secure, and
 collaborative development.  