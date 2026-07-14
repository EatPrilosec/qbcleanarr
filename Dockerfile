FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY cleaner.py .

ENV CONFIG_PATH=/config/config.ini
ENV RUN_INTERVAL_MINUTES=5

# Use unbuffered output so logs appear immediately
ENV PYTHONUNBUFFERED=1

CMD ["python", "cleaner.py"]
