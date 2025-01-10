from concurrent import futures
import grpc
import user_pb2
import user_pb2_grpc
import mysql.connector
import logging

def normalize_email(email):
    local, domain = email.lower().split('@')
    
    if domain in ['gmail.com', 'googlemail.com']:
        local = local.replace('.', '')
        local = local.split('+')[0]
        
    return f"{local}@{domain}"

class UserCommandService(user_pb2_grpc.UserCommandServiceServicer):
    def __init__(self):
        self.conn = mysql.connector.connect(
            host="db",
            user="user",
            password="password",
            database="users"
        )
        self.requestRegister = {}
        self.requestUpdate = {}
        self.requestDelete = {}
        self.create_table()
        logging.basicConfig(level=logging.INFO)

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users
                          (email VARCHAR(255) PRIMARY KEY, ticker VARCHAR(255), low_value FLOAT, high_value FLOAT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS stock_values
                          (id INT AUTO_INCREMENT PRIMARY KEY, email VARCHAR(255), ticker VARCHAR(255), price FLOAT, timestamp TIMESTAMP, FOREIGN KEY (email) REFERENCES users(email))''')
        cursor.close()

    def RegisterUser(self, request, context):
        normalized_email = normalize_email(request.email)
        try:
            if normalized_email in self.requestRegister:
                if self.requestRegister[normalized_email] == 0:
                    return user_pb2.CommandResponse(message="Registration in process...")
                elif self.requestRegister[normalized_email] == 1:
                    return user_pb2.CommandResponse(message="User already registered successfully")

            self.requestRegister[normalized_email] = 0
            cursor = self.conn.cursor()
            try:
                cursor.execute("INSERT INTO users (email, ticker, low_value, high_value) VALUES (%s, %s, %s, %s)", 
                               (normalized_email, request.ticker, request.low_value, request.high_value))
                self.conn.commit()
                self.requestRegister[normalized_email] = 1
                if normalized_email in self.requestDelete:
                    self.requestDelete.pop(normalized_email, None)
                logging.info(f"User {normalized_email} registered successfully.")
                return user_pb2.CommandResponse(message="User registered successfully")
            except mysql.connector.Error as db_err:
                self.conn.rollback()
                self.requestRegister.pop(normalized_email, None) 
                logging.error(f"Database error: {db_err}")
                return user_pb2.CommandResponse(message="An error occurred during registration.")
            finally:
                cursor.close()
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            return user_pb2.CommandResponse(message="An unexpected error occurred.")

    def UpdateUser(self, request, context):
        normalized_email = normalize_email(request.email)
        key = (normalized_email, request.ticker, request.low_value, request.high_value)  

        try:
            if key in self.requestUpdate:
                if self.requestUpdate[key] == 0:
                    return user_pb2.CommandResponse(message="Update in process...")
                elif self.requestUpdate[key] == 1:
                    return user_pb2.CommandResponse(message="User already updated successfully")

            keys_to_delete = [k for k in self.requestUpdate if k[0] == normalized_email]
            for k in keys_to_delete:
                del self.requestUpdate[k]

            self.requestUpdate[key] = 0

            cursor = self.conn.cursor()
            try:
                cursor.execute("UPDATE users SET ticker = %s, low_value = %s, high_value = %s WHERE email = %s",
                               (request.ticker, request.low_value, request.high_value, normalized_email))
                self.conn.commit()
                self.requestUpdate[key] = 1
                return user_pb2.CommandResponse(message="User updated successfully")
            except mysql.connector.Error as db_err:
                self.conn.rollback()
                logging.error(f"Database error: {db_err}")
                return user_pb2.CommandResponse(message="An error occurred during update.")
            finally:
                cursor.close()
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            return user_pb2.CommandResponse(message="An unexpected error occurred.")

    def DeleteUser(self, request, context):
        normalized_email = normalize_email(request.email)
        try:
            if normalized_email in self.requestDelete:
                if self.requestDelete[normalized_email] == 0:
                    return user_pb2.CommandResponse(message="Deletion in process...")
                elif self.requestDelete[normalized_email] == 1:
                    return user_pb2.CommandResponse(message="User already deleted successfully")

            self.requestDelete[normalized_email] = 0

            cursor = self.conn.cursor()
            try:
                cursor.execute("DELETE FROM users WHERE email = %s", (normalized_email,))
                self.conn.commit()
                self.requestDelete[normalized_email] = 1
                if normalized_email in self.requestRegister:
                    self.requestRegister.pop(normalized_email, None)
                return user_pb2.CommandResponse(message="User deleted successfully")
            except mysql.connector.Error as db_err:
                self.conn.rollback()
                self.requestDelete.pop(normalized_email, None) 
                logging.error(f"Database error: {db_err}")
                return user_pb2.CommandResponse(message="An error occurred during deletion.")
            finally:
                cursor.close()
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            return user_pb2.CommandResponse(message="An unexpected error occurred.")

    def UpdateThreshold(self, request, context):
        normalized_email = normalize_email(request.email)
        key = (normalized_email, request.low_value, request.high_value)  

        try:
            if key in self.requestUpdate:
                if self.requestUpdate[key] == 0:
                    return user_pb2.CommandResponse(message="Update in process...")
                elif self.requestUpdate[key] == 1:
                    return user_pb2.CommandResponse(message="User already updated successfully")

            keys_to_delete = [k for k in self.requestUpdate if k[0] == normalized_email]
            for k in keys_to_delete:
                del self.requestUpdate[k]

            self.requestUpdate[key] = 0

            cursor = self.conn.cursor()
            try:
                if request.high_value == -1 and request.low_value == -1:
                    return user_pb2.CommandResponse(message="Non hai inserito valori da aggiornare")

                cursor.execute("SELECT low_value, high_value FROM users WHERE email = %s", (normalized_email,))
                result = cursor.fetchone()

                if result:
                    db_low_value = result[0]
                    db_high_value = result[1]
                    
                    if request.low_value == -1:
                        if db_low_value > request.high_value and request.high_value !=0 :
                            return user_pb2.CommandResponse(message="Errore: il low_value nel database è maggiore dell'high_value che stai cercando di inserire")
                        else: 
                            cursor.execute("UPDATE users SET high_value = %s WHERE email = %s",
                                    (request.high_value, normalized_email))
                            self.conn.commit()
                            self.requestUpdate[key] = 1
                            if request.high_value ==0:
                                return user_pb2.CommandeRespoonse (message="User updated successfully and high_value deleted")
                            return user_pb2.CommandResponse(message="User updated successfully")
                        
                    
                    if request.high_value == -1:
                        if request.low_value > db_high_value and request.low_value !=0:
                            return user_pb2.CommandResponse(message="Errore: l'high_value nel database è minore del low_value che stai cercando di inserire")
                        else: 
                            cursor.execute("UPDATE users SET low_value = %s WHERE email = %s",
                                    (request.low_value, normalized_email))
                            self.conn.commit()
                            self.requestUpdate[key] = 1
                            if request.low_value ==0:
                                return user_pb2.CommandeRespoonse (message="User updated successfully and low_value deleted")
                            return user_pb2.CommandResponse(message="User updated successfully")
                    
                    cursor.execute("UPDATE users SET low_value = %s, high_value = %s WHERE email = %s",
                                (request.low_value, request.high_value, normalized_email))
                    self.conn.commit()
                    self.requestUpdate[key] = 1
                    if request.low_value == 0 and request.high_value == 0: 
                        return user_pb2.CommandResponse(message="User threshold deleted successfully")
                    return user_pb2.CommandResponse(message="User updated successfully")

                else:
                    return user_pb2.CommandResponse(message="Errore: utente non trovato")

            finally:
                cursor.close()
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            return user_pb2.CommandResponse(message="An unexpected error occurred.")


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
    user_pb2_grpc.add_UserCommandServiceServicer_to_server(UserCommandService(), server)
    user_pb2_grpc.add_UserQueryServiceServicer_to_server(UserQueryService(), server)
    server.add_insecure_port('[::]:50052')
    server.start()
    server.wait_for_termination()
    
if __name__ == '__main__':
    serve()