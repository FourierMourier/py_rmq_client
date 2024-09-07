import argparse
import logging
from typing import Literal, get_args
from pydantic import BaseModel, Field, field_validator, ValidationInfo
from enum import Enum
from src.publish import publish_main
from src.consume import consume_main
from src.logging import SOEventLogger
from typing import Optional


MODE_LITERAL_TYPE = Literal['consumer', 'publisher']
MODE_CHOICES = get_args(MODE_LITERAL_TYPE)  # https://github.com/python/typing/issues/697#issuecomment-577145238


class LogLevelEnum(Enum):
    critical = "critical"
    fatal = "critical"
    error = "error"
    warning = "warning"
    warn = "warning"
    info = "info"
    debug = "debug"


class CliArgs(BaseModel):
    mode: MODE_LITERAL_TYPE = Field(default='consumer')
    message: Optional[str] = Field(default=None)
    delay: float = Field(default=1.0)
    count: int = Field(default=0)
    log_level: LogLevelEnum = Field("debug")
    verbose: bool = Field(True)

    @field_validator("message", mode="before", check_fields=True)
    @classmethod
    def validate_message(cls, v, info: ValidationInfo):
        client_mode: str = info.data.get("mode")
        if client_mode == 'publisher':
            assert v is not None, f"When client mode={client_mode} specifying `message` is required"
        return v


def setup_parser() -> argparse.ArgumentParser:
    log_level_choices = [level.name for level in LogLevelEnum]
    parser = argparse.ArgumentParser(description='RabbitMQ Publisher/Consumer CLI')
    parser.add_argument('--mode', default='consumer', choices=MODE_CHOICES, help='Client\'s behavior')
    parser.add_argument('--message', default=None, help='Message to publish (for publish mode)')
    parser.add_argument('--delay', type=float, default=1.0, help='Delay between operations in seconds')
    parser.add_argument('--count', type=int, default=0, help='Number of messages to publish (0 for infinite)')
    parser.add_argument('--log-level', type=str, default="debug", choices=log_level_choices)
    parser.add_argument('--verbose', type=bool, default=True)
    return parser


def main():
    parser = setup_parser()
    args = parser.parse_args()

    cli = CliArgs(**args.__dict__)

    logging_log_level = getattr(logging, cli.log_level.value.upper(), 30)
    logging.basicConfig(level=logging_log_level)

    event_logger = SOEventLogger.init_v1(cli.verbose)

    if cli.mode == 'consumer':
        consume_main(cli.delay, event_logger)
    elif cli.mode == 'publisher':
        if not cli.message:
            parser.error("--message is required for publish mode")
        publish_main(cli.message, cli.delay, cli.count, event_logger)
    else:
        raise ValueError(f"Unsupported mode provided: {cli.mode}")


if __name__ == "__main__":
    main()
