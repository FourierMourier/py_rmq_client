### README.md

# Python RabbitMQ Publisher/Consumer client

A flexible RabbitMQ client for publishing and consuming messages with customizable flow, 
supporting both `publisher` and `consumer` modes; can be configured via CLI arguments and environment variables.
You might find it useful for experimenting with RabbitMQ configurations or, at least, simple testing.


[![Docker Hub](https://img.shields.io/docker/pulls/fouriermourier/py_rmq_client.svg)](https://hub.docker.com/r/fouriermourier/py_rmq_client)

---

## Table of Contents

- [Setup](#setup)
  - [Using pre-built images](#using-pre-built-images)
  - [Build from scratch](#build-from-scratch)
- [Usage](#usage)
  - [CLI Arguments](#cli-arguments)
  - [Environment Variables](#environment-variables)
  - [Running with Docker](#running-with-docker)
  - [Examples](#examples)
- [RabbitMQ Configuration](#rabbitmq-configuration)

---

## Setup

If you don't want to build the image from scratch, you can pull the pre-built docker images directly from the repository.

### Using pre-built images

1. Pull the Docker image:

   ```bash
   docker pull fouriermourier/py_rmq_client:latest
   ```

2. Start the RabbitMQ client:

   ```bash
   docker run --env-file .env fouriermourier/py_rmq_client:latest
   ```

### Build from scratch
#### docker
1. Build

```shell
docker build --no-cache -t local/py_rmq_client:latest .
```

2. Run the consumer

```shell
docker run --rm --env-file .env local/py_rmq_client:latest rmq --mode=consumer --delay=0.5 --log-level=warning --verbose=True 
```

3. Run the publisher:

```shell
docker run --rm --env-file .env local/py_rmq_client:latest rmq --mode=publisher --message="hello there" --delay=0.6 --log-level=warning --verbose=True
```


#### docker-compose

1. Build

```bash
docker-compose -f docker-compose-scratch.yaml build --no-cache
```

2. Run containers

```bash
docker-compose -f docker-compose-scratch.yaml up
```

---

## Usage

### CLI Arguments

When running the RabbitMQ client, you can specify options through CLI arguments to customize its behavior. 
Here's a summary of available CLI options:

| Argument      | Description                                     | Default    | Choices                                         |
|---------------|-------------------------------------------------|------------|-------------------------------------------------|
| `--mode`      | Client's behavior (publish or consume)          | `consumer` | `consumer`, `publisher`                         |
| `--message`   | Message to publish (required in publisher mode) | `None`     | -                                               |
| `--delay`     | Delay between operations in seconds             | `1.0`      | -                                               |
| `--count`     | Number of messages to publish (0 for infinite)  | `0`        | -                                               |
| `--log-level` | Set the log verbosity                           | `debug`    | `critical`, `error`, `warning`, `info`, `debug` |
| `--verbose`   | Enable detailed output                          | `True`     | `True`, `False`                                 |

> **Note**: If you're in `publisher` mode, the `--message` argument is required.

> **Note #2**: It's better to set `log-level` to "warning" or higher so that you won't see too many messages regarding connection info

### Environment Variables

Alternatively, you can configure RabbitMQ using environment variables. 
Here's the list of supported variables and their default values:

| Environment Variable    | Description                                          | Default                        |
|-------------------------|------------------------------------------------------|--------------------------------|
| `RABBITMQ_HOST`         | The RabbitMQ server hostname                         | `localhost`                    |
| `RABBITMQ_PORT`         | The port RabbitMQ is running on                      | `5672`                         |
| `RABBITMQ_DEFAULT_USER` | Username for connecting to RabbitMQ                  | `guest`                        |
| `RABBITMQ_DEFAULT_PASS` | Password for the user                                | `guest`                        |
| `RABBITMQ_QUEUE_NAME`   | Name of the queue to consume/publish messages to     | `my_queue`                     |
| `RABBITMQ_SSL_ENABLED`  | Whether to enable SSL for the connection             | `False`                        |
| `RABBITMQ_SSL_CA_CERTS` | Path to the SSL CA certificate                       | `None`                         |
| `EXCHANGE_NAME`         | RabbitMQ exchange name                               | `""`                           |
| `EXCHANGE_TYPE`         | Exchange type (e.g., direct, fanout, topic, headers) | `direct`                       |
| `RABBITMQ_ROUTING_KEY`  | Routing key for binding queue to exchange            | Value of `RABBITMQ_QUEUE_NAME` |

### Running with Docker

In the `docker-compose.yml`, you can customize the `entrypoint` to control how the client runs. 
Below are two examples to configure the `entrypoint`.

1. **Publisher** mode:

   ```yaml
   services:
     rmq:
       image: fouriermourier/py_rmq_client:latest
       ## if you need to build from scratch: 
       # build:
       #   context: ./
       #   dockerfile: Dockerfile
       env_file:
         - .env
       entrypoint:
         - rmq
         - --mode=publisher
         - --message="hello there"
         - --delay=0.6
         - --count=10
         - --log-level=warning
         - --verbose=True
   ```

2. **Consumer** mode:

   ```yaml
   services:
     rmq:
       image: fouriermourier/py_rmq_client:latest
       ## if you need to build from scratch:
       # build:
       #   context: ./
       #   dockerfile: Dockerfile
       env_file:
         - .env
       entrypoint:
         - rmq
         - --mode=consumer
         - --delay=0.3
         - --log-level=warning
         - --verbose=True
   ```

### Examples

#### Running the publisher

You can run the publisher mode with a custom message, delay, and count of messages to send:


```shell
docker-compose -f docker-compose.yaml run consumer --mode=publisher --message="hello world" --delay=1 --count=5 --log-level=warning
```

The client will publish "hello world" 5 times with a 1-second delay between each message.

#### Running the consumer

To run the consumer:

```bash
docker-compose -f docker-compose.yaml run consumer --mode=publisher --message="hello world" --delay=1 --count=5 --log-level=warning
```

The consumer will process messages with a 1.5-second delay between each one.

---

## RabbitMQ client configuration

By default, the client uses the values below:

- port: `5672`
- exchange name: `""`
- exchange type: `direct`
- host: `localhost`
- username: `guest`
- password: `guest`
- queue name: `my_queue`
- ssl enabled: `False`
- ssl CA certificates: `None`
- routing key: value of `RABBITMQ_QUEUE_NAME` if specified, otherwise - value of the `my_queue` parameter

Feel free to adjust `.env` file or `ConfigMap` in case of running in k8s to your specific credentials.

---
