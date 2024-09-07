import pika  # type: ignore
import time
from .common import load_config, RabbitMQConnectionManager
from .logging import BaseEventLogger, EventTypes


__all__ = ['publish_main']


def publish_message(message: str, channel, exchange: str, routing_key: str, event_logger: BaseEventLogger):
    channel.basic_publish(
        exchange=exchange,
        routing_key=routing_key,
        body=message.encode("utf-8"),  # make sure you're sending the correct bytes
        properties=pika.BasicProperties(
            delivery_mode=pika.DeliveryMode.Persistent,  # make message persistent = 2
        ))
    event_logger.log_event(EventTypes.publish, body=message, exchange=exchange)


def publish_main(message: str, delay: float, count: int, event_logger: BaseEventLogger):
    config = load_config()
    connection_manager = RabbitMQConnectionManager(config)
    published = 0
    print(f"Starting publisher with {delay}s delay between message processing")
    while count == 0 or published < count:
        with connection_manager.managed_channel() as channel:
            publish_message(message, channel, config.exchange_name, config.queue_name, event_logger)
            time.sleep(delay)
            published += 1
            if count > 0:
                event_logger.log_event(EventTypes.countable_publish_stats, published=published, count=count)
            else:
                event_logger.log_event(EventTypes.uncountable_publish_stats, published=published)
