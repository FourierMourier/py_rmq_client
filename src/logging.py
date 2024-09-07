import datetime
from abc import ABC, abstractmethod
from enum import Enum
import logging
from typing import Dict, Optional


__all__ = ['EventTypes', 'Event', 'BaseEventLogger', 'EventLogger', 'SOEventLogger']


MAYBE_LOGGER_T = Optional[logging.Logger]


class EventTypes(Enum):
    consume = "consume"
    process = "process"
    publish = "publish"
    countable_publish_stats = "countable_publish_stats"
    uncountable_publish_stats = "uncountable_publish_stats"


class MessageFormatter:
    def __init__(self, template: str):
        self.template = template

    def format_message(self, **kwargs):
        return self.template.format(**kwargs)


class SafeDict(dict):
    """Class for safe strings formatting just ignoring missing keys avoiding runtime errors"""
    def __missing__(self, key):
        return '{' + key + '}'


class Event:
    def __init__(self, name: EventTypes, template, verbose):
        self.name = name
        self.template = template
        self.verbose = verbose

    def format(self, **kwargs) -> Optional[str]:
        return self.template.format_map(SafeDict(kwargs))

    def match(self, name: EventTypes) -> bool:
        return self.name == name


def init_events(verbose: bool) -> Dict[EventTypes, Event]:
    """
    init events templates based on the verbose value
    """
    templates = {
        EventTypes.consume: {
            True: "Received: {body}, Exchange: {exchange}, Routing Key: {routing_key}",
            False: "Received: {body}"
        },
        EventTypes.process: {
            True: "Processed message {body}, took {processing_delay} seconds",
            False: "Processed message {body}"
        },
        EventTypes.publish: {
            True: "Published message: {body}, to Exchange: {exchange}",
            False: "Published message: {body}"
        },
        EventTypes.countable_publish_stats: {
            True: "Published {published}/{count} messages",
            False: "Published {published} messages"
        },
        EventTypes.uncountable_publish_stats: {
            True: "Published {published} messages",
            False: "Published {published} messages"
        }
    }

    return {
        event_type: Event(name=event_type, template=templates[event_type][verbose], verbose=verbose)
        for event_type in templates
    }


class BaseEventLogger(ABC):
    def __init__(self, events: Dict[EventTypes, Event]):
        self.events = events

    @abstractmethod
    def log_event(self, event_name: EventTypes, **kwargs):
        pass


class EventLogger(BaseEventLogger):
    def __init__(self, events: Dict[EventTypes, Event], logger: MAYBE_LOGGER_T = None):
        super().__init__(events)
        self.logger = logger or logging.getLogger("events_logger")

    def log_event(self, event_name: EventTypes, **kwargs):
        """
        log events based on event_name and passed data through kwargs.
        """
        event = self.events.get(event_name)
        if event:
            message = event.format(**kwargs)
            if message:
                self.logger.info(message)

    @classmethod
    def init_v1(cls, verbose: bool = False, logger: MAYBE_LOGGER_T = None):
        return cls(init_events(verbose), logger)


class SOEventLogger(BaseEventLogger):
    """
    Simply logs to the stdout
    """
    def __init__(self, events: Dict[EventTypes, Event], include_dt=True):
        super().__init__(events)
        self.include_dt = include_dt

    def prepare_message(self, message: str):
        if self.include_dt:
            message = f"{datetime.datetime.utcnow()}: {message}"

        return f"[x] {message}"

    def log_event(self, event_name: EventTypes, **kwargs):
        """
        log events by printing them to stdout.
        """
        event = self.events.get(event_name)
        if event:
            message = event.format(**kwargs)
            if message:
                print(self.prepare_message(message))

    @classmethod
    def init_v1(cls, verbose: bool = False):
        return cls(init_events(verbose))
