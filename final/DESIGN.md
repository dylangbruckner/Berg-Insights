The design portion of the project will be composed of several sections:

BergInsights

Scraper:
	To get the entrees for any given day, we needed to scrape the Berg website. To do this, we used BeautifulSoup, as it was the easiest and most applicable scraper for our application. Unfortunately, the HTML of the Berg website wasn’t very straightforward; the entrees didn’t have any id or class distinctions. Thus, I had to cut out a portion of the HTML, bound by two categories, which were different for the breakfast and the lunch/dinner. From there, we could search for the tag, <a>, of all of the data remaining in the snipped section, which would give us all of the entrees for any given meal. There are also functions to make the HTML finding easier based on the date, as the berg website’s address for each meal is based on the date and a numeric key for the meal. 

SQL:

We have three tables:

Wait Times: stores the wait times reported by the form, and is accessed to produce an average time interval using the nearest entries into the form timewise

Entrees: Houses all of the entrees and an id number for each so they can be associated with ratings and comments

Ratings/comments: stores each rating and comments as it’s own entry and associates each with a certain entree id. 

Routes/HTML:

Layout: Uses a Navbar similar to the one in finance, set up using bootstrap. When on a mobile device or any device with a smaller viewscreen, the individual buttons at the top of the navbar collapse, making the UI more mobile friendly. However, the form is still easily accessible as it’s own button, to promote user accessibility if the webpage is accessed on a phone, which is more likely when reporting meal ratings and wait times while eating. 

Index: The homepage of BergInsights. Consists of a carousel of tables displaying the meals for today, as well as 3 meals back and 15 meals forward, as well as the ratings and a random comment for each. We used a carousel so that the user can quickly swipe back and forth meals on mobile devices. The carousel has six variables from the / route in app.py. Firstly, the entreesdict dictionary of lists, which has keys of the meals relative to the current meal for organization (-3, -2, -1, 0, 1, etc.) which is looped through to produce each of the carousel slides using Jinja. It also checks if the key is 0, in which case it makes that slide the active slide so that the first slide when the webpage opens is always the current meal. There is also a dictionary of lists of: the day, the date, and the meal, all to display to the user what information is being shown. Then, there is a ratingsdict and commentsdict, which follow a similar structure, but use an average rating of all of the ratings for any given meal, and a random comment for the meal from the archived comments. We also have standard cases for when there are no ratings or comments, as well as for Sunday breakfast when there is no hot food and thus no table entrees. Scroll through the table yourself to see them! Lastly, below the carousel, we have the projceted wait times, calculcted by averaging out nearby reported wait times. 

Form: A form which asks the user for their estimated wait time with four possible options, as well as a time of reporting function. Then, it uses a jijna for loop and the scraped entrees for the current meal to generate the correct number of rating boxes and meal names, and has a button next to each meal where you can add a comment. All of the meal ratings are optional, so the user doesn’t have to fill out every meal rating to submit. Then, the form inserts the data into the respective databases, and the table is updated if applicable. 

About and contact: two html pages which are fairly simple and just display text. 

CSS: Optimized, especially for the table and homepage, to be user friendly. 


Other:
There is a function that returns the meal date and meal number (breakfast, lunch, dinner) based on how many meals away from the current meal is put in to make our table easier




BergDash
