import os
import sys

from flask import Flask, flash, redirect, render_template, request, session
import requests
import datetime
from datetime import datetime as dtime, time, timedelta
from bs4 import BeautifulSoup

from cs50 import SQL

app = Flask(__name__)

os.environ['FLASK_DEBUG'] = '1'

db = SQL("sqlite:///huds.db")

# Get current date and time
today = datetime.date.today()
current_time = time(dtime.now().time().hour, dtime.now().time().minute)


# takes the html of any lunch/dinner page and returns the entrees
def lundinentree(samplehtml):
    # finds specific section of the code
    start_tag = samplehtml.find(lambda tag: tag.name == 'tr' and 'Entrees' in tag.get_text())
    end_tag = samplehtml.find(lambda tag: tag.name == 'tr' and 'Veg,Vegan' in tag.get_text())

    # this should (theoretically) add all of the entrees to a list called entrees
    if start_tag and end_tag:
        content_set = set()
        current_tag = start_tag.find_next()
    
        while current_tag and current_tag != end_tag:
            content_set.add(str(current_tag))
            current_tag = current_tag.find_next()

        content_between = ''.join(content_set)

        soup_between = BeautifulSoup(content_between, 'html.parser')
        entrees_tags = soup_between.find_all("a")

        # Extract text from each <a> tag and store in the entrees list
        unique_entrees = set(tag.get_text(strip=True) for tag in entrees_tags)
    
        # Convert the set to a list if needed
        entrees = list(unique_entrees)

        return entrees
    else:
        return("no entrees found")
    

# takes the breakfast page of any day and returns the entrees, if applicable
def breakentree(samplehtml):
    # finds specific section of the code
    start_tag = samplehtml.find(lambda tag: tag.name == 'tr' and 'Breakfast Meats' in tag.get_text())
    end_tag = samplehtml.find(lambda tag: tag.name == 'tr' and 'Breakfast Bakery' in tag.get_text())

    # this should (theoretically) add all of the entrees to a list called entrees
    if start_tag and end_tag:
        content_set = set()
        current_tag = start_tag.find_next()
    
        while current_tag and current_tag != end_tag:
            content_set.add(str(current_tag))
            current_tag = current_tag.find_next()

        content_between = ''.join(content_set)

        soup_between = BeautifulSoup(content_between, 'html.parser')
        entrees_tags = soup_between.find_all("a")

        # Extract text from each <a> tag and store in the entrees list
        unique_entrees = set(tag.get_text(strip=True) for tag in entrees_tags)
    
        # Convert the set to a list if needed
        entrees = list(unique_entrees)

        return entrees
    else:
        return(None)

# returns the entrees for a meal number
def mealnumber(mealnum):
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
    mealdate = cmealdate + timedelta((mealnum-mealnum%3)/3)
    meal = mealnum%3 + cmealnum
    if (cmealnum + mealnum%3 < 0):
        mealdate = mealdate - timedelta(1)
        if meal == -1:
            meal = 2
        else:
            meal = 1
    elif (cmealnum + mealnum%3 > 2):
        mealdate = mealdate + timedelta(1)
        if meal == 3:
            meal = 0
        else:
            meal = 1
    
    # formats the date, and gets the url of that date's html
    fdate = f"{mealdate.month}-{mealdate.day}-{mealdate.year}"
    MYHTML = f"https://www.foodpro.huds.harvard.edu/foodpro/menu_items.asp?date={fdate}&type=30&meal={meal}"

    if meal == 0:
        return breakentree(BeautifulSoup(requests.get(MYHTML).content, "html.parser"))
    else:
        return lundinentree(BeautifulSoup(requests.get(MYHTML).content, "html.parser"))


# ----------BEGIN ROUTES--------------------------------------------------------------------------------------------------------------------


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
def index():

    current_wait_times = db.execute("SELECT wait_time FROM wait_times ORDER BY ABS(wait_time - (:current_time)) LIMIT 3;", current_time=current_time)

    wait_time_calc = 0

    for row in current_wait_times:
        wait_time_calc += int(row['wait_time'])

    average_wait_times = wait_time_calc / 3 
    day2 = []
    day1 = ["chicken", "tacos", "beets"]
    day0 = ["chicken", "bananas"]
    day_1 = ["chicken", "duck", "alligator", "bannanas"]
    entreesdict = {-1: day_1, 0: day0, 1: day1, 2: day2}
    # Daniel put a dictionary here with all of the days as the key, ie _1, 0, 1, etc. for the days of the carousel with entrees, like seen above
    # also make sure that these are in order from negative to positive in the dictionary, like i did
    # And then the dictionary of (rounded) ratings here, like so
    rday2 = []
    rday1 = [1, 7.2, 4.1]
    rday0 = [3, 10]
    rday_1 = [1, 10, 10, 10]
    ratingsdict = {-1: rday_1, 0: rday0, 1: rday1, 2: rday2}
    # And then a dictionary of one comment from each here, make sure the order is right for all of these
    cday2 = []
    cday1 = ["eww", "yumyum", "a"]
    cday0 = ["eww", "b"]
    cday_1 = ["sedflwg", "d", "a", "b"]
    commentssdict = {-1: cday_1, 0: cday0, 1: cday1, 2: cday2}

    return render_template("index.html", average_wait_times=average_wait_times, entreesdict = entreesdict, ratingsdict = ratingsdict, commentssdict = commentssdict)


@app.route("/form", methods=["GET", "POST"])
def form():

    if request.method == "POST":

        errors = []

        if not request.form.get("time-input"):
            errors.append("Please provide the time when you were in line.")

        if not request.form.get("time-base"):
            errors.append("Please provide a time report.")

        if not request.form.get("rating-base"):
            errors.append("Please provide a meal rating.")
        
        if errors:
            return render_template("form.html", errors=errors)
        
        specified_time = request.form.get("time-input")
        time_report = request.form.get("time-base")
        meal_rating = request.form.get("rating-base")

        db.execute(
            "INSERT INTO wait_times (timestamp, wait_time) VALUES (:specified_time, :time_report) ;",
            specified_time = specified_time,
            time_report = time_report,
        )

        return redirect("/")

    else:  
        return render_template("form.html")



