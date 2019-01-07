SPINZ
===================
Item Catalog Project
#######################
Spinz is a music catalog app where users can post album artwork for their favorite bands.
Users are able to add bands as well as albums to the bands they’ve added as well to the bands that other users have added. User sign in is available by OAuth through Google+.

Languages & Development
#######################
The server side code of this application is written in Python using the Flask framework. 

The front-end of this app uses a combination of HTML and CSS. Some Javascript and jQuery were used to connect to the Google+ API for OAuth and to make requests from the client to the server.

The SQLLite database is setup and accessed using the SQLAlchemy ORM.

Contents
#######################
*stage.py*
* Holds the server code.
* Routes established for creating, editing, deleting, and reading database content.
* OAuth handled through a login page route, a route to connect to the Google+ API to get an authorization token, and a route to log out by ordering Google+ to revoke the authorization token.
* JSON Endpoints are available for reading the Band and Album tables.

*dp_setup.py*
* Creates the database.
* Database consists of three tables: User, Band, Album.
* The Band table has a foreign key that looks up to the User table.
* The Album table has foreign keys that look up to the User table and to the Band table.

*templates*
* HTML files are stored in the templates directory
* Templates use HTML escaping to receive data from the server.

*static*
* Holds the CSS file for styling the app’s HTML pages.
* Stores the app logo and font files.

*credentials.json*
* Stores the Client Id and Client Secrets for the app.

Installation
#######################
To install and run, you need access to a linux server and a browser. 
* First run the code on the db_setup.py file on the linux server to create the database (appropriately named dirocktory.db).
* Next, run the stage.py file to instantiate the app. In it’s current configuration, the app will run on the localhost domain on port 8080. If you are using a virtual machine to host the server code, you can access the app with the browser by going to localhost:8080.
* Open the browser, and login to the application by going to localhost:8080/login. Token credentials and user info are stored in flask’s session object.
* If you would like to proceed  without logging into your Google+ Account, you can go straight to localhost:8080/bands to access content. 
* You will have full read access to the site without needing to login, however, if you want to create, modify, or delete any data you will need a user account (created when you login through OAuth).

Libraries Used
#######################
* httplib2
* json
* requests
* random
* string
* flask
* oauth2client.client
* sqlalchemy


 