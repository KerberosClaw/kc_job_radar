FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gspread google-auth google-api-python-client google-auth-oauthlib

COPY src/ src/
COPY config.sample.yaml .

# config.yaml, credentials, data/ are volume-mounted at runtime
