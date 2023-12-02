import os
import sys

from flask import Flask, flash, redirect, render_template, request, session
import requests

from cs50 import SQL

app = Flask(__name__)

os.environ['FLASK_DEBUG'] = '1'

db = SQL("sqlite:///huds.db")


# Scraper
# URL = "https://realpython.github.io/fake-jobs/"
# page = requests.get(URL)


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
def index():
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

