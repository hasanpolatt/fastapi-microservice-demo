import os

import sqlalchemy as _sql
import sqlalchemy.ext.declarative as _decl
import sqlalchemy.orm as _orm
from dotenv import load_dotenv

# Loading environment variables from the .env file.
load_dotenv()

# Getting PostgreSQL connection details from environment variables.
postgres_host = os.environ.get("POSTGRES_HOST")
postgres_db = os.environ.get("POSTGRES_DB")
postgres_user = os.environ.get("POSTGRES_USER")
postgres_password = os.environ.get("POSTGRES_PASSWORD")

# Creating the database URL for the PostgreSQL connection.
DATABASE_URL = (
    f"postgresql://{postgres_user}:{postgres_password}@{postgres_host}/{postgres_db}"
)

# Creating a SQLAlchemy engine to connect to the PostgreSQL database.
engine = _sql.create_engine(DATABASE_URL)
# Creating a session factory to handle database sessions with autocommit and autoflush disabled.
SessionLocal = _orm.sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Creating a base class for defining ORM models.
Base = _decl.declarative_base()
