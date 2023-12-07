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
        return None
    

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
        return date.weekday()

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

    average_wait_times = wait_time_calc / 3 
    
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
            meal[keys] = "Breakfast"
        elif temp == 1:
            meal[keys] = "Lunch"
        else:
            meal[keys] = "Dinner"
        datesofweek[keys] = dates[keys]
        
        

    # Daniel put a dictionary here with all of the days as the key, ie _1, 0, 1, etc. for the days of the carousel with entrees, like seen above
    # also make sure that these are in order from negative to positive in the dictionary, like i did
    # And then the dictionary of (rounded) ratings here, like so
    for keys in ratingsdict:
        ratingsdict[keys] = [1, 2, 3, 4, 5, 3, 2, 4]
    # And then a dictionary of one comment from each here, make sure the order is right for all of these
    for keys in commentsdict:
        commentsdict[keys] = ["a", "a", "a", "A", "ewww", "a", "testing123"]

    return render_template("index.html", average_wait_times=average_wait_times, entreesdict = entreesdict, ratingsdict = ratingsdict, commentsdict = commentsdict, dates = dates, meal = meal, datesofweek = datesofweek)


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



