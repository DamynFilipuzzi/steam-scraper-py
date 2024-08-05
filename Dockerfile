FROM python:3.11.3-alpine

WORKDIR /app
COPY . /app

# Upgrade pip and install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Install Chromium and Chromedriver
RUN apk update && apk add --no-cache \
    chromium \
    chromium-chromedriver

ENV DOCKERIZED=true