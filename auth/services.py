import os

import auth_models as _models
import database as _database
import email_validator as _email_validator
import fastapi as _fastapi
import fastapi.security as _security
import jwt
import passlib.hash as _hash
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


async def authenticate_user(email: str, password: str, db: _orm.Session):
    user = await get_user_by_email(email=email, db=db)

    if not user:
        return False

    if not user.is_verified:
        return "is_verified_false"

    if not user.verify_password(password):
        return False

    return user


async def get_current_user(
    db: _orm.Session = _fastapi.Depends(get_db),
    token: str = _fastapi.Depends(oauth2schema),
):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user = db.query(_models.User).get(payload["id"])
    except:
        raise _fastapi.HTTPException(
            status_code=401, detail="Invalid Email or Password"
        )
    return _schemas.User.model_validate(user)
