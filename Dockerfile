FROM python:3.11.3-alpine
RUN pip install --upgrade pip
RUN pip install requests beautifulsoup4 python-dotenv selenium tqdm psycopg2-binary free-proxy
# RUN apt-get update && apt-get install -y wget unzip && wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && apt install -y ./google-chrome-stable_current_amd64.deb && rm google-chrome-stable_current_amd64.deb && apt-get clean

# WORKDIR /app
ADD /app .
ADD /env .
COPY .env .env
CMD [ "/app" ]