from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Base, User, Category, Item

engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

# dummy user
User1 = User(name="jhon", email="email@example.com", picture='image')
session.add(User1)
session.commit()

# Soccer category
soccer = Category(user_id=1, name="Soccer")

session.add(soccer)
session.commit()

# Items for Soccer category

Item1 = Item(user_id=1, name="ball",
             description="ball description", category=soccer)

session.add(Item1)
session.commit()

Item2 = Item(user_id=1, name="shoes",
             description="shoes description", category=soccer)

session.add(Item2)
session.commit()

# Snowboarding category
snowboarding = Category(user_id=1, name="Snowboarding")

session.add(snowboarding)
session.commit()

# Items for Snowboarding category
Item1 = Item(user_id=1, name="snowboard",
             description="snowboard description", category=snowboarding)

session.add(Item1)
session.commit()


Item2 = Item(user_id=1, name="goggles",
             description="goggles description", category=snowboarding)

session.add(Item2)
session.commit()

print("done adding data")
