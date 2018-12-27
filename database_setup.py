from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))


class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False, unique=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    items = relationship("Item", backref="catergory")

    @property
    def serialize(self):
        items = [item.serialize for item in self.items]
        return {
            'name': self.name,
            'id': self.id,
            'items': items,
        }


class Item(Base):
    __tablename__ = 'item'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False, unique=True)
    description = Column(String(250))
    created = Column(DateTime, server_default=func.now())
    category_name = Column(String(80), ForeignKey('category.name'))
    category = relationship(Category)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
        }


engine = create_engine('postgresql:///catalog.db')
Base.metadata.create_all(engine)
