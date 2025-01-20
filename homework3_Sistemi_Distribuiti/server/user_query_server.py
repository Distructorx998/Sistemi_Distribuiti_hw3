from concurrent import futures
import grpc
import user_pb2
import user_pb2_grpc
import mysql.connector
import logging

class UserQueryService(user_pb2_grpc.UserQueryServiceServicer):
    def __init__(self):
        self.conn = mysql.connector.connect(
            host="db",  # Nome del servizio DB su Kubernetes
            user="user",
            password="password",
            database="users"
        )
        logging.basicConfig(level=logging.INFO)

    def GetAllData(self, request, context):
        cursor = self.conn.cursor()
        try:
            cursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED") 
            
            # Recupera i nomi delle tabelle dal database
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()  # Recupera i nomi delle tabelle

            # Prepara una lista per i dati
            data = []

            # Cicla attraverso ogni tabella trovata
            for table in tables:
                table_name = table[0]  # Ogni riga è una tupla, il nome della tabella è il primo elemento
                cursor.execute(f"SELECT * FROM {table_name}")
                rows = cursor.fetchall()

                # Aggiungi il nome della tabella e i suoi dati
                data.append(f"Table: {table_name}")
                for row in rows:
                    data.append(str(row))

            # Ritorna i dati recuperati come risposta
            return user_pb2.AllDataResponse(data=data)
        except mysql.connector.Error as db_err:
            logging.error(f"Database error: {db_err}")
            return user_pb2.AllDataResponse(data=["An error occurred while retrieving data."])
        finally:
            cursor.close()

    def GetLastStockValue(self, request, context):
        normalized_email = normalize_email(request.email)
        cursor = self.conn.cursor()
        try:
            cursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED") 
            cursor.execute("SELECT price FROM stock_values WHERE email = %s ORDER BY timestamp DESC LIMIT 1", (normalized_email,))
            result = cursor.fetchone()
            if result:
                return user_pb2.StockValueResponse(message="Last stock value retrieved successfully", value=result[0])
            else:
                return user_pb2.StockValueResponse(message="No stock value found for the given email", value=0.0)
        except mysql.connector.Error as db_err:
            logging.error(f"Database error: {db_err}")
            return user_pb2.StockValueResponse(message="An error occurred while retrieving the last stock value.", value=0.0)
        finally:
            cursor.close()

    def GetAverageStockValue(self, request, context):
        normalized_email = normalize_email(request.email)
        cursor = self.conn.cursor()
        try:
            cursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED") 
            cursor.execute("SELECT ticker FROM users WHERE email = %s", (normalized_email,))
            user_ticker = cursor.fetchone()
            
            if user_ticker:
                cursor.execute("SELECT price FROM stock_values WHERE email = %s AND ticker = %s ORDER BY timestamp DESC LIMIT %s", 
                            (normalized_email, user_ticker[0], request.count))
                results = cursor.fetchall()
                if results:
                    average_value = sum([r[0] for r in results]) / len(results)
                    return user_pb2.StockValueResponse(message="Average stock value calculated successfully", value=average_value)
                else:
                    return user_pb2.StockValueResponse(message="No stock values found for the given email and ticker", value=0.0)
            else:
                return user_pb2.StockValueResponse(message="No ticker found for the given email", value=0.0)
        except mysql.connector.Error as db_err:
            logging.error(f"Database error: {db_err}")
            return user_pb2.StockValueResponse(message="An error occurred while calculating the average stock value.", value=0.0)
        finally:
            cursor.close()

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    user_pb2_grpc.add_UserQueryServiceServicer_to_server(UserQueryService(), server)
    server.add_insecure_port('[::]:50053')
    server.start()
    server.wait_for_termination()
    
if __name__ == '__main__':
    serve()