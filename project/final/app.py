import os
import sys
import datetime
from datetime import datetime as dtime, time, timedelta
import requests
import sqlite3
import random
from bs4 import BeautifulSoup
from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from flask_session import Session
from functools import wraps
from cs50 import SQL
import pytz

# Initialize Flask app
app = Flask(__name__)

# Configure secret key
app.secret_key = "your_secret_key"  # Replace with your actual secret key

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# Set up database connections
# Connection to users.db
def get_users_db_connection():
    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row  # Enables column access by name: row['column_name']
    return conn


# Connection to huds.db
def get_huds_db_connection():
    db = SQL("sqlite:///huds.db")
    return db

# Global db initialization
db = get_huds_db_connection()
# Additional functions and routes will go here


# Bergdash User login required
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("You need to be logged in to access this page.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


# Insights Functions----------------------------------------------------------------------------------------------------------------

dashtoday = datetime.date.today()

# Get the current time (hour and minute)
dashcurrent_time = datetime.datetime.now().time()

# Get the current date
today = datetime.date.today()

# Get the current time (hour and minute)
current_time = datetime.datetime.now().time()
# Get current date and time
est_timezone = pytz.timezone('US/Eastern')

utc_now = dtime.utcnow()

est_now = utc_now.astimezone(est_timezone)

today = est_now.date()
current_time = est_now.time()

# Ensure responses aren't cached (optional but useful for development)
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Takes the html of any lunch/dinner page and returns the entrees
def lundinentree(samplehtml):
    # finds specific section of the code
    start_tag = samplehtml.find(
        lambda tag: tag.name == "tr" and "Entrees" in tag.get_text()
    )
    end_tag = samplehtml.find(
        lambda tag: tag.name == "tr" and "Veg,Vegan" in tag.get_text()
    )

    # this should (theoretically) add all of the entrees to a list called entrees
    if start_tag and end_tag:
        content_set = set()
        current_tag = start_tag.find_next()

        while current_tag and current_tag != end_tag:
            content_set.add(str(current_tag))
            current_tag = current_tag.find_next()

        content_between = "".join(content_set)

        soup_between = BeautifulSoup(content_between, "html.parser")
        entrees_tags = soup_between.find_all("a")

        # Extract text from each <a> tag and store in the entrees list
        unique_entrees = set(tag.get_text(strip=True) for tag in entrees_tags)

        # Convert the set to a list if needed
        entrees = list(unique_entrees)

        return entrees
    else:
        return None


# takes the breakfast page of any day and returns the entrees, if applicable
def breakentree(samplehtml):
    # finds specific section of the code
    start_tag = samplehtml.find(
        lambda tag: tag.name == "tr" and "Breakfast Meats" in tag.get_text()
    )
    end_tag = samplehtml.find(
        lambda tag: tag.name == "tr" and "Breakfast Bakery" in tag.get_text()
    )

    # this should (theoretically) add all of the entrees to a list called entrees
    if start_tag and end_tag:
        content_set = set()
        current_tag = start_tag.find_next()

        while current_tag and current_tag != end_tag:
            content_set.add(str(current_tag))
            current_tag = current_tag.find_next()

        content_between = "".join(content_set)

        soup_between = BeautifulSoup(content_between, "html.parser")
        entrees_tags = soup_between.find_all("a")

        # Extract text from each <a> tag and store in the entrees list
        unique_entrees = set(tag.get_text(strip=True) for tag in entrees_tags)

        # Convert the set to a list if needed
        entrees = list(unique_entrees)

        return entrees
    else:
        return None


# determines the date and meal of any meal num
def date_a_meal(mealnum):
    # determines the current meal date and meal(B, L, D)
    if current_time > time(19, 30, 0):
        cmealdate = today + timedelta(1)
        cmealnum = 0
    else:
        cmealdate = today
        if current_time < time(10, 30, 0):
            cmealnum = 0
        elif current_time < time(14, 0, 0):
            cmealnum = 1
        elif current_time < time(19, 30, 0):
            cmealnum = 2

    # finds the meal date of mealnum and calculates the meal (B, L, D) using math
    mealdate = cmealdate + timedelta((mealnum - mealnum % 3) / 3)
    meal = mealnum % 3 + cmealnum
    if cmealnum + mealnum % 3 < 0:
        mealdate = mealdate - timedelta(1)
        if meal == -1:
            meal = 2
        else:
            meal = 1
    elif cmealnum + mealnum % 3 > 2:
        mealdate = mealdate + timedelta(1)
        if meal == 3:
            meal = 0
        else:
            meal = 1

    return meal, mealdate


# returns the entrees for a meal number
def mealnumber(mealnum):
    # determines the current meal date and meal(B, L, D)
    meal, mealdate = date_a_meal(mealnum)

    # formats the date, and gets the url of that date's html
    fdate = f"{mealdate.month}-{mealdate.day}-{mealdate.year}"
    MYHTML = f"https://www.foodpro.huds.harvard.edu/foodpro/menu_items.asp?date={fdate}&type=30&meal={meal}"

    if meal == 0:
        return breakentree(BeautifulSoup(requests.get(MYHTML).content, "html.parser"))
    else:
        return lundinentree(BeautifulSoup(requests.get(MYHTML).content, "html.parser"))


def getdayofweek(date):
    if date == (today - timedelta(1)):
        return "Yesterday"
    elif date == today:
        return "Today"
    elif date == (today + timedelta(1)):
        return "Tommorow"
    else:
        return date.strftime("%A")


# Insights routes----------------------------------------------------------------------------------------------------------------------------
@app.route("/")
def index():
    # Finding average wait times based on the nearest 4 wait times
    # Num_of_times specifies how many wait times to base average off of
    num_of_times = 4

    current_wait_times = db.execute(
        "SELECT wait_time FROM wait_times ORDER BY ABS(wait_time - (:current_time)) LIMIT (:num_of_times);",
        current_time=current_time,
        num_of_times=num_of_times,
    )

    wait_time_calc = 0

    for row in current_wait_times:
        wait_time_calc += int(row["wait_time"])

    average_wait_time = round(wait_time_calc / len(current_wait_times))

    wait_time_txt = [
        "No wait",
        "Less than 5 minutes",
        "5-10 minutes",
        "More than 10 minutes",
    ]

    wait_time = wait_time_txt[average_wait_time]

    # Defining meals index
    nummeals = [-3, -2, -1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
    entreesdict = dict.fromkeys(nummeals)
    ratingsdict = dict.fromkeys(nummeals)
    commentsdict = dict.fromkeys(nummeals)
    dates = dict.fromkeys(nummeals)
    meal = dict.fromkeys(nummeals)
    datesofweek = dict.fromkeys(nummeals)

    for keys in entreesdict:
        entreesdict[keys] = mealnumber(keys)
        dates[keys] = date_a_meal(keys)[1]
        temp = date_a_meal(keys)[0]
        if temp == 0:
            meal[keys] = "breakfast"
        elif temp == 1:
            meal[keys] = "lunch"
        else:
            meal[keys] = "dinner"
        datesofweek[keys] = getdayofweek(dates[keys])

    # Daniel put a dictionary here with all of the days as the key, ie _1, 0, 1, etc. for the days of the carousel with entrees, like seen above
    # also make sure that these are in order from negative to positive in the dictionary, like i did
    # And then the dictionary of (rounded) ratings here, like so

    for key in ratingsdict:
        if entreesdict[key] is not None:
            ratings_list = []

            for entree in entreesdict[key]:
                ratings_rows = db.execute(
                    "SELECT rating FROM ratings WHERE entree_id = (SELECT id FROM entrees WHERE name = (:entree));",
                    entree=entree,
                )

                if len(ratings_rows) == 0:
                    avg_rating = -1

                    ratings_list.append(avg_rating)

                else:
                    entree_ratings = [d["rating"] for d in ratings_rows]

                    if len(entree_ratings) != 0:
                        avg_rating = round(sum(entree_ratings) / len(entree_ratings))

                        ratings_list.append(avg_rating)

            ratingsdict[key] = ratings_list

    # And then a dictionary of one comment from each here, make sure the order is right for all of these
    for key in commentsdict:
        if entreesdict[key] is not None:
            comments_list = []

            for entree in entreesdict[key]:
                comments_rows = db.execute(
                    "SELECT comment FROM ratings WHERE entree_id = (SELECT id FROM entrees WHERE name = (:entree)) AND comment IS NOT NULL;",
                    entree=entree,
                )

                if len(comments_rows) == 0:
                    comment = "No comments."

                    comments_list.append(comment)

                else:
                    entree_comments = [d["comment"] for d in comments_rows]

                    filtered_comments = [
                        value for value in entree_comments if value is not ""
                    ]

                    if filtered_comments:
                        comments_list.append(random.choice(filtered_comments))
                    else:
                        comments_list.append("No comments.")

            commentsdict[key] = comments_list

    return render_template(
        "index.html",
        wait_time=wait_time,
        entreesdict=entreesdict,
        ratingsdict=ratingsdict,
        commentsdict=commentsdict,
        dates=dates,
        meal=meal,
        datesofweek=datesofweek,
    )


@app.route("/form", methods=["GET", "POST"])
def form():
    current_entrees = mealnumber(0)

    if request.method == "POST":
        errors = []

        if not request.form.get("time-input"):
            errors.append("Please provide the time when you were in line.")

        if not request.form.get("time-base"):
            errors.append("Please provide a time report.")

        if errors:
            return render_template(
                "form.html", current_entrees=current_entrees, errors=errors
            )

        specified_time = request.form.get("time-input")
        time_report = request.form.get("time-base")

        db.execute(
            "INSERT INTO wait_times (timestamp, wait_time) VALUES (:timestamp, :wait_time);",
            timestamp=specified_time,
            wait_time=time_report,
        )

        for entree in current_entrees:
            meal_rating = request.form.get(f"{entree}-rating")
            meal_comment = request.form.get(f"commentBox-{ entree }")

            if meal_rating:
                # Query database for entrees
                entree_ids = db.execute(
                    "SELECT id FROM entrees WHERE name = (:entree);", entree=entree
                )

                # Ensure entree exists
                if len(entree_ids) == 0:
                    db.execute(
                        "INSERT INTO entrees (name) VALUES (:entree);", entree=entree
                    )

                    entree_ids = db.execute(
                        "SELECT id FROM entrees WHERE name = (:entree);", entree=entree
                    )

                    db.execute(
                        "INSERT INTO ratings (entree_id, rating, comment) VALUES (:entree_id, :rating, :comment);",
                        entree_id=entree_ids[0]["id"],
                        rating=meal_rating,
                        comment=meal_comment,
                    )

                else:
                    db.execute(
                        "INSERT INTO ratings (entree_id, rating, comment) VALUES (:entree_id, :rating, :comment);",
                        entree_id=entree_ids[0]["id"],
                        rating=meal_rating,
                        comment=meal_comment,
                    )

        return redirect("/")

    else:
        return render_template("form.html", current_entrees=current_entrees)

@app.route("/aboutUs")
def aboutUs():
    return render_template("about.html")

# BergDash routes---------------------------------------------------------------------------------------------------------------------------------


@app.route("/dash")
def index1():
    return render_template("index1.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "POST":
        username = request.form.get("username").lower()
        password = request.form.get("password")

        if not username or not password:
            flash("Must provide username and password", "warning")
            return render_template("login.html")

        conn = get_users_db_connection()
        cur = conn.cursor()
        user = cur.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        conn.close()

        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Invalid username and/or password", "warning")
            return render_template("login.html")

        session["user_id"] = user["id"]
        session["username"] = username
        return redirect(url_for("post_registration"))

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username").lower()
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not username or not password or not confirmation:
            flash("Missing username or password", "warning")
            return render_template("register.html")

        if password != confirmation:
            flash("Passwords do not match", "warning")
            return render_template("register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters long", "warning")
            return render_template("register.html")

        conn = get_users_db_connection()
        cur = conn.cursor()
        user_check = cur.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()

        if user_check:
            flash("Username already exists", "warning")
            conn.close()
            return render_template("register.html")

        password_hash = generate_password_hash(password)
        cur.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash),
        )
        conn.commit()
        conn.close()

        return redirect(url_for("post_registration"))

    return render_template("register.html")


@app.route("/post_registration")
@login_required
def post_registration():
    username = session.get("username")
    return render_template("postreg.html", username=username)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index1"))


@app.route("/order", methods=["GET", "POST"])
@login_required
def order():
    if request.method == "POST":
        # Add your order form processing logic here
        return redirect(url_for("purchase_history"))
    return render_template("order.html")


@app.route("/faq")
def faq():
    return render_template("faq.html")


@app.route("/customer")
@login_required
def customer_dashboard():
    return render_template("customer.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.context_processor
def inject_username():
    return dict(username=session.get("username", "Guest"))


@app.route("/submit_order", methods=["POST"])
def submit_order():
    if "user_id" not in session:
        # Redirect to login if the user is not logged in
        return redirect(url_for("login"))

    # Extract data from form
    delivery_time = request.form.get("deliveryTime")
    # Convert delivery_time to the correct format
    delivery_datetime = datetime.datetime.strptime(delivery_time, "%Y-%m-%dT%H:%M").strftime("%Y-%m-%d %H:%M:%S")

    

    box_count = int(request.form.get("foodQuantity"))  # Convert to int for calculation
    box_contents = request.form.get("foodItems")
    dropoff_location = request.form.get("dropoffLocation")
    additional_comments = request.form.get("additionalComments")
    venmo_username = request.form.get("venmoUsername")

    # Calculate order price
    order_price = 3 if box_count > 0 else 0
    if box_count > 1:
        order_price += (box_count - 1) * 1.5

    # Establish connection to the SQLite database
    conn = get_users_db_connection()
    cur = conn.cursor()

    try:
        # Insert order into the database
        cur.execute(
            "INSERT INTO orders (customer_id, order_datetime, delivery_datetime, box_count, box_contents, dropoff_location, additional_comments, venmo_username, order_price) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                session["user_id"],
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                delivery_datetime,
                box_count,
                box_contents,
                dropoff_location,
                additional_comments,
                venmo_username,
                order_price,
            ),
        )
        conn.commit()

        # Retrieve the last order's ID
        order_id = cur.execute("SELECT last_insert_rowid()").fetchone()[0]
        session["last_order_id"] = order_id

    except Exception as e:
        print("SQLite error:", e)
        conn.rollback()
        return redirect(
            url_for("order_error")
        )  # Redirect to an error page or back to the order form
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("confirmation"))


@app.route("/confirmation")
def confirmation():
    if "last_order_id" not in session:
        # Handle the case where there is no recent order
        flash("No recent order found.", "warning")
        return redirect(url_for("index1"))

    # Retrieve the last order's details from the database
    conn = get_users_db_connection()
    cur = conn.cursor()

    try:
        order = cur.execute(
            "SELECT * FROM orders WHERE id = ?", (session["last_order_id"],)
        ).fetchone()

        if order is None:
            # Handle case where order details are not found
            flash("Order details not found.", "warning")
            return redirect(url_for("index1"))

        # Extract order details
        delivery_time = order["delivery_datetime"]
        box_contents = order["box_contents"]
        dropoff_location = order["dropoff_location"]
        additional_comments = order["additional_comments"]
        order_price = order["order_price"]

    except Exception as e:
        print("SQLite error:", e)
        flash("An error occurred while retrieving order details.", "warning")
        return redirect(url_for("index1"))
    finally:
        cur.close()
        conn.close()

    return render_template(
        "confirmation.html",
        delivery_time=delivery_time,
        box_contents=box_contents,
        dropoff_location=dropoff_location,
        additional_comments=additional_comments,
        order_price=order_price,
    )


@app.route("/deliver")
@login_required
def deliverer():
    conn = get_users_db_connection()
    cur = conn.cursor()

    try:
        orders = cur.execute(
            "SELECT * FROM orders WHERE deliverer_id IS NULL"
        ).fetchall()
    except Exception as e:
        print("SQLite error:", e)
        flash("An error occurred while retrieving orders.", "warning")
        return redirect(url_for("index1"))
    finally:
        cur.close()
        conn.close()

    return render_template("deliverer.html", orders=orders)


@app.route("/purchase_history")
@login_required
def purchase_history():
    user_id = session.get("user_id")
    if not user_id:
        flash("You need to be logged in to view this page.", "warning")
        return redirect(url_for("login"))

    conn = get_users_db_connection()
    cur = conn.cursor()

    try:
        # Fetch orders made by the current user
        orders = cur.execute(
            """
            SELECT o.*, u.username as deliverer_username
            FROM orders o
            LEFT JOIN users u ON o.deliverer_id = u.id
            WHERE customer_id = ?
            """,
            (user_id,),
        ).fetchall()
    except Exception as e:
        print("SQLite error:", e)
        flash("An error occurred while retrieving your order history.", "warning")
        return redirect(url_for("index1"))
    finally:
        cur.close()
        conn.close()

    return render_template("phistory.html", orders=orders)


@app.route("/claim_order/<int:order_id>", methods=["POST"])
@login_required
def claim_order(order_id):
    user_id = session.get("user_id")
    if not user_id:
        flash("You need to be logged in to claim an order.", "warning")
        return redirect(url_for("login"))

    conn = get_users_db_connection()
    cur = conn.cursor()
    try:
        # Update the order to set the deliverer_id to the current user's ID
        cur.execute(
            "UPDATE orders SET deliverer_id = ? WHERE id = ?", (user_id, order_id)
        )
        conn.commit()

        # Retrieve the details of the claimed order
        order = cur.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()

        # Store order details in the session for the claimed route
        session["claimed_order"] = dict(order)

    except Exception as e:
        print("SQLite error:", e)
        conn.rollback()
        flash("An error occurred while claiming the order.", "warning")
        return redirect(url_for("deliverer"))
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("claimed"))


@app.route("/claimed")
@login_required
def claimed():
    # Retrieve order details from the session
    order = session.get("claimed_order", None)

    # Clear the claimed order details from the session
    session.pop("claimed_order", None)

    if not order:
        flash("No order details found.", "warning")
        return redirect(url_for("deliverer"))

    return render_template("claimed.html", order=order)


@app.route("/order_error")
def order_error():
    # Render an error template or return an error message
    return "An error occurred with your order."


if __name__ == "__main__":
    app.run(debug=True)
