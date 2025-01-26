import os
import time

import auth_models as _models
import database as _database
import email_validator as _email_validator
import fastapi as _fastapi
import fastapi.security as _security
import passlib.hash as _hash
import pika
import sqlalchemy.orm as _orm
from sqlalchemy import and_

import models.auth_schemas as _schemas

JWT_SECRET = os.getenv("JWT_SECRET")
RABBITMQ_URL = os.getenv("RABBITMQ_URL")
oauth2schema = _security.OAuth2PasswordBearer("/api/token")


def create_database():
    return _database.Base.metadata.create_all(bind=_database.engine)


def get_db():
    db = _database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_user_by_email(email: str, db: _orm.Session):
    return (
        db.query(_models.User)
        .filter(and_(_models.User.email == email, _models.User.is_verified == True))
        .first()
    )


async def create_user(user: _schemas.UserCreate, db: _orm.Session):
    try:
        valid = _email_validator.validate_email(user.email)
        name = user.name
        email = user.email
    except _email_validator.EmailNotValidError:
        raise _fastapi.HTTPException(
            status_code=404, detail="Please enter a valid email address."
        )

    user_obj = _models.User(
        name=name, email=email, hashed_password=_hash.bcrypt.hash(user.password)
    )
