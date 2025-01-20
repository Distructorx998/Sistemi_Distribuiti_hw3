FROM python:3.12.7

WORKDIR /app

# Installazione delle dipendenze
RUN pip install confluent_kafka prometheus_client
RUN apt-get update && apt-get install -y \
    ssmtp \
    && rm -rf /var/lib/apt/lists/*

# Copia tutti i file dalla directory corrente alla directory di lavoro del container
COPY . .

CMD ["python", "alert_notification_system.py"]
