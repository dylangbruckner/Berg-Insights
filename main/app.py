import os
import sys

from flask import Flask, flash, redirect, render_template, request, session
import requests
import datetime
from datetime import datetime as dtime, time, timedelta
import pytz
from bs4 import BeautifulSoup

from cs50 import SQL

app = Flask(__name__)

os.environ['FLASK_DEBUG'] = '1'

db = SQL("sqlite:///huds.db")

today = datetime.date.today()
current_time = time(dtime.now().time().hour, dtime.now().time().minute)
fdate = f"{today.month}-{today.day}-{today.year}";

print(current_time)

# Scraper
BREAKFAST = f"https://www.foodpro.huds.harvard.edu/foodpro/menu_items.asp?date={fdate}&type=30&meal=0"
LUNCH = f"https://www.foodpro.huds.harvard.edu/foodpro/menu_items.asp?date={fdate}&type=30&meal=1"
DINNER = f"https://www.foodpro.huds.harvard.edu/foodpro/menu_items.asp?date={fdate}&type=30&meal=2"

# gets html
breakfast = requests.get(BREAKFAST)
lunch = requests.get(LUNCH)
dinner = requests.get(DINNER)

# runs html through parser
brehtml = BeautifulSoup(breakfast.content, "html.parser")
lunhtml = BeautifulSoup(lunch.content, "html.parser")
dinhtml = BeautifulSoup(dinner.content, "html.parser")

# finds specific section of the code
start_tag = dinhtml.find("tr", text_="Entrees")
end_tag = dinhtml.find("tr", text_="Veg,Vegan")

# this should (theoretically) add all of the entrees to a list called entrees
if start_tag and end_tag:
    content_between = ''
    current_tag = start_tag.find_next()
    while current_tag and current_tag != end_tag:
        content_between += str(current_tag)
        current_tag = current_tag.find_next()

    soup_between = BeautifulSoup(content_between, 'html.parser')
    entrees = soup_between.find_all("a").get_text()


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
def index():

    current_wait_time = db.execute("SELECT wait_time FROM wait_times ORDER BY ABS(wait_time - (:current_time)) LIMIT 1;", current_time=time)

    return render_template("index.html")

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



