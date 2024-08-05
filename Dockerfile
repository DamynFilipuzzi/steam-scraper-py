FROM python:3.11.3-alpine

WORKDIR /app
COPY . /app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

RUN apk update
RUN apk add chromium
RUN apk add chromium-chromedriver