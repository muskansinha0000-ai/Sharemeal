
from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "sharemeal-development-key"

DATABASE = os.path.join(app.root_path, "sharemeal.db")


def get_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()

    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user'
        );

        CREATE TABLE IF NOT EXISTS donations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            food_name TEXT NOT NULL,
            quantity TEXT NOT NULL,
            location TEXT NOT NULL,
            pickup_time TEXT NOT NULL,
            description TEXT,
            status TEXT NOT NULL DEFAULT 'Available',
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS pickup_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            donation_id INTEGER NOT NULL,
            requester_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            FOREIGN KEY (donation_id) REFERENCES donations(id),
            FOREIGN KEY (requester_id) REFERENCES users(id)
        );
    """)

    admin = conn.execute(
        "SELECT id FROM users WHERE email = ?",
        ("admin@sharemeal.com",)
    ).fetchone()

    if not admin:
        conn.execute(
            """INSERT INTO users (name, email, password, role)
               VALUES (?, ?, ?, ?)""",
            (
                "ShareMeal Admin",
                "admin@sharemeal.com",
                generate_password_hash("Admin@123"),
                "admin"
            )
        )

    conn.commit()
    conn.close()


@app.route("/")
def home():
    conn = get_connection()
    donations = conn.execute(
        "SELECT * FROM donations WHERE status = 'Available' ORDER BY id DESC"
    ).fetchall()
    conn.close()
    return render_template("home.html", donations=donations)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or len(password) < 6:
            flash("Enter all details. Password must have at least 6 characters.")
            return redirect(url_for("register"))

        conn = get_connection()
        try:
            conn.execute(
                "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                (name, email, generate_password_hash(password))
            )
            conn.commit()
            flash("Registration successful. Please log in.")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("This email is already registered.")
        finally:
            conn.close()

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = get_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["role"] = user["role"]

            if user["role"] == "admin":
                return redirect(url_for("admin"))
            return redirect(url_for("home"))

        flash("Invalid email or password.")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/donate", methods=["GET", "POST"])
def donate():
    if "user_id" not in session:
        flash("Please log in before donating food.")
        return redirect(url_for("login"))

    if request.method == "POST":
        food_name = request.form.get("food_name", "").strip()
        quantity = request.form.get("quantity", "").strip()
        location = request.form.get("location", "").strip()
        pickup_time = request.form.get("pickup_time", "").strip()
        description = request.form.get("description", "").strip()

        if not all([food_name, quantity, location, pickup_time]):
            flash("Please fill in all required fields.")
            return redirect(url_for("donate"))

        conn = get_connection()
        conn.execute(
            """INSERT INTO donations
               (user_id, food_name, quantity, location, pickup_time, description)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                session["user_id"], food_name, quantity,
                location, pickup_time, description
            )
        )
        conn.commit()
        conn.close()

        flash("Your food donation has been added!")
        return redirect(url_for("home"))

    return render_template("donate.html")


@app.route("/request-pickup/<int:donation_id>", methods=["POST"])
def request_pickup(donation_id):
    if "user_id" not in session:
        flash("Please log in to request a pickup.")
        return redirect(url_for("login"))

    conn = get_connection()
    donation = conn.execute(
        "SELECT * FROM donations WHERE id = ? AND status = 'Available'",
        (donation_id,)
    ).fetchone()

    if not donation:
        conn.close()
        flash("This donation is no longer available.")
        return redirect(url_for("home"))

    if donation["user_id"] == session["user_id"]:
        conn.close()
        flash("You cannot request your own donation.")
        return redirect(url_for("home"))

    existing = conn.execute(
        """SELECT id FROM pickup_requests
           WHERE donation_id = ? AND requester_id = ? AND status = 'Pending'""",
        (donation_id, session["user_id"])
    ).fetchone()

    if existing:
        flash("You already have a pending request for this donation.")
    else:
        conn.execute(
            """INSERT INTO pickup_requests (donation_id, requester_id)
               VALUES (?, ?)""",
            (donation_id, session["user_id"])
        )
        conn.commit()
        flash("Pickup request submitted!")

    conn.close()
    return redirect(url_for("home"))


@app.route("/admin")
def admin():
    if session.get("role") != "admin":
        flash("Please log in as an administrator.")
        return redirect(url_for("login"))

    conn = get_connection()

    users = conn.execute(
        "SELECT id, name, email, role FROM users ORDER BY id DESC"
    ).fetchall()

    donations = conn.execute(
        """SELECT donations.*, users.name AS donor_name
           FROM donations
           LEFT JOIN users ON donations.user_id = users.id
           ORDER BY donations.id DESC"""
    ).fetchall()

    requests = conn.execute(
        """SELECT pickup_requests.*, donations.food_name,
                  users.name AS requester_name
           FROM pickup_requests
           JOIN donations ON pickup_requests.donation_id = donations.id
           JOIN users ON pickup_requests.requester_id = users.id
           ORDER BY pickup_requests.id DESC"""
    ).fetchall()

    stats = {
        "users": conn.execute("SELECT COUNT(*) FROM users").fetchone()[0],
        "donations": conn.execute("SELECT COUNT(*) FROM donations").fetchone()[0],
        "requests": conn.execute("SELECT COUNT(*) FROM pickup_requests").fetchone()[0],
        "available": conn.execute(
            "SELECT COUNT(*) FROM donations WHERE status = 'Available'"
        ).fetchone()[0]
    }

    conn.close()

    return render_template(
        "admin.html",
        users=users,
        donations=donations,
        requests=requests,
        stats=stats
    )


@app.route("/admin/request/<int:request_id>/<action>", methods=["POST"])
def update_request(request_id, action):
    if session.get("role") != "admin":
        flash("Administrator access required.")
        return redirect(url_for("login"))

    if action not in ("approve", "reject"):
        flash("Invalid action.")
        return redirect(url_for("admin"))

    conn = get_connection()
    pickup = conn.execute(
        "SELECT * FROM pickup_requests WHERE id = ?", (request_id,)
    ).fetchone()

    if not pickup or pickup["status"] != "Pending":
        conn.close()
        flash("This request cannot be updated.")
        return redirect(url_for("admin"))

    if action == "approve":
        conn.execute(
            "UPDATE pickup_requests SET status = 'Approved' WHERE id = ?",
            (request_id,)
        )
        conn.execute(
            "UPDATE donations SET status = 'Reserved' WHERE id = ?",
            (pickup["donation_id"],)
        )
        flash("Pickup request approved.")
    else:
        conn.execute(
            "UPDATE pickup_requests SET status = 'Rejected' WHERE id = ?",
            (request_id,)
        )
        flash("Pickup request rejected.")

    conn.commit()
    conn.close()
    return redirect(url_for("admin"))



@app.route("/food-records")
def food_records():
    return render_template("food-records.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        flash("Please log in to view your dashboard.")
        return redirect(url_for("login"))
    return render_template("dashboard.html")


@app.route("/available-food")
def available_food():
    # The homepage is the live database-backed available-food listing.
    return redirect(url_for("home") + "#donations")


@app.route("/my-donations")
def my_donations():
    if "user_id" not in session:
        flash("Please log in to view your donations.")
        return redirect(url_for("login"))
    conn = get_connection()
    donations = conn.execute(
        "SELECT * FROM donations WHERE user_id = ? ORDER BY id DESC",
        (session["user_id"],)
    ).fetchall()
    conn.close()
    return render_template("my-donation.html", donations=donations)


@app.route("/request-food", methods=["GET", "POST"])
def request_food():
    if request.method == "POST":
        flash("For a live pickup request, please use the Request Pickup button on an available donation.")
        return redirect(url_for("home"))
    return render_template("request-food.html")


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
