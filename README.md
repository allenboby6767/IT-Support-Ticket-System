# IT Support Ticket System

## Employee workflow
Register -> Login -> Dashboard -> Create Ticket -> Submit -> Success -> My Tickets -> Ticket Details.

## Support staff workflow
Staff Login -> Ticket Queue -> Manage Ticket -> Update Status / Add Resolution / Close Ticket.

## Stack
Python, Flask, MongoDB Atlas, PyMongo, HTML/CSS, AWS EC2.

## Setup
1. Install Python 3.12+ and create a virtual environment.
2. Install: `pip install -r requirements.txt`
3. Put your MongoDB Atlas URI in `MONGO_URI`.
4. Configure Atlas Network Access.
5. Run `python app.py`.

## MongoDB
The app uses `users` and `tickets` collections in the `it_support_system` database. Credentials are read from `.env`; `.env` is ignored by Git.

## Staff account
Register an employee account, then change its `role` field to `support_staff` in MongoDB Atlas for testing the staff workflow.

## Deployment
Manual EC2 deployment is supported. Configure the server environment with `.env`, install requirements, run the Flask app, and expose the required port or use a reverse proxy. Never commit credentials.
