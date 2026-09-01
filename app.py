import os
from datetime import datetime, timezone
from functools import wraps

from bson.objectid import ObjectId
from dotenv import load_dotenv
from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from werkzeug.security import check_password_hash, generate_password_hash


# ---------------------------------------------------------
# LOAD ENVIRONMENT VARIABLES
# ---------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(BASE_DIR, ".env")

load_dotenv(ENV_FILE, override=True)


# ---------------------------------------------------------
# FLASK CONFIGURATION
# ---------------------------------------------------------

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv(
    "SECRET_KEY",
    "dev-secret-change-me"
)

MONGO_URI = os.getenv("MONGO_URI", "").strip()
DB_NAME = os.getenv(
    "MONGO_DB",
    "it_support_system"
).strip()


# ---------------------------------------------------------
# MONGODB CONNECTION
# ---------------------------------------------------------

client = None
db = None
users = None
tickets = None


def connect_mongodb():
    """
    Connect to MongoDB Atlas.

    Returns True if the connection succeeds.
    Returns False if the connection fails.
    """

    global client, db, users, tickets

    # Read .env again in case it was changed
    load_dotenv(ENV_FILE, override=True)

    uri = os.getenv("MONGO_URI", "").strip()
    database_name = os.getenv(
        "MONGO_DB",
        "it_support_system"
    ).strip()

    if not uri:
        client = None
        db = None
        users = None
        tickets = None
        return False

    try:
        new_client = MongoClient(
            uri,
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=10000,
            socketTimeoutMS=10000
        )

        # Force an actual connection test
        new_client.admin.command("ping")

        new_db = new_client[database_name]

        # Store successful connection
        client = new_client
        db = new_db
        users = new_db["users"]
        tickets = new_db["tickets"]

        return True

    except PyMongoError as error:
        print("MongoDB connection failed:")
        print(error)

        client = None
        db = None
        users = None
        tickets = None

        return False


def ensure_database():
    """
    Make sure MongoDB is connected.
    If the connection was lost or was not available during
    startup, try connecting again.
    """

    global client, db, users, tickets

    if client is not None and db is not None:
        try:
            client.admin.command("ping")
            return True
        except PyMongoError:
            pass

    return connect_mongodb()


# Try connecting when the application starts
connect_mongodb()


# ---------------------------------------------------------
# LOGIN DECORATOR
# ---------------------------------------------------------

def login_required(f):

    @wraps(f)
    def w(*args, **kwargs):

        if "user_id" not in session:
            flash(
                "Please log in first.",
                "error"
            )
            return redirect(url_for("login"))

        return f(*args, **kwargs)

    return w


# ---------------------------------------------------------
# ROLE DECORATOR
# ---------------------------------------------------------

def role_required(*roles):

    def decorator(f):

        @wraps(f)
        def w(*args, **kwargs):

            if "user_id" not in session:
                return redirect(url_for("login"))

            if session.get("role") not in roles:
                flash(
                    "You do not have permission to access that page.",
                    "error"
                )
                return redirect(url_for("dashboard"))

            return f(*args, **kwargs)

        return w

    return decorator


# ---------------------------------------------------------
# DATABASE DECORATOR
# ---------------------------------------------------------

def database_required(f):

    @wraps(f)
    def w(*args, **kwargs):

        if not ensure_database():
            flash(
                "MongoDB is not connected. "
                "Check your .env MONGO_URI and Atlas Network Access.",
                "error"
            )
            return redirect(url_for("login"))

        return f(*args, **kwargs)

    return w


# ---------------------------------------------------------
# TEMPLATE CONTEXT
# ---------------------------------------------------------

@app.context_processor
def ctx():

    return {
        "current_user": session.get("name"),
        "current_role": session.get("role"),
    }


# ---------------------------------------------------------
# HOME
# ---------------------------------------------------------

@app.route("/")
def index():

    if "user_id" in session:
        return redirect(url_for("dashboard"))

    return redirect(url_for("login"))


# ---------------------------------------------------------
# EMPLOYEE LOGIN
# ---------------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
@database_required
def login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        if not email or not password:

            flash(
                "Email and password are required.",
                "error"
            )

            return render_template("login.html")

        user = users.find_one({
            "email": email
        })

        if not user:

            flash(
                "Invalid email or password.",
                "error"
            )

            return render_template("login.html")

        if not check_password_hash(
            user["password"],
            password
        ):

            flash(
                "Invalid email or password.",
                "error"
            )

            return render_template("login.html")

        session.clear()

        session.update({
            "user_id": str(user["_id"]),
            "name": user["name"],
            "role": user["role"]
        })

        return redirect(
            url_for("dashboard")
        )

    return render_template("login.html")


# ---------------------------------------------------------
# SUPPORT STAFF LOGIN
# ---------------------------------------------------------

@app.route(
    "/staff-login",
    methods=["GET", "POST"]
)
@database_required
def staff_login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        user = users.find_one({
            "email": email,
            "role": "support_staff"
        })

        if not user or not check_password_hash(
            user["password"],
            password
        ):

            flash(
                "Invalid support staff credentials.",
                "error"
            )

            return render_template(
                "staff_login.html"
            )

        session.clear()

        session.update({
            "user_id": str(user["_id"]),
            "name": user["name"],
            "role": user["role"]
        })

        return redirect(
            url_for("staff_queue")
        )

    return render_template(
        "staff_login.html"
    )


# ---------------------------------------------------------
# REGISTRATION
# ---------------------------------------------------------

@app.route(
    "/register",
    methods=["GET", "POST"]
)
@database_required
def register():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        if not name or not email or not password:

            flash(
                "All fields are required.",
                "error"
            )

            return render_template(
                "register.html"
            )

        if password != confirm_password:

            flash(
                "Passwords do not match.",
                "error"
            )

            return render_template(
                "register.html"
            )

        if len(password) < 6:

            flash(
                "Password must contain at least 6 characters.",
                "error"
            )

            return render_template(
                "register.html"
            )

        if users.find_one({
            "email": email
        }):

            flash(
                "An account with that email already exists.",
                "error"
            )

            return render_template(
                "register.html"
            )

        users.insert_one({
            "name": name,
            "email": email,
            "password": generate_password_hash(
                password
            ),
            "role": "employee",
            "created_at": datetime.now(timezone.utc)
        })

        flash(
            "Registration successful. You can now log in.",
            "success"
        )

        return redirect(
            url_for("login")
        )

    return render_template(
        "register.html"
    )


# ---------------------------------------------------------
# LOGOUT
# ---------------------------------------------------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# ---------------------------------------------------------
# EMPLOYEE DASHBOARD
# ---------------------------------------------------------

@app.route("/dashboard")
@login_required
@database_required
def dashboard():

    if session.get("role") == "support_staff":

        return redirect(
            url_for("staff_queue")
        )

    employee_id = ObjectId(
        session["user_id"]
    )

    my_tickets = list(
        tickets.find({
            "employee_id": employee_id
        })
        .sort("created_at", -1)
        .limit(5)
    )

    total = tickets.count_documents({
        "employee_id": employee_id
    })

    open_count = tickets.count_documents({
        "employee_id": employee_id,
        "status": "Open"
    })

    progress_count = tickets.count_documents({
        "employee_id": employee_id,
        "status": "In Progress"
    })

    return render_template(
        "dashboard.html",
        my_tickets=my_tickets,
        total=total,
        open_count=open_count,
        progress_count=progress_count
    )


# ---------------------------------------------------------
# CREATE SUPPORT TICKET
# ---------------------------------------------------------

@app.route(
    "/tickets/create",
    methods=["GET", "POST"]
)
@role_required("employee")
@database_required
def create_ticket():

    if request.method == "POST":

        title = request.form.get(
            "title",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        priority = request.form.get(
            "priority",
            ""
        )

        errors = []

        if not title:
            errors.append(
                "Title is required."
            )

        if not description:
            errors.append(
                "Description is required."
            )

        if priority not in {
            "Low",
            "Medium",
            "High"
        }:

            errors.append(
                "Please select a valid priority."
            )

        if errors:

            for error in errors:

                flash(
                    error,
                    "error"
                )

            return render_template(
                "create_ticket.html",
                form=request.form
            )

        now = datetime.now(timezone.utc)

        result = tickets.insert_one({

            "title": title,

            "description": description,

            "priority": priority,

            "status": "Open",

            "employee_id": ObjectId(
                session["user_id"]
            ),

            "employee_name": session["name"],

            "resolution": "",

            "created_at": now,

            "updated_at": now
        })

        return redirect(
            url_for(
                "ticket_success",
                ticket_id=str(
                    result.inserted_id
                )
            )
        )

    return render_template(
        "create_ticket.html",
        form={}
    )


# ---------------------------------------------------------
# TICKET SUBMISSION SUCCESS
# ---------------------------------------------------------

@app.route(
    "/tickets/success/<ticket_id>"
)
@role_required("employee")
@database_required
def ticket_success(ticket_id):

    try:

        ticket = tickets.find_one({
            "_id": ObjectId(ticket_id),
            "employee_id": ObjectId(
                session["user_id"]
            )
        })

    except Exception:

        ticket = None

    if not ticket:

        flash(
            "Ticket not found.",
            "error"
        )

        return redirect(
            url_for("dashboard")
        )

    return render_template(
        "success.html",
        ticket=ticket
    )


# ---------------------------------------------------------
# EMPLOYEE TICKET LIST
# ---------------------------------------------------------

@app.route("/tickets")
@role_required("employee")
@database_required
def my_tickets():

    employee_id = ObjectId(
        session["user_id"]
    )

    ticket_list = list(
        tickets.find({
            "employee_id": employee_id
        })
        .sort("created_at", -1)
    )

    return render_template(
        "tickets.html",
        tickets=ticket_list
    )


# ---------------------------------------------------------
# TICKET DETAILS
# ---------------------------------------------------------

@app.route(
    "/tickets/<ticket_id>"
)
@login_required
@database_required
def ticket_details(ticket_id):

    try:

        ticket = tickets.find_one({
            "_id": ObjectId(ticket_id)
        })

    except Exception:

        ticket = None

    if not ticket:

        flash(
            "Ticket not found.",
            "error"
        )

        return redirect(
            url_for("dashboard")
        )

    # Employees can only view their own tickets
    if (
        session.get("role") == "employee"
        and str(ticket["employee_id"])
        != session["user_id"]
    ):

        flash(
            "You cannot access that ticket.",
            "error"
        )

        return redirect(
            url_for("dashboard")
        )

    return render_template(
        "ticket_details.html",
        ticket=ticket
    )


# ---------------------------------------------------------
# SUPPORT STAFF QUEUE
# ---------------------------------------------------------

@app.route("/staff/queue")
@role_required("support_staff")
@database_required
def staff_queue():

    ticket_list = list(
        tickets.find()
        .sort("created_at", -1)
    )

    return render_template(
        "staff_queue.html",
        tickets=ticket_list
    )


# ---------------------------------------------------------
# SUPPORT STAFF MANAGE TICKET
# ---------------------------------------------------------

@app.route(
    "/staff/tickets/<ticket_id>",
    methods=["GET", "POST"]
)
@role_required("support_staff")
@database_required
def manage_ticket(ticket_id):

    try:

        ticket_object_id = ObjectId(
            ticket_id
        )

        ticket = tickets.find_one({
            "_id": ticket_object_id
        })

    except Exception:

        ticket = None

    if not ticket:

        flash(
            "Ticket not found.",
            "error"
        )

        return redirect(
            url_for("staff_queue")
        )

    if request.method == "POST":

        action = request.form.get(
            "action"
        )

        status = request.form.get(
            "status",
            ticket.get("status", "Open")
        )

        resolution = request.form.get(
            "resolution",
            ""
        ).strip()

        valid_statuses = {
            "Open",
            "In Progress",
            "Resolved",
            "Closed"
        }

        if status not in valid_statuses:

            flash(
                "Invalid status.",
                "error"
            )

            return render_template(
                "manage_ticket.html",
                ticket=ticket
            )

        update = {
            "status": status,
            "updated_at": datetime.now(timezone.utc)
        }

        if action in {
            "add_resolution",
            "close"
        }:

            update["resolution"] = resolution

        if action == "close":

            update["status"] = "Closed"

        tickets.update_one(
            {
                "_id": ticket_object_id
            },
            {
                "$set": update
            }
        )

        flash(
            "Ticket updated successfully.",
            "success"
        )

        return redirect(
            url_for(
                "manage_ticket",
                ticket_id=ticket_id
            )
        )

    return render_template(
        "manage_ticket.html",
        ticket=ticket
    )


# ---------------------------------------------------------
# HEALTH CHECK
# ---------------------------------------------------------

@app.route("/health")
def health():

    if not ensure_database():

        return {
            "status": "error",
            "mongodb": "not connected"
        }, 503

    try:

        client.admin.command("ping")

        return {
            "status": "ok",
            "mongodb": "connected"
        }, 200

    except PyMongoError as error:

        print("Health check MongoDB error:")
        print(error)

        return {
            "status": "error",
            "mongodb": "not connected"
        }, 503


# ---------------------------------------------------------
# RUN APPLICATION
# ---------------------------------------------------------

if __name__ == "__main__":

    print("")
    print("=" * 55)
    print("IT SUPPORT TICKET SYSTEM")
    print("=" * 55)

    if ensure_database():

        print("MongoDB: CONNECTED")

    else:

        print("MongoDB: NOT CONNECTED")

    print("=" * 55)
    print("Starting Flask application...")
    print("=" * 55)
    print("")

    app.run(
        host="0.0.0.0",
        port=int(
            os.getenv(
                "PORT",
                "5000"
            )
        ),
        debug=False
    )