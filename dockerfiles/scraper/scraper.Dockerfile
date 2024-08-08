FROM python:3.11.3-alpine

WORKDIR /scraper
COPY . /scraper

# Upgrade pip and install dependencies
RUN pip install --upgrade pip
RUN pip install -r ./dockerfiles/scraper/requirements.txt

# Install Chromium and Chromedriver
RUN apk update && apk add --no-cache \
    chromium \
    chromium-chromedriver

ENV DOCKERIZED=true