# This is the server code for the Item Catalog Project.
# It's purpose is to fulfill GET and POST requests from the client.
# The server connects to a database and performs CRUD operations to
# modify the database.
# OAuth through Google is used to create user accounts and restrict
# access to CRUD operations.

# Import Modules
import httplib2
import json
import requests
import random
import string
from flask import session as login_session
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
from sqlalchemy import create_engine, asc, func, desc
from sqlalchemy.orm import sessionmaker
from db_setup import Base, Band, Album, User
from flask import Flask, render_template, request, redirect, jsonify
from flask import url_for, flash, make_response

engine = create_engine('sqlite:///dirocktory.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)

app = Flask(__name__)

# Client Id and application name registered with Google for OAuth
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = 'Item Catalog Project'


# Google Authorization
# Use the one-time use code obtained from the client to request an
# authorization token.
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Check the STATE argument to protect against CSRF
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid State Parameter'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Create a Flow object from the client secrets obtained from Google.
    # Use the flow object to send the one-time-use code to Google and  create
    # a 'credentials' object which will have the access token as one of it's
    # properties.
    code = request.data
    try:
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(json.dumps(
            'Could not retrieve token from authorization code'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the token received from Google is valid by sending a request
    # to Google's verification API
    access_token = credentials.access_token
    url = (
        'https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
        % access_token)
    h = httplib2.Http()
    verified_token = json.loads(h.request(url, 'GET')[1])

    if verified_token.get('error') is not None:
        response = make_response(json.dumps(verified_token.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Confirm that the Google User ID on the verfied token
    # matches the Google User Id on the code-exchanged token.
    gplus_id = credentials.id_token['sub']
    if verified_token['user_id'] != gplus_id:
        response = make_response(json.dumps('User ID of token does not \
            match requestor ID'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Confirm that the application client id matches the verified token's.
    if verified_token['issued_to'] != CLIENT_ID:
        response = make_response(json.dumps('Issued to ID of the token \
            does not match the application CLIENT ID'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check if the user logging in is already logged into the session.
    # If not, request user information from Google API and store in
    # the login session object.
    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')

    if stored_credentials is not None and stored_gplus_id == gplus_id:
        response = make_response(json.dumps('Current user is already \
            logged in'), 201)
        response.headers['Content-Type'] = 'application/json'
        return response

    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    data = requests.get(userinfo_url, params=params)
    userinfo = data.json()

    login_session['gplus_id'] = gplus_id
    login_session['access_token'] = credentials.access_token
    login_session['username'] = userinfo['name']
    login_session['picture'] = userinfo['picture']
    login_session['email'] = userinfo['email']

    # Use the user's email as a unique identifier to search the
    # database for a user id.
    # If the user doesn't already exist in the database, create a new row.
    user_id = getUserId(login_session['email'])
    if user_id is None:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    # Output html to the login screen
    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;\
    -webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    return output


def getUserId(email):
    try:
        session = DBSession()
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


def createUser(login_session):
    session = DBSession()
    newUser = User(name=login_session['username'], email=login_session['email\
        '], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


# Log the user out of their session
@app.route('/gdisconnect')
def gdisconnect():
    # Check if an access token currently exists in the user's session
    token = login_session.get('access_token')
    if token is None:
        response = make_response(json.dumps('You are not currently \
            logged in.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Send a request to the Google API to revoke the session's access token.
    # If the request is successful, delete the user's information from the
    # session object.
    h = httplib2.Http()
    url_disc = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % token
    res = h.request(url_disc, 'GET')[0]

    if res['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        flash("You have successfully been logged out.")
        return redirect(url_for('index'))
    else:
        response = make_response(json.dumps('Failed to revoke token from \
            OAuth Server'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response


# Render login screen with a STATE variable as an argument.
# State is stored in the login session to protect against
# cross-site reference forgery.
@app.route('/login')
def showlogin():
    state = ''.join(random.choice(
            string.ascii_uppercase + string.digits) for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


# Route for main index page.
# Shows bands that exist in the database.
# For logged in users, shows the user's most popular album year
# with links to albums added by the user from that year.
@app.route('/')
@app.route('/bands')
def index():
    session = DBSession()
    bands = session.query(Band).all()
    if 'username' not in login_session:
        return render_template('publicbands.html', bands=bands)
    else:
        pop_year = session.query(
            Album.year, func.count(Album.id).label('num')).filter_by(
            user_id=login_session['user_id']).group_by(
            Album.year).order_by(desc('num')).first()
        if pop_year is None:
            head = "Add an album to see most popular year"
            my_albums = None
        else:
            head = "My most common album year is %s" % pop_year[0]
            my_albums = session.query(Album).filter_by(
                user_id=login_session['user_id'], year=pop_year[0]).all()
        return render_template('bands.html',
                               bands=bands, user_id=login_session['user_id'],
                               my_albums=my_albums, head=head)


# JSON endpoint describing all bands in the database.
@app.route('/bands/JSON')
def indexJSON():
    session = DBSession()
    bands = session.query(Band).all()
    return jsonify(Band=[b.serialize for b in bands])


# Add a new band to the database
@app.route('/bands/new', methods=['GET', 'POST'])
def newBand():
    # Restrict to logged-in users
    if 'username' not in login_session:
        return redirect('/login')
    session = DBSession()
    if request.method == 'POST':
        # Parse form data to create new row in the Band table.
        name = request.form['name']
        photo = request.form['photo']
        newBand = Band(name=name, photo=photo,
                       user_id=login_session['user_id'])
        session.add(newBand)
        session.commit()
        return redirect(url_for('index'))
    else:
        return render_template('newBand.html')


# Show band information. Render a different template for logged-in user
# that shows the option to add an album to the database.
@app.route('/bands/<int:id>')
def showBand(id):
    session = DBSession()
    band = session.query(Band).filter_by(id=id).one()
    creator = session.query(User).filter_by(id=band.user_id).one()
    albums = session.query(Album).filter_by(band_id=id).all()
    if 'username' in login_session:
        return render_template('showBand.html', b=band, albums=albums,
                               user_id=login_session['user_id'],
                               creator=creator)
    else:
        return render_template('publicshowBand.html\
            ', b=band, albums=albums, creator=creator)


# JSON endpoint describing algsbums from a particular band
@app.route('/bands/<int:id>/JSON')
def showBandJSON(id):
    session = DBSession()
    band = session.query(Band).filter_by(id=id).one()
    albums = session.query(Album).filter_by(band_id=id).all()
    return jsonify(Album=[a.serialize for a in albums])


# HTML endpoint describing album information
@app.route('/bands/<int:band_id>/<int:alb_id>')
def showAlbum(band_id, alb_id):
    session = DBSession()
    band = session.query(Band).filter_by(id=band_id).one()
    album = session.query(Album).filter_by(id=alb_id).one()
    creator = session.query(User).filter_by(id=album.user_id).one()
    if 'username' in login_session:
        return render_template('showAlbum.html', b=band, a=album,
                               creator=creator)
    else:
        return render_template('publicshowAlbum.html', b=band,
                               a=album, creator=creator)


# JSON endpoint describing album information
@app.route('/bands/<int:band_id>/<int:alb_id>/JSON')
def showAlbumJSON(band_id, alb_id):
    session = DBSession()
    band = session.query(Band).filter_by(id=band_id).one()
    album = session.query(Album).filter_by(id=alb_id).one()
    return jsonify(Album=album.serialize)


# Route for editing a band in the database.
# Restrict access to a logged-in user and the user who created the band.
@app.route('/bands/<int:id>/edit', methods=['GET', 'POST'])
def editBand(id):
    if 'username' not in login_session:
        return redirect('/login')
    session = DBSession()
    editBand = session.query(Band).filter_by(id=id).one()
    if login_session['user_id'] != editBand.user_id:
        response = make_response(json.dumps('User not authorized \
            to edit this band.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    if request.method == 'POST':
        name = request.form.get('name')
        photo = request.form.get('photo')
        if name:
            editBand.name = name
        if photo:
            editBand.photo = photo
        session.add(editBand)
        session.commit()
        return redirect(url_for('index'))
    else:
        return render_template('editBand.html', band=editBand)


# Route for deleting a band in the database.
# Restrict access to a logged-in user and the user who created the band.
@app.route('/bands/<int:id>/delete', methods=['GET', 'POST'])
def deleteBand(id):
    if 'username' not in login_session:
        return redirect('/login')
    session = DBSession()
    delBand = session.query(Band).filter_by(id=id).one()
    if login_session['user_id'] != delBand.user_id:
        response = make_response(json.dumps('User not authorized \
            to delete this band.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    if request.method == 'POST':
        delAlbum = session.query(Album).filter_by(band_id=id).all()
        map(lambda d: session.delete(d), delAlbum)
        session.delete(delBand)
        session.commit()
        return redirect(url_for('index'))
    else:
        return render_template('deleteBand.html', band=delBand)


# Route for creating a new album in a band.
# Restrict to logged-in users. Any user can create an album.
@app.route('/bands/<int:id>/new', methods=['GET', 'POST'])
def newAlbum(id):
    if 'username' not in login_session:
        return redirect('/login')
    session = DBSession()
    if request.method == 'POST':
        name = request.form['name']
        artwork = request.form['artwork']
        fav_song = request.form['fav_song']
        year = request.form['year']
        user = login_session['user_id']
        newAlbum = Album(name=name, artwork=artwork, fav_song=fav_song,
                         year=year, band_id=id, user_id=user)
        session.add(newAlbum)
        session.commit()
        return redirect(url_for('showBand', id=id))
    else:
        return render_template('newAlbum.html', band_id=id)


# Route for editing an album in the database.
# Restrict access to a logged-in user and the user who created the album.
@app.route('/bands/<int:band_id>/<int:alb_id>/edit', methods=['GET', 'POST'])
def editAlbum(band_id, alb_id):
    if 'username' not in login_session:
        return redirect('/login')
    session = DBSession()
    editAlbum = session.query(Album).filter_by(id=alb_id).one()
    if login_session['user_id'] != editAlbum.user_id:
        response = make_response(json.dumps('User not authorized to edit \
            this album.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    if request.method == 'POST':
        name = request.form.get('name')
        artwork = request.form.get('artwork')
        fav_song = request.form.get('fav_song')
        year = request.form.get('year')
        if name:
            editAlbum.name = name
        if artwork:
            editAlbum.artwork = artwork
        if fav_song:
            editAlbum.fav_song = fav_song
        if year:
            editAlbum.year = year
        session.add(editAlbum)
        session.commit()
        return redirect(url_for('showAlbum', band_id=band_id, alb_id=alb_id))
    else:
        return render_template('editAlbum.html', a=editAlbum, band_id=band_id)


# Route for deleting an album in the database.
# Restrict access to a logged-in user and the user who created the album.
@app.route('/bands/<int:band_id>/<int:alb_id>/delete', methods=['GET', 'POST'])
def deleteAlbum(band_id, alb_id):
    if 'username' not in login_session:
        return redirect('/login')
    session = DBSession()
    delAlbum = session.query(Album).filter_by(id=alb_id).one()
    if login_session['user_id'] != delAlbum.user_id:
        response = make_response(json.dumps('User not authorized to \
            delete this album.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    if request.method == 'POST':
        session.delete(delAlbum)
        session.commit()
        return redirect(url_for('showBand', id=band_id))
    else:
        return render_template('deleteAlbum.html', band_id=band_id, a=delAlbum)


# Run Flask Application
if __name__ == '__main__':
    app.secret_key = 'a_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8080)
