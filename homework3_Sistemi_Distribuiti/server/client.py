import grpc
import sys
import user_pb2
import user_pb2_grpc

class StockMonitorClient:
    def __init__(self, command_host='localhost', command_port=30003, query_host='localhost', query_port=30004):
        """
        Inizializza il client gRPC con due canali di comunicazione separati per i comandi e le query
        
        :param command_host: Indirizzo del server dei comandi (default: localhost)
        :param command_port: Porta del server dei comandi (default: 30003)
        :param query_host: Indirizzo del server delle query (default: localhost)
        :param query_port: Porta del server delle query (default: 30004)
        """
        self.command_channel = grpc.insecure_channel(f'{command_host}:{command_port}')
        self.query_channel = grpc.insecure_channel(f'{query_host}:{query_port}')
        self.command_stub = user_pb2_grpc.UserCommandServiceStub(self.command_channel)
        self.query_stub = user_pb2_grpc.UserQueryServiceStub(self.query_channel)

    def register_user(self, email, ticker, low_value=None, high_value=None):
        """
        Registra un nuovo utente
        
        :param email: Email dell'utente
        :param ticker: Ticker delle azioni
        :param low_value: Soglia minima (opzionale)
        :param high_value: Soglia massima (opzionale)
        """
        try:
            request = user_pb2.RegisterUserRequest(
                email=email, 
                ticker=ticker, 
                low_value=low_value, 
                high_value=high_value 
            )
            response = self.command_stub.RegisterUser(request)
            print("Risposta RegisterUser:", response.message)
        except grpc.RpcError as e:
            print(f"Errore gRPC: {e.code()} - {e.details()}")

    def update_user(self, email, ticker, low_value=None, high_value=None):
        """
        Aggiorna i dettagli di un utente esistente
        
        :param email: Email dell'utente
        :param ticker: Nuovo ticker delle azioni
        :param low_value: Nuova soglia minima (opzionale)
        :param high_value: Nuova soglia massima (opzionale)
        """
        try:
            request = user_pb2.UpdateUserRequest(
                email=email, 
                ticker=ticker, 
                low_value=low_value if low_value is not None else 0, 
                high_value=high_value if high_value is not None else 0
            )
            response = self.command_stub.UpdateUser(request)
            print("Risposta UpdateUser:", response.message)
        except grpc.RpcError as e:
            print(f"Errore gRPC: {e.code()} - {e.details()}")

    def delete_user(self, email):
        """
        Rimuove un utente
        
        :param email: Email dell'utente da rimuovere
        """
        try:
            request = user_pb2.DeleteUserRequest(email=email)
            response = self.command_stub.DeleteUser(request)
            print("Risposta DeleteUser:", response.message)
        except grpc.RpcError as e:
            print(f"Errore gRPC: {e.code()} - {e.details()}")

    def update_threshold(self, email, low_value=None, high_value=None):
        """
        Aggiorna le soglie di un utente
        
        :param email: Email dell'utente
        :param low_value: Nuova soglia minima (opzionale)
        :param high_value: Nuova soglia massima (opzionale)
        """
        try:
            request = user_pb2.UpdateThresholdRequest(
                email=email, 
                low_value=low_value if low_value is not None else 0, 
                high_value=high_value if high_value is not None else 0
            )
            response = self.command_stub.UpdateThreshold(request)
            print("Risposta UpdateThreshold:", response.message)
        except grpc.RpcError as e:
            print(f"Errore gRPC: {e.code()} - {e.details()}")

    def remove_threshold(self, email, remove_low=False, remove_high=False):
        """
        Rimuove le soglie di un utente
        
        :param email: Email dell'utente
        :param remove_low: Rimuove la soglia minima se True
        :param remove_high: Rimuove la soglia massima se True
        """
        try:
            request = user_pb2.RemoveThresholdRequest(
                email=email, 
                low_value=0 if remove_low else None, 
                high_value=0 if remove_high else None
            )
            response = self.command_stub.RemoveThreshold(request)
            print("Risposta RemoveThreshold:", response.message)
        except grpc.RpcError as e:
            print(f"Errore gRPC: {e.code()} - {e.details()}")

    def get_last_stock_value(self, email):
        """
        Recupera l'ultimo valore delle azioni per un utente
        
        :param email: Email dell'utente
        :return: Valore delle azioni
        """
        try:
            request = user_pb2.EmailRequest(email=email)
            response = self.query_stub.GetLastStockValue(request)
            print(f"Risposta LastStockValue: {response.message} Valore: {response.value}")
            return response.value
        except grpc.RpcError as e:
            print(f"Errore gRPC: {e.code()} - {e.details()}")
            return None

    def get_average_stock_value(self, email, count):
        """
        Calcola il valore medio delle azioni per un utente
        
        :param email: Email dell'utente
        :param count: Numero di valori per calcolare la media
        :return: Valore medio delle azioni
        """
        try:
            request = user_pb2.AverageStockRequest(email=email, count=count)
            response = self.query_stub.GetAverageStockValue(request)
            print(f"Risposta AverageStockValue: {response.message} Valore: {response.value}")
            return response.value
        except grpc.RpcError as e:
            print(f"Errore gRPC: {e.code()} - {e.details()}")
            return None

    def get_all_data(self):
        """
        Recupera tutti i dati degli utenti
        
        :return: Lista di dati degli utenti
        """
        try:
            request = user_pb2.Empty()
            response = self.query_stub.GetAllData(request)
            print("Risposta Tutti Gli Utenti:")
            if not response.data:
                print("Nessun dato trovato.")
            else:
                for data in response.data:
                    print(data)
            return list(response.data)
        except grpc.RpcError as e:
            print(f"Errore gRPC: {e.code()} - {e.details()}")
            return []

