import time
import mysql.connector
import logging
import json
from datetime import datetime
from confluent_kafka import Producer, Consumer, KafkaException

# Configurazione del consumer Kafka
consumer_config = {
    'bootstrap.servers': 'kafka:9092',  # Usare il nome del servizio Kubernetes
    'group.id': 'group1',
    'auto.offset.reset': 'earliest',
    'enable.auto.commit': True,
    'auto.commit.interval.ms': 5000
}

# Configurazione del producer Kafka
producer_config = {
    'bootstrap.servers': 'kafka:9092'
}

# Istanziazione di consumer e producer
consumer = Consumer(consumer_config)
producer = Producer(producer_config)

# Sottoscrizione ai topic
topic1 = 'to-alert-system'
topic2 = 'to-notifier'

# Configurazione database MySQL
db_config = {
    'host': 'db',  # Nome del servizio Kubernetes per il DB
    'user': 'user',
    'password': 'password',
    'database': 'users'
}

# Funzione per produrre messaggi Kafka
def produce_sync(producer, topic, value):
    try:
        producer.produce(topic, value)
        logging.info(f"Produced message to {topic}: {value}")
        messages_produced.inc()  # Incrementa il contatore Prometheus
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
    # Verifica Kafka e topic prima di iniziare
    wait_for_kafka(topic1)
    
    # Sottoscrizione al topic dopo che Kafka è pronto
    consumer.subscribe([topic1])

    while True:
        try:
            # Poll per ricevere nuovi messaggi
            msg = consumer.poll(1.0)
            if msg is None:
                continue  # Nessun messaggio ricevuto
            if msg.error():
                logging.error(f"Consumer error: {msg.error()}")
                continue

            # Parsing del messaggio ricevuto
            data = json.loads(msg.value().decode('utf-8'))
            timestamp = data['timestamp']
            messaggio = data['messaggio']
            logging.info(f"Received message: {messaggio}")

            # Connessione al database
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor(dictionary=True)

            # Query per ottenere utenti e prezzi
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

            # Log degli utenti trovati
            logging.info(f"Fetched users with stock values: {users}")

            # Controlla ogni profilo
            for user in users:
                email = user['email']
                low_value = user['low_value']
                high_value = user['high_value']
                price = user['price']
                ticker = user['ticker']
                condition = None

                # Verifica le condizioni di superamento soglia e aggiorna il database
                if low_value is not None and price < low_value:
                    condition = f"below_low ({price} < {low_value})"
                    logging.info(f"Updating low_value for email: {email}, new low_value: {price}")
                    cursor.execute("UPDATE users SET low_value = %s WHERE email = %s", (price, email))
                    conn.commit()  # Commit dopo l'aggiornamento
                elif high_value is not None and price > high_value:
                    condition = f"above_high ({price} > {high_value})"
                    logging.info(f"Updating high_value for email: {email}, new high_value: {price}")
                    cursor.execute("UPDATE users SET high_value = %s WHERE email = %s", (price, email))
                    conn.commit()  # Commit dopo l'aggiornamento

                if condition:
                    # Costruisci il messaggio per il topic `to-notifier`
                    notification = {
                        'email': email,
                        'ticker': ticker,
                        'condition': condition
                    }
                    produce_sync(producer, topic2, json.dumps(notification))

            # Chiudi il cursore e la connessione
            cursor.close()
            conn.close()

            # Flusha i messaggi accumulati nel producer
            producer.flush()

        except mysql.connector.Error as db_err:
            logging.error(f"Database error: {db_err}")
        except Exception as e:
            logging.error(f"General error: {e}")
        finally:
            # Garantire che la connessione venga chiusa in caso di errore
            try:
                if cursor:
                    cursor.close()
                if conn:
                    conn.close()
            except:
                pass

    consumer.close()
