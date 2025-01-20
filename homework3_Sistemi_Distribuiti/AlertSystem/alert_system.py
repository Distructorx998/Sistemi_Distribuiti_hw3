import time
import mysql.connector
import logging
import json
from datetime import datetime
from confluent_kafka import Producer, Consumer, KafkaException
from prometheus_client import start_http_server, Gauge, Counter

# Configurazione del consumer Kafka
consumer_config = {
    'bootstrap.servers': 'kafka:9092',
    'group.id': 'group1',
    'auto.offset.reset': 'earliest',
    'enable.auto.commit': True,
    'auto.commit.interval.ms': 5000
}

# Configurazione del producer Kafka
producer_config = {
    'bootstrap.servers': 'kafka:9092'
}

# Configurazione database MySQL
db_config = {
    'host': 'db',
    'user': 'user',
    'password': 'password',
    'database': 'users'
}

# Prometheus metrics
response_time_gauge = Gauge('response_time_seconds', 'Time taken for DB operations', ['service', 'node'])
messages_produced = Counter('messages_produced_total', 'Total messages produced to Kafka', ['service', 'node'])
messages_received = Counter('messages_received_total', 'Total messages received from Kafka', ['service', 'node'])
db_update_time_gauge = Gauge('db_update_time_seconds', 'Time taken to update the database', ['service', 'node'])

# Etichette statiche
SERVICE_NAME = "alert-system"
NODE_NAME = "node1"

# Funzione per produrre messaggi Kafka
def produce_sync(producer, topic, value):
    try:
        producer.produce(topic, value)
        messages_produced.labels(service=SERVICE_NAME, node=NODE_NAME).inc()  # Incrementa il contatore
        logging.info(f"Produced message to {topic}: {value}")
    except Exception as e:
        logging.error(f"Failed to produce message: {e}")

# Funzione per verificare la disponibilità di Kafka e del topic
def wait_for_kafka(topic):
    logging.info("Waiting for Kafka to be ready...")
    while True:
        try:
            metadata = producer.list_topics(timeout=10)
            if topic in metadata.topics:
                logging.info(f"Kafka is ready. Topic '{topic}' is available.")
                break
            else:
                logging.warning(f"Topic '{topic}' not found. Retrying...")
        except KafkaException as e:
            logging.error(f"Kafka not ready: {e}")
        time.sleep(5)

# Ciclo principale
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Avvio server Prometheus per le metriche
    start_http_server(8002)  # Porta per esportare le metriche

    # Istanziazione di consumer e producer
    consumer = Consumer(consumer_config)
    producer = Producer(producer_config)

    # Verifica Kafka e topic prima di iniziare
    wait_for_kafka('to-alert-system')

    # Sottoscrizione al topic dopo che Kafka è pronto
    consumer.subscribe(['to-alert-system'])

    while True:
        try:
            start_time = time.time()

            # Poll per ricevere nuovi messaggi
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                logging.error(f"Consumer error: {msg.error()}")
                continue

            # Parsing del messaggio ricevuto
            messages_received.labels(service=SERVICE_NAME, node=NODE_NAME).inc()  # Incrementa il contatore
            data = json.loads(msg.value().decode('utf-8'))
            timestamp = data['timestamp']
            messaggio = data['messaggio']
            logging.info(f"Received message: {messaggio}")

            # Connessione al database
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor(dictionary=True)

            # Query per ottenere utenti e prezzi
            query_start = time.time()
            query = """
                SELECT 
                    u.email, 
                    u.ticker, 
                    u.low_value, 
                    u.high_value, 
                    s.price
                FROM 
                    users u
                JOIN 
                    stock_values s
                ON 
                    u.ticker = s.ticker
                WHERE 
                    s.timestamp = (SELECT MAX(timestamp) FROM stock_values WHERE ticker = u.ticker)
            """
            cursor.execute(query)
            users = cursor.fetchall()
            db_update_time_gauge.labels(service=SERVICE_NAME, node=NODE_NAME).set(time.time() - query_start)

            # Controlla ogni profilo
            for user in users:
                email = user['email']
                low_value = user['low_value']
                high_value = user['high_value']
                price = user['price']
                ticker = user['ticker']
                condition = None

                if low_value is not None and price < low_value:
                    condition = f"below_low ({price} < {low_value})"
                    cursor.execute("UPDATE users SET low_value = %s WHERE email = %s", (price, email))
                    conn.commit()
                elif high_value is not None and price > high_value:
                    condition = f"above_high ({price} > {high_value})"
                    cursor.execute("UPDATE users SET high_value = %s WHERE email = %s", (price, email))
                    conn.commit()

                if condition:
                    notification = {
                        'email': email,
                        'ticker': ticker,
                        'condition': condition
                    }
                    produce_sync(producer, 'to-notifier', json.dumps(notification))

            # Log del tempo totale per il ciclo
            response_time_gauge.labels(service=SERVICE_NAME, node=NODE_NAME).set(time.time() - start_time)

            cursor.close()
            conn.close()
            producer.flush()

        except mysql.connector.Error as db_err:
            logging.error(f"Database error: {db_err}")
        except Exception as e:
            logging.error(f"General error: {e}")
        finally:
            try:
                if cursor:
                    cursor.close()
                if conn:
                    conn.close()
            except:
                pass

    consumer.close()
