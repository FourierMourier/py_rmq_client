import os
import ssl
import pika  # type: ignore
import pika.exceptions  # type: ignore
from pydantic import BaseModel, Field, ValidationError, field_validator, ValidationInfo
from contextlib import contextmanager
from pika.exchange_type import ExchangeType  # type: ignore
import logging
from typing import Optional


__all__ = ['RabbitMQConfig', 'load_config', 'create_connection', 'RabbitMQConnectionManager']


class RabbitMQConfig(BaseModel):
    host: str = Field("localhost", alias="RABBITMQ_HOST")
    port: int = Field(5672, alias="RABBITMQ_PORT",
                      description="You might tend to use a different port if your connection is tls")
    username: str = Field("guest", alias="RABBITMQ_DEFAULT_USER")
    password: str = Field("guest", alias="RABBITMQ_DEFAULT_PASS")
    queue_name: str = Field("my_queue", alias="RABBITMQ_QUEUE_NAME")
    ssl_enabled: bool = Field(False, alias="RABBITMQ_SSL_ENABLED")
    ssl_ca_certs: Optional[str] = Field(None, alias="RABBITMQ_SSL_CA_CERTS")
    exchange_name: str = Field("", alias="EXCHANGE_NAME")
    # pydantic will convert this string to match the Enum type; the behaviour in this case is pretty similar to Literal
    exchange_type: ExchangeType = Field("direct", alias="EXCHANGE_TYPE")
    routing_key: str = Field(..., alias="RABBITMQ_ROUTING_KEY")

    @field_validator("routing_key", mode="before", check_fields=True)
    @classmethod
    def check_routing_key(cls, v, info: ValidationInfo):
        if v is None:
            return info.data.get("queue_name")
        return v


def load_config() -> RabbitMQConfig:
    try:
        return RabbitMQConfig(**os.environ)
    except ValidationError as e:
        print("Configuration Error:", e)
        raise


def create_connection(config: RabbitMQConfig):
    credentials = pika.PlainCredentials(config.username, config.password)
    connection_params = {
        "host": config.host,
        "port": config.port,
        "virtual_host": '/',
        "credentials": credentials,
    }

    if config.ssl_enabled:
        context = ssl.create_default_context(cafile=config.ssl_ca_certs)
        connection_params["ssl_options"] = pika.SSLOptions(context)

    return pika.BlockingConnection(pika.ConnectionParameters(**connection_params))


def ensure_exchange_exists(channel, exchange_name: str, exchange_type: str):
    try:
        # maybe declare to check if exchange exists
        channel.exchange_declare(exchange=exchange_name, exchange_type=exchange_type, passive=True)
        # regarding the passive:
        #   https://pika.readthedocs.io/en/stable/modules/channel.html#pika.channel.Channel.exchange_declare
        logging.info(f"Exchange '{exchange_name}' already exists.")
    except pika.exceptions.ChannelClosedByBroker:
        logging.info(f"Exchange '{exchange_name}' does not exist. Creating it...")
        channel.exchange_declare(exchange=exchange_name, exchange_type=exchange_type)


class RabbitMQConnectionManager:
    def __init__(self, config: RabbitMQConfig):
        self.config = config
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel: Optional[pika.adapters.blocking_connection.BlockingChannel] = None

    @staticmethod
    def prepare_channel(channel, config: RabbitMQConfig) -> None:
        # redeclare vars
        queue_name = config.queue_name
        routing_key = config.routing_key or queue_name
        # declare an exchange and bind the queue to it
        channel.queue_declare(queue=queue_name, durable=True)  # declare the queue with durability
        if len(config.exchange_name):
            channel.exchange_declare(exchange=config.exchange_name, exchange_type=config.exchange_type, durable=True)
            channel.queue_bind(exchange=config.exchange_name, queue=queue_name,
                               routing_key=routing_key)

    @contextmanager
    def managed_channel(self) -> pika.adapters.blocking_connection.BlockingChannel:
        try:
            if self.connection is None or self.connection.is_closed:
                self.connection = create_connection(self.config)

            if self.connection is not None:
                if self.channel is None or self.channel.is_closed:
                    self.channel = self.connection.channel()
                    self.prepare_channel(self.channel, self.config)

                if self.channel is not None:
                    yield self.channel
                else:
                    raise RuntimeError("Failed to create a channel")
            else:
                raise RuntimeError("Failed to establish a connection")

        except pika.exceptions.AMQPConnectionError as e:
            print(f"AMQP Connection Error: {e}")
            raise
        except Exception as e:
            print(f"Unexpected error: {e}")
            raise
        finally:
            if self.channel is not None and self.channel.is_open:
                self.channel.close()
            if self.connection is not None and self.connection.is_open:
                self.connection.close()
