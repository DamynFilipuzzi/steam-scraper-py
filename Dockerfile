FROM python:3.9
RUN pip install requests beautifulsoup4 python-dotenv selenium tqdm psycopg2
WORKDIR /app
ADD /app .
ADD /env .
COPY .env .env