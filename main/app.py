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

    average_wait_time = round(wait_time_calc / len(current_wait_times))

    wait_time_txt = ["No wait", "Less than 5 minutes", "5-10 minutes", "More than 10 minutes"]

    return render_template("index.html", wait_time=wait_time_txt[average_wait_time])


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
        meal_comment = request.form.get("meal-comment")

        current_entrees = mealnumber(0)

        for entree in current_entrees:
            
            # Query database for username
            rows = db.execute("SELECT * FROM entrees WHERE name = (:entree)", entree=entree)

            # Ensure username does not exist
            if len(rows) != 0:
                db.execute("INSERT INTO entrees (name) VALUES (:entree);", entree=entree)

                entree_id = db.execute("SELECT id FROM entrees WHERE name = (:entree);", entree=entree )

                db.execute("INSERT INTO ratings (entree_id, rating, comment) VALUES (:entree_id, :rating, :comment);", 
                           entree_id=entree_id[0]['id'], rating=meal_rating, comment=meal_comment)

            else:
                db.execute("INSERT INTO ratings (entree_id, rating, comment) VALUES (:entree_id, :rating, :comment);", 
                           entree_id=rows[0]['id'], rating=meal_rating, comment=meal_comment)

        return redirect("/")

    else:  

        current_entrees = mealnumber(0)

        return render_template("form.html", current_entrees=current_entrees)



