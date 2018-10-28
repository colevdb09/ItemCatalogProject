# Import sqlAlchemy ORM classes and methods
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from passlib.apps import custom_app_context as pwd_context

Base = declarative_base()

# Create a user object. 
class User(Base):
	
    __tablename__ = 'user'

    name = Column(String(32), index=True)
    id = Column(Integer, primary_key=True)
    email = Column(String(100), nullable=False)
    picture = Column(String(250))

# Create a band class with a lookup to the user
class Band(Base):

	__tablename__ = 'band'

	name = Column(String(50), nullable = False)
	photo = Column(String(80))
	id = Column(Integer, primary_key = True)
	user_id = Column(Integer,ForeignKey('user.id'))
	user = relationship(User)

	# Serialized for JSON endpoints
	@property
	def serialize(self):
		return{
			'name':self.name,
			'photo':self.photo,
			'id':self.id,
			'user':self.user_id
		}

# Create an album class with lookups to the user class and band class
class Album(Base):

	__tablename__ = 'album'

	name = Column(String(50), nullable = False)
	id = Column (Integer, primary_key = True)
	artwork = Column(String(80))
	fav_song = Column(String(32))
	year = Column(Integer)
	band_id = Column(Integer, ForeignKey('band.id'))
	band = relationship(Band)
	user_id = Column(Integer,ForeignKey('user.id'))
	user = relationship(User)

	# Serialized for JSON endpoints
	@property
	def serialize(self):
		return{
			'name':self.name,
			'artwork':self.artwork,
			'fav_song':self.fav_song,
			'year':self.year,
			'band':self.band_id,
			'user':self.user_id
		}


engine = create_engine('sqlite:///dirocktory.db')

Base.metadata.create_all(engine)