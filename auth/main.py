import logging

import pika
import database as _database
import fastapi as _fastapi
import models as _models

connection = pika.BlockingConnection(pika.ConnectionParameters(host="localhost"))
channel = connection.channel()
channel.queue_declare(queue='email_notification')

def get_db():
    db = _database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


app = _fastapi.FastAPI()
logging.basicConfig(level=logging.INFO)
_models.Base.metadata.create_all(_models.engine)


