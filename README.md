# IT Support Ticket System

Assessment-scale Flask + MongoDB IT Support Ticket System.

## Employee workflow
Register -> Login -> Dashboard -> Create Ticket -> Submit -> Success -> My Tickets -> Ticket Details.

## Support staff workflow
Staff Login -> Ticket Queue -> Manage Ticket -> Update Status / Add Resolution / Close Ticket.

## Stack
Python, Flask, MongoDB Atlas, PyMongo, HTML/CSS, Werkzeug password hashing, AWS EC2.

## Setup
1. Install Python 3.12+ and create a virtual environment.
2. Install: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env`.
4. Put your MongoDB Atlas URI in `MONGO_URI`.
5. Configure Atlas Network Access.
6. Run `python app.py`.
7. Open `http://127.0.0.1:5000`.

## MongoDB
The app uses `users` and `tickets` collections in the `it_support_system` database. Credentials are read from `.env`; `.env` is ignored by Git.

## Staff account
Register an employee account, then change its `role` field to `support_staff` in MongoDB Atlas for testing the staff workflow.

## Health check
`/health` returns MongoDB connection status.

## Deployment
Manual EC2 deployment is supported. Configure the server environment with `.env`, install requirements, run the Flask app, and expose the required port or use a reverse proxy. Never commit credentials.

## Known limitations
Assessment-scale implementation: no email notifications, password reset, attachments, advanced admin console, or CI/CD.

## Evidence placeholders
Add the actual GitHub URL, PR URL, release/tag, Figma view-only URL, and EC2 public URL to the final submission document.
