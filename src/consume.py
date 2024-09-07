import time
import functools
from .common import RabbitMQConnectionManager, load_config, RabbitMQConfig
from .logging import EventTypes, BaseEventLogger


def callback(ch, method, properties, body, processing_delay: float, event_logger: BaseEventLogger):
    event_logger.log_event(EventTypes.consume, body=body, exchange=f"'{method.exchange}'",
                           routing_key=method.routing_key)
    time.sleep(processing_delay)
    ch.basic_ack(delivery_tag=method.delivery_tag)


def consume_messages(processing_delay: float, config: RabbitMQConfig, event_logger: BaseEventLogger):
    connection_manager = RabbitMQConnectionManager(config)

    with connection_manager.managed_channel() as channel:
        # configure basic QoS and the callback for message processing
        channel.basic_qos(prefetch_count=1)  # fetch only one message at a time for processing
        on_message_callback = functools.partial(callback, processing_delay=processing_delay, event_logger=event_logger)
        channel.basic_consume(queue=config.queue_name, on_message_callback=on_message_callback)

        print(' [*] Waiting for messages. To exit press CTRL+C')
        channel.start_consuming()  # start consuming messages


def consume_main(delay: float, event_logger: BaseEventLogger):
    config = load_config()
    print(f"Starting consumer with {delay}s delay between message processing")
    consume_messages(delay, config, event_logger=event_logger)
