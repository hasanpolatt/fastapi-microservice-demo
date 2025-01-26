import database as _database
from database import Base, engine

Base.metadata.create_all(engine)


class User(_database.Base):
    __tablename__ = "users"
