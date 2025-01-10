# Dockerfile per AlertSystem
FROM python:3.12.7

WORKDIR /app

# Installazione delle dipendenze
RUN pip install confluent_kafka
RUN pip install mysql-connector-python  

# Copia tutti i file dalla directory corrente alla directory di lavoro del container
COPY . .

CMD ["python", "alert_system.py"]