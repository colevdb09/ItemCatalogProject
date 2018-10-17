import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from passlib.apps import custom_app_context as pwd_context

Base = declarative_base()

class User(Base):
	
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    username = Column(String(32), index=True)
    password_hash = Column(String(64))

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

class Band(Base):

	__tablename__ = 'band'

	name = Column(String(50), nullable = False)
	photo = Column(String(80))
	id = Column(Integer, primary_key = True)
	user_id = Column(Integer,ForeignKey('user.id'))
	user = relationship(User)

	@property
	def serialize(self):
		return{
			'name':self.name,
			'photo':self.photo,
			'id':self.id,
			'user':self.user_id
		}

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

	@property
	def serialize(self):
		return{
			'name':self.name,
			'artwork':self.artwork,
			'fav_song':self.fav_song,
			'year':self.year,
			'band':self.band,
			'user':self.user_id
		}


engine = create_engine('sqlite:///dirocktory.db')

Base.metadata.create_all(engine)