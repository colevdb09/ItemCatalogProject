from flask import Flask, render_template, request, redirect,jsonify, url_for, flash
app = Flask(__name__)

from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from db_setup import Base, Band, Album, User


#Connect to Database and create database session
engine = create_engine('sqlite:///dirocktory.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)

session = DBSession()

newBand = Band(name="AC/DC",photo="https://espngrantland.files.wordpress.com/2014/12/ac-dc-1970.jpg?w=1200")

session.add(newBand)

session.commit()