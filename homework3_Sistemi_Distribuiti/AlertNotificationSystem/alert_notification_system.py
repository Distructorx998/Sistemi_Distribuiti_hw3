import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
from confluent_kafka import Consumer, KafkaException, KafkaError
import time
import logging
import os
from prometheus_client import start_http_server, Gauge, Counter

# Configurazione dei log
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configurazione Prometheus
REQUEST_COUNT = Counter(
    'alert_notification_requests_total',
    'Numero totale di richieste ricevute',
    ['service', 'node']
)
ERROR_COUNT = Counter(
    'alert_notification_errors_total',
    'Numero totale di errori durante la gestione delle richieste',
    ['service', 'node']
)
RESPONSE_TIME = Gauge(
    'alert_notification_response_time_seconds',
    'Tempo di risposta medio in secondi',
    ['service', 'node']
)

# Recupero informazioni di servizio e nodo
SERVICE_NAME = 'alert-notification-system'
NODE_NAME = os.getenv('NODE_NAME', 'unknown-node')

# Avvio server Prometheus per le metriche
start_http_server(8001)  # Porta 8000 esposta per le metriche

# Configurazione del consumer Kafka
consumer_config = {
    'bootstrap.servers': 'kafka:9092',
    'group.id': 'email-notification-group',
    'auto.offset.reset': 'earliest'
}

# Configurazione SMTP per inviare email
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_USERNAME = 'distructorx@gmail.com'
SMTP_PASSWORD = 'tlkaetutxjeahlyu'

# Nome del topic da verificare e sottoscrivere
topic = 'to-notifier'

# Funzione per verificare la disponibilità di Kafka e del topic

    # Funzione per verificare la disponibilità di Kafka e del topic con retry incrementale
def wait_for_kafka(bootstrap_servers, topic, initial_timeout=60, retry_interval=60):
        start_time = time.time()
        while True:
            try:
                consumer = Consumer({'bootstrap.servers': bootstrap_servers, 'group.id': 'health-check'})
                metadata = consumer.list_topics(timeout=5.0)
                if topic in metadata.topics:
                    logging.info(f"Kafka è pronto e il topic '{topic}' esiste.")
                    consumer.close()
                    return True
                else:
                    logging.warning(f"Topic '{topic}' non trovato. Riprovo tra {retry_interval} secondi...")
            except KafkaException as e:
                logging.error(f"Errore durante la verifica di Kafka: {e}")
            
            time.sleep(retry_interval)
            retry_interval = 60  # Incrementa il tempo di retry a 60 secondi dopo il primo tentativo
# Funzione per inviare email
def send_email(to_email, subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USERNAME
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SMTP_USERNAME, to_email, msg.as_string())

        logging.info(f"Email inviata con successo a {to_email}")
    except Exception as e:
        logging.error(f"Errore durante l'invio dell'email a {to_email}: {e}")
        ERROR_COUNT.labels(service=SERVICE_NAME, node=NODE_NAME).inc()  # Incrementa errori in caso di fallimento

# Verifica Kafka
logging.info("Verificando la disponibilità di Kafka...")
wait_for_kafka(consumer_config['bootstrap.servers'], topic)

# Creazione del consumer Kafka
consumer = Consumer(consumer_config)
logging.info(f"Sottoscrizione al topic '{topic}'...")
consumer.subscribe([topic])

# Ciclo principale per consumare messaggi
logging.info("Inizio del ciclo principale per consumare i messaggi...")
while True:
    start_time = time.time()  # Tempo di inizio per il monitoraggio della durata
    msg = consumer.poll(1.0)
    if msg is None:
        continue
    if msg.error():
        logging.error(f"Errore del consumer: {msg.error()}")
        ERROR_COUNT.labels(service=SERVICE_NAME, node=NODE_NAME).inc()  # Incrementa errori
        continue

    try:
        data = json.loads(msg.value().decode('utf-8'))
        logging.info(f"Messaggio ricevuto: {data}")

        email = data.get('email')
        ticker = data.get('ticker')
        condition = data.get('condition')

        if not email or not ticker or not condition:
            logging.warning("Messaggio non valido, mancano campi obbligatori")
            continue

        # Aggiorna contatore delle richieste
        REQUEST_COUNT.labels(service=SERVICE_NAME, node=NODE_NAME).inc()

        # Creazione dei contenuti dell'email
        subject = f"Ticker Alert: {ticker}"
        body = f"La condizione di superamento soglia per il ticker '{ticker}' è stata soddisfatta:\n\n{condition}"

        # Invio dell'email
        send_email(email, subject, body)

        # Calcolo del tempo di risposta
        elapsed_time = time.time() - start_time
        RESPONSE_TIME.labels(service=SERVICE_NAME, node=NODE_NAME).set(elapsed_time)

    except Exception as e:
        logging.error(f"Errore durante l'elaborazione del messaggio: {e}")
        ERROR_COUNT.labels(service=SERVICE_NAME, node=NODE_NAME).inc()  # Incrementa errori in caso di eccezioni

# Chiudi il consumer quando il processo termina
consumer.close()
logging.info("Consumer chiuso.")
