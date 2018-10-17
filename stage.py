from flask import Flask, render_template, request, redirect,jsonify, url_for, flash
app = Flask(__name__)

from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Band, Album, User


#Connect to Database and create database session
engine = create_engine('sqlite:///dirocktory.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)

