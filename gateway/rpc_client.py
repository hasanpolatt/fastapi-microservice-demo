import json
import os
import uuid

import pika
from dotenv import load_dotenv

load_dotenv()
RABBITMQ_URL = os.environ.get(
    "RABBITMQ_URL"
)  # Get RabbitMQ URL from environment variables


class OcrRpcClient(object):
    """
    A client for performing Remote Procedure Calls (RPC) to the OCR microservice using RabbitMQ.
    """

    def __init__(self):
        """
        Initialize the RPC client by creating a connection to RabbitMQ,
        setting up a channel, and declaring a callback queue for responses.
        """
        # Create a connection to RabbitMQ
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=RABBITMQ_URL)
        )

        # Open a channel for communication
        self.channel = self.connection.channel()

        # Declare a callback queue to receive responses
        result = self.channel.queue_declare(queue="", exclusive=True)
        self.callback_queue = result.method.queue

        # Set up a consumer to listen on the callback queue
        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True,
        )

    def on_response(self, props, body):
        """
        Callback function that handles responses from the OCR service.
        Checks if the response matches the correlation ID of the current request.
        """
        # Match the correlation ID to ensure this response corresponds to the current request
        if self.corr_id == props.correlation_id:
            self.response = body

    def call(self, message):
        """
        Sends a request to the OCR microservice and waits for a response.

        :param message: The request data to send to the OCR microservice (JSON serializable).
        :return: The response from the OCR microservice as a Python dictionary.
        """
        # Initialize the response variable and generate a unique correlation ID for this request
        self.response = None
        self.corr_id = str(uuid.uuid4())
        # Publish the message to the 'ocr_service' queue
        self.channel.basic_publish(
            exchange="",
            routing_key="ocr_service",
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
            ),
            body=json.dumps(message),
        )

        # Wait for a response to be received in the callback queue
        while self.response is None:
            self.connection.process_data_events()
        # Decode the received response from JSON to a Python dictionary
        response_json = json.loads(self.response)
        return response_json
