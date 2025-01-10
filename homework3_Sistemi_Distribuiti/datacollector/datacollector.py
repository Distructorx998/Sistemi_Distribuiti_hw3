import time
import mysql.connector
import yfinance as yf
import logging
import json
from datetime import datetime
from circuit_breaker import CircuitBreaker
from confluent_kafka import Producer

# Configurazione del produttore Kafka
producer_config = {
    'bootstrap.servers': 'kafka:9092',  # Nome del servizio Kafka su Kubernetes
    'acks': 'all',
    'batch.size': 500,
    'max.in.flight.requests.per.connection': 1,
    'retries': 3
}

producer = Producer(producer_config)
topic1 = 'to-alert-system'

# Callback per confermare l'invio del messaggio Kafka
def update_completed(err, msg):
    if err:
        logging.error(f"Delivery failed: {err}")
    else:
        logging.info(f"Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")

# Circuit Breaker
circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=30)

def fetch_stock_price(ticker):
    stock = yf.Ticker(ticker)
    return stock.history(period="1d")['Close'].iloc[-1]

# Crea la tabella se non esiste
def create_table_if_not_exists(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stock_values (
            id INT AUTO_INCREMENT PRIMARY KEY,
            email VARCHAR(255) NOT NULL,
            ticker VARCHAR(10) NOT NULL,
            price DECIMAL(10, 2) NOT NULL,
            timestamp DATETIME NOT NULL
        )
    """)

def main():
    while True:
        try:
            # Connessione al database con il contesto
            with mysql.connector.connect(
                host="db",  # Nome del servizio DB su Kubernetes
                user="user",
                password="password",
                database="users"
            ) as conn:
                with conn.cursor() as cursor:
                    create_table_if_not_exists(cursor)

                    cursor.execute("SELECT email, ticker FROM users")
                    users = cursor.fetchall()
                    logging.info(f"Users fetched from database: {users}")
                    
                    timestamp = datetime.now().isoformat()
                    messaggio = 'fase di aggiornamento dei valori è stata completata'
                    message = {'timestamp': timestamp, 'messaggio': messaggio}
                    
                    for email, ticker in users:
                        try:
                            price = circuit_breaker.call(fetch_stock_price, ticker)
                            cursor.execute(
                                "INSERT INTO stock_values (email, ticker, price, timestamp) VALUES (%s, %s, %s, NOW())",
                                (email, ticker, price)
                            )
                            conn.commit()
                        except Exception as e:
                            logging.error(f"Error fetching data for {ticker}: {e}")
                    
                    # Produzione del messaggio con conferma
                    producer.produce(topic1, json.dumps(message), callback=update_completed)
                    logging.info(f"Message sent to Kafka topic '{topic1}': {message}")
                    producer.flush()

        except mysql.connector.Error as e:
            logging.error(f"Database error: {e}")
            time.sleep(10)  # Ritardo prima di tentare una nuova connessione
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
        time.sleep(60)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
