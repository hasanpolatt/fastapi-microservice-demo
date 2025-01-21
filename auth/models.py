from database import Base, engine
import database as _database
Base.metadata.create_all(engine)

class User(_database.Base):
    __tablename__ = "users"