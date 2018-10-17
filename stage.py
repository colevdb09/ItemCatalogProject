from flask import Flask, render_template, request, redirect,jsonify, url_for, flash
app = Flask(__name__)

from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Band, Album, User


#Connect to Database and create database session
engine = create_engine('sqlite:///dirocktory.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)

@app.route('/')
@app.route('/bands')
def bands():

@app.route('/bands/new', methods = ['GET','POST'])
def newband():

@app.route('/bands/<int:id>')

@app.route('/bands/<int:id>/edit', methods = ['GET','POST'])
def editband():

@app.route('/bands/<int:id>/delete', methods = ['GET','DELETE'])
def delband():

@app.route('/bands/<int:id>/new', methods = ['GET','POST'])
def newalbum():

@app.route('/bands/<int:id>/<int:alb_id>/edit', methods = ['GET','POST'])
def editalbum():

@app.route('/bands/<int:id>/<int:alb_id>/delete', methods = ['GET','DELETE'])
def deletealbum():
