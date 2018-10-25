from flask import Flask, render_template, request, redirect,jsonify, url_for, flash
app = Flask(__name__)

from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from db_setup import Base, Band, Album, User


#Connect to Database and create database session
engine = create_engine('sqlite:///dirocktory.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)

from flask import session as login_session
import random, string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests


CLIENT_ID = json.loads(
		open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = 'Item Catalog Project'

@app.route('/gconnect', methods=['POST'])
def gconnect():
	if request.args.get('state') != login_session['state']:
		response = make_response(json.dumps('Invalid State Parameter'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response

	code = request.data

	try:
		oauth_flow = flow_from_clientsecrets('client_secrets.json',scope='')
		oauth_flow.redirect_uri = 'postmessage'
		credentials = oauth_flow.step2_exchange(code)
	except FlowExchangeError:
		response = make_response(json.dumps('Could not retrieve token from authorization code'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response

	access_token = credentials.access_token
	url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
	h = httplib2.Http()

	verified_token = json.loads(h.request(url,'GET')[1])

	if verified_token.get('error') is not None:
		response = make_response(json.dumps(verified_token.get('error')), 500)
		response.headers['Content-Type'] = 'application/json'
		return response

	gplus_id = credentials.id_token['sub']
	if verified_token['user_id'] != gplus_id:
		response = make_response(json.dumps('User ID of token does not match requestor ID'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response

	if verified_token['issued_to'] != CLIENT_ID:
		response = make_response(json.dumps('Issued to ID of the token does not match the application CLIENT ID'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response

	stored_credentials = login_session.get('credentials')
	stored_gplus_id = login_session.get('gplus_id')

	if stored_credentials is not None and stored_gplus_id == gplus_id:
		response = make_response(json.dumps('Current user is already logged in'), 201)
		response.headers['Content-Type'] = 'application/json'
		return response

	login_session['gplus_id'] = gplus_id
	login_session['access_token'] = credentials.access_token
	
	userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
	params = {'access_token': credentials.access_token, 'alt': 'json'}
	data = requests.get(userinfo_url, params=params)
	userinfo = data.json()

	login_session['username'] = userinfo['name']
	login_session['picture'] = userinfo['picture']
	login_session['email'] = userinfo['email']

	user_id = getUserId(login_session['email'])
	if user_id is None:
		user_id = createUser(login_session)
	login_session['user_id'] = user_id

	output = ''
	output += '<h1>Welcome, '
	output += login_session['username']
	output += '!</h1>'
	output += '<img src="'
	output += login_session['picture']
	output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
	flash("you are now logged in as %s" % login_session['username'])
	return output

@app.route('/gdisconnect')
def gdisconnect():
	token = login_session.get('access_token')
	if token is None:
		response = make_response(json.dumps('You are not currently logged in.'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response
	h = httplib2.Http()
	url_disc = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % token
	res = h.request(url_disc,'GET')[0]

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
		response = make_response(json.dumps('Failed to revoke token from OAuth Server'),400)
		response.headers['Content-Type'] = 'application/json'
		return response

def getUserId(email):
	try:
		session = DBSession()
		user = session.query(User).filter_by(email=email).one()
		return user.id
	except:
		return None

def createUser(login_session):
	session = DBSession()
	newUser = User(name=login_session['username'], email=login_session['email'], picture=login_session['picture'])
	session.add(newUser)
	session.commit()
	user = session.query(User).filter_by(email = login_session['email']).one()
	return user.id


@app.route('/login')
def showlogin():
	state = ''.join(random.choice(string.ascii_uppercase + string.digits) 
		for x in xrange(32))
	login_session['state'] = state

	return render_template('login.html', STATE = state)

@app.route('/')
@app.route('/bands')
def index():
	session = DBSession()
	bands = session.query(Band).all()
	if 'username' not in login_session:
		return render_template('publicbands.html',bands=bands)
	else:
		return render_template('bands.html',bands=bands,user_id=login_session['user_id'])

@app.route('/bands/new', methods = ['GET','POST'])
def newBand():
	if 'username' not in login_session:
		return redirect('/login')
	session = DBSession()
	if request.method == 'POST':
		name = request.form['name']
		photo = request.form['photo']
		newBand = Band(name=name, photo=photo, user_id=login_session['user_id'])
		session.add(newBand)
		session.commit()
		return redirect(url_for('index'))
	else:
		return render_template('newBand.html')

@app.route('/bands/<int:id>')
def showBand(id):
	session = DBSession()
	band = session.query(Band).filter_by(id=id).one()
	albums = session.query(Album).filter_by(band_id=id).all()
	if band.user_id == login_session.get('user_id'):
		return render_template('showBand.html',b=band,albums=albums)
	else:
		return render_template('publicshowBand.html',b=band,albums=albums)

@app.route('/bands/<int:band_id>/<int:alb_id>')
def showAlbum(band_id,alb_id):
	session = DBSession()
	band = session.query(Band).filter_by(id=band_id).one()
	album = session.query(Album).filter_by(id=alb_id).one()
	return render_template('showAlbum.html',b=band,a=album)

@app.route('/bands/<int:id>/edit', methods = ['GET','POST'])
def editBand(id):
	if 'username' not in login_session:
		return redirect('/login')
	session = DBSession()
	editBand = session.query(Band).filter_by(id=id).one()
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
		return render_template('editBand.html',band=editBand)

@app.route('/bands/<int:id>/delete', methods = ['GET','POST'])
def deleteBand(id):
	if 'username' not in login_session:
		return redirect('/login')
	session = DBSession()
	delBand = session.query(Band).filter_by(id=id).one()
	if request.method == 'POST':
		delAlbum = session.query(Album).filter_by(band_id=id).all()
		map(lambda d: session.delete(d), delAlbum)
		session.delete(delBand)
		session.commit()
		return redirect(url_for('index'))
	else:
		return render_template('deleteBand.html',band=delBand)

@app.route('/bands/<int:id>/new', methods = ['GET','POST'])
def newAlbum(id):
	if 'username' not in login_session:
		return redirect('/login')
	session = DBSession()
	if request.method == 'POST':
		name = request.form['name']
		artwork = request.form['artwork']
		fav_song = request.form['fav_song']
		year = request.form['year']		
		newAlbum = Album(name=name, artwork=artwork, fav_song=fav_song, year=year, band_id=id) 
		session.add(newAlbum)
		session.commit()
		return redirect(url_for('showBand',id=id))
	else:
		return render_template('newAlbum.html',band_id=id)

@app.route('/bands/<int:band_id>/<int:alb_id>/edit', methods = ['GET','POST'])
def editAlbum(band_id,alb_id):
	if 'username' not in login_session:
		return redirect('/login')
	session = DBSession()
	editAlbum = session.query(Album).filter_by(id=alb_id).one()
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
		return redirect(url_for('showAlbum',band_id=band_id,alb_id=alb_id))
	else:
		return render_template('editAlbum.html',a=editAlbum,band_id=band_id)

@app.route('/bands/<int:band_id>/<int:alb_id>/delete', methods = ['GET','POST'])
def deleteAlbum(band_id,alb_id):
	if 'username' not in login_session:
		return redirect('/login')
	session = DBSession()
	delAlbum = session.query(Album).filter_by(id=alb_id).one()
	if request.method == 'POST':
		session.delete(delAlbum)
		session.commit()
		return redirect(url_for('showBand',id=band_id))
	else:
		return render_template('deleteAlbum.html',band_id=band_id,a=delAlbum)

if __name__ == '__main__':
	app.secret_key = 'a_secret_key'
	app.debug = True
	app.run(host = '0.0.0.0', port = 8080)