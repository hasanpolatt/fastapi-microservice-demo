import logging

import auth_models as _models
import database as _database
import fastapi as _fastapi
import pika
import services as _services
import sqlalchemy.orm as _orm

from models.auth_schemas import (GenerateOtp, GenerateUserToken, User,
                                 UserBase, UserCreate, VerifyOtp)

connection = pika.BlockingConnection(pika.ConnectionParameters(host="localhost"))
channel = connection.channel()
channel.queue_declare(queue="email_notification")


def get_db():
    db = _database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


app = _fastapi.FastAPI()
logging.basicConfig(level=logging.INFO)
_models.Base.metadata.create_all(_models.engine)


@app.post("/api/users", tags=["User Auth"])
async def create_user(
    user: UserCreate, db: _orm.Session = _fastapi.Depends(_services.get_db)
):
    db_user = await _services.get_user_by_email(email=user.email, db=db)

    if db_user:
        logging.info("User with that email already exists")
        raise _fastapi.HTTPException(
            status_code=409, detail="User with that email already exists"
        )

    user = await _services.create_user(user)

    return _fastapi.HTTPException(
        status_code=202,
        detail="User Registered, please verify email to activate account",
    )


@app.post("/api/token", tags=["User Auth"])
async def generate_token(
    user_data: GenerateUserToken, db: _orm.Session = _fastapi.Depends(_services.get_db)
):

    user = await _services.authenticate_user(
        email=user_data.username, password=user_data.password, db=db
    )

    if user == "is_verified_false":
        logging.info("Email verification is pending. Please verify email to proceed.")
        raise _fastapi.HTTPException(
            status_code=403,
            detail="Email verification is pending. Please verify email to proceed.",
        )

    if not user:
        logging.info("Invalid Credentials")
        raise _fastapi.HTTPException(status_code=401, detail="Invalid Credentials")

    logging.info("JWT Token Created")
    return await _services.create_token(user=user)


@app.get("/check_api")
async def check_api():
    return {"status": "Connected to API successfully"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)
