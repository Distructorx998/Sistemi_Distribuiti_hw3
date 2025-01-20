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

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    user_pb2_grpc.add_UserCommandServiceServicer_to_server(UserCommandService(), server)
    server.add_insecure_port('[::]:50052')
    server.start()
    server.wait_for_termination()
    
if __name__ == '__main__':
    serve()