def main():
    """
    Funzione principale per l'interfaccia a riga di comando
    """
    client = StockMonitorClient()

    while True:
        print("\nMenu:")
        print("1. Aggiungi Nuovo Utente")   
        print("2. Modifica Ticker")
        print("3. Modifica Soglie")
        print("4. Rimuovi Utente")  
        print("5. Visualizza Ultimo Valore delle Azioni")
        print("6. Calcola Valore Medio delle Azioni")
        print("7. Visualizza Tutti gli Utenti")            
        print("8. Esci")    
        
        choice = input("Inserisci la tua scelta: ")

        try:
            match choice:
                case '1':
                    email = input("Inserisci email: ")
                    ticker = input("Inserisci ticker: ")
                    
                    low_value_input = input("Inserisci soglia minima (premi invio per non specificare): ")
                    high_value_input = input("Inserisci soglia massima (premi invio per non specificare): ")

                    low_value = float(low_value_input) if low_value_input else None
                    high_value = float(high_value_input) if high_value_input else None
                    
                    # Verifica che la soglia minima non sia maggiore di quella massima
                    if (low_value is not None and high_value is not None and low_value > high_value):
                        print("Errore: soglia minima maggiore di quella massima")
                        continue

                    client.register_user(email, ticker, low_value, high_value)

                case '2':
                    email = input("Inserisci email: ")
                    ticker = input("Inserisci nuovo ticker: ")
                    
                    low_value_input = input("Inserisci soglia minima (premi invio per non specificare): ")
                    high_value_input = input("Inserisci soglia massima (premi invio per non specificare): ")

                    low_value = float(low_value_input) if low_value_input else None
                    high_value = float(high_value_input) if high_value_input else None
                    
                    # Verifica che la soglia minima non sia maggiore di quella massima
                    if (low_value is not None and high_value is not None and low_value > high_value):
                        print("Errore: soglia minima maggiore di quella massima")
                        continue

                    client.update_user(email, ticker, low_value, high_value)

                case '3':
                    email = input("Inserisci email: ")
                    
                    # Gestione soglia minima
                    risposta1 = input("Vuoi Eliminare [e], Aggiornare [a] o Ignorare [invio] la soglia minima? ")
                    low_value = -1
                    if risposta1 == 'e':
                        low_value = 0
                    elif risposta1 == 'a':
                        low_value_input = input("Inserisci soglia minima: ")
                        low_value = float(low_value_input) if low_value_input else None

                    # Gestione soglia massima
                    risposta2 = input("Vuoi Eliminare [e], Aggiornare [a] o Ignorare [invio] la soglia massima? ")
                    high_value = -1
                    if risposta2 == 'e':
                        high_value = 0
                    elif risposta2 == 'a':
                        high_value_input = input("Inserisci soglia massima: ")
                        high_value = float(high_value_input) if high_value_input else None

                    # Verifica che la soglia minima non sia maggiore di quella massima
                    if (low_value > high_value):
                        if (low_value == 0 or high_value==0 or low_value == -1 or high_value==-1 ):
                            client.update_threshold(email, low_value, high_value)
                        else:
                            print("Errore: soglia minima maggiore di quella massima")
                            break
                    client.update_threshold(email, low_value, high_value)
  

                case '4':
                    email = input("Inserisci email: ")
                    client.delete_user(email)

                case '5':
                    email = input("Inserisci l'email: ")
                    client.get_last_stock_value(email)

                case '6':
                    email = input("Inserisci email: ")
                    count = int(input("Inserisci il numero di valori per la media: "))
                    client.get_average_stock_value(email, count)

                case '7':
                    client.get_all_data()

                case '8':
                    print("Uscita in corso...")
                    break

                case _:
                    print("Inserisci un numero da 1 a 8.")

        except ValueError:
            print("Input non valido. Riprova.")
        except Exception as e:
            print(f"Si è verificato un errore: {e}")

if __name__ == "__main__":
    main()