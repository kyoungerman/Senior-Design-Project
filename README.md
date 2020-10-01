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
     

Things to improve:
       
    The parsing of the product listing titles is done with over 200 lines of "if" statements. 
    We did this because it was easy and we were on a deadline. Knowing what I know now, I would instead 
    use regular expressions. This would make it more maintainable, extendable, and concise.
    
    The file structure is not great. Most of the code is in one file. I would break up the functions defined 
    in views.py and give them a seperate file. This would serve to increase readability and maintainability.
    
    The UI is very basic. The focus of this project wasn't to create a nice looking website. However, a 
    nicer UI would go a long way.
    
    The security is non-existent. One can easily run an SQL injection attack on the database. 
    There's no DDoS protection, etc.
    
    Finally, I would add a system to automatically add PC parts as they are searched, if they don't 
    already exist in the database. This is no small task, and it was outside the scope of our project.
    But in a real-wolrd scenario, there are 1000's of PC parts with new ones being released all the time,
    making a system such as this incredibly useful.

Team: Me, Austin Tarango, Jordan Ruckle, and Jacob Silva.
