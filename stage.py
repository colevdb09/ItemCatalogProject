from flask import Flask, render_template, request, redirect,jsonify, url_for, flash
app = Flask(__name__)

from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from db_setup import Base, Band, Album, User


#Connect to Database and create database session
engine = create_engine('sqlite:///dirocktory.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)

@app.route('/')
@app.route('/bands')
def index():
	session = DBSession()
	bands = session.query(Band).all()
	return render_template('bands.html',bands=bands)

@app.route('/bands/new', methods = ['GET','POST'])
def newBand():
	session = DBSession()
	if request.method == 'POST':
		name = request.form['name']
		photo = request.form['photo']
		newBand = Band(name=name, photo=photo)
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
	return render_template('showBand.html',b=band,albums=albums)

@app.route('/bands/<int:band_id>/<int:alb_id>')
def showAlbum(band_id,alb_id):
	session = DBSession()
	band = session.query(Band).filter_by(id=band_id).one()
	album = session.query(Album).filter_by(id=alb_id).one()
	return render_template('showAlbum.html',b=band,a=album)

@app.route('/bands/<int:id>/edit', methods = ['GET','POST'])
def editBand(id):
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
	session = DBSession()
	delAlbum = session.query(Album).filter_by(id=alb_id).one()
	if request.method == 'POST':
		session.delete(delAlbum)
		session.commit()
		return redirect(url_for('showBand',id=band_id))
	else:
		return render_template('deleteAlbum.html',band_id=band_id,a=delAlbum)

if __name__ == '__main__':
	app.debug = True
	app.run(host = '0.0.0.0', port = 8080)