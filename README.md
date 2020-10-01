My role in this project was of the primary back-end developer. I was reponisble for setting up the Django framework, designing and implementing the databse schema,
hosting the database on AWS, web scraping, pulling data from the ebay API, and implementing product identification. I did not work on our custom facebook API or the
front end.

This project uses the following technologies:
Python, Django, PostgreSQL, Amazon Web Services, Beautiful Soup, Chart.js and the eBay API. 

First, a user would enter a term in the search bar of the webpage.
The app would then search eBay, Craigslist, and Facebook Marketplace for the entered search term.
Then, it would aggregate all relevant product listings into a results page.
The application would also track about 100 PC parts and their prices, and store them in a remote database hosted on AWS.
Finally, the user could see the historical prices of the PC parts in a line chart format.


files of interest: WebApp-master/mysite/main/views.py hold a majority of the code that we wrote.
                   WebApp-master/mysite/main/models.py is where the database tables are defined.

Team: Me, Austin Tarango, Jordan Ruckle, and Jacob Silva.
