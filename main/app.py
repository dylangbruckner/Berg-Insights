from flask import Flask, flash, redirect, render_template, request, session

app = Flask(__name__)

#hi there
@app.route("/")
def index():
    return render_template("index.html")