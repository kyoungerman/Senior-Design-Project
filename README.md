My role in this project was of the primary back-end developer. I was reponisble for setting up the Django framework, designing and implementing the databse schema,
hosting the database on AWS, web scraping, pulling data from the ebay API, and implementing product identification. I did not work on our custom facebook API or the
front end.

This project uses the following technologies:

Python, Django, PostgreSQL, Amazon Web Services, Beautiful Soup, Chart.js and the eBay API. 


Here's how it worked:

     First, a user would enter a term in the search bar of the webpage.

     The app would then search eBay, Craigslist, and Facebook Marketplace for the entered search term.

     Then, it would aggregate all relevant product listings and display a results page.

     The application would also track 129 different PC parts and their daily prices,
     and store price history in a remote database

     Finally, the user could see the historical prices of any PC part in a line chart format.


Files of interest:

     WebApp-master/mysite/main/views.py holds a majority of the code that we wrote. It's quite big.
  
     WebApp-master/mysite/main/models.py is where the database tables are defined.

Team: Me, Austin Tarango, Jordan Ruckle, and Jacob Silva.
