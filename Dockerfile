FROM python:3.12.5-alpine

WORKDIR /workspace

COPY requirements/requirements.txt /workspace/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY src/ /workspace/src
COPY rmq_client.py /workspace/rmq_client.py

COPY rmq /usr/local/bin/rmq
RUN dos2unix /usr/local/bin/rmq && chmod +x /usr/local/bin/rmq

# disable python's output buffering
ENV PYTHONUNBUFFERED=1

ENV PYTHONPATH="/workspace:${PYTHONPATH}"
