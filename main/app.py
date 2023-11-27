from flask import Flask, flash, redirect, render_template, request, session
import requests

# Scraper
# URL = "https://realpython.github.io/fake-jobs/"
page = requests.get(URL)


app = Flask(__name__)

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

#hi there
@app.route("/")
def index():
    return render_template("index.html")