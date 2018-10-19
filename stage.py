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
@app.route('/bands/<int:id>/edit', methods = ['GET','POST'])
def editBand(id):
	session = DBSession()
	editBand = session.query(Band).filter_by(id=id).one()
	if request.method == 'POST':
		name = request.form['name']
		photo = request.form['photo']
		editBand.name = name
		editBand.photo = photo
		session.add(editBand)
		session.commit()
		return redirect(url_for('index'))
	else:
		return render_template('editBand.html',band=editBand)

@app.route('/bands/<int:id>/delete', methods = ['GET','POST'])
def deleteBand(id):
	######### CURRENTLY DOESN'T DELETE ALBUMS FROM THE DATABASE #########
	session = DBSession()
	delBand = session.query(Band).filter_by(id=id).one()
	if request.method == 'POST':
		session.delete(delBand)
		session.commit()
		return redirect(url_for('index'))
	else:
		return render_template('deleteBand.html',band=delBand)

@app.route('/bands/<int:id>/new', methods = ['GET','POST'])
def newAlbum(id):
	pass

@app.route('/bands/<int:id>/<int:alb_id>/edit', methods = ['GET','POST'])
def editAlbum():
	pass

@app.route('/bands/<int:id>/<int:alb_id>/delete', methods = ['GET','DELETE'])
def deleteAlbum():
	pass

if __name__ == '__main__':
	app.debug = True
	app.run(host = '0.0.0.0', port = 8080)