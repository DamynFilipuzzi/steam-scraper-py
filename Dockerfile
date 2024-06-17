FROM python:3.11.3-alpine
RUN pip install --upgrade pip
RUN pip install requests beautifulsoup4 python-dotenv selenium tqdm psycopg2-binary free-proxy

RUN apk update
RUN apk add chromium
RUN apk add chromium-chromedriver

# WORKDIR /app
ADD /app .
ADD /env .
COPY .env .env
CMD [ "/app" ]