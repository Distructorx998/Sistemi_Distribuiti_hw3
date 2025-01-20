## **Guida al build & deploy**
### **Prequisiti**
Assicurarsi che siano installati i seguenti elementi:
- **Docker**
- **DockerCompose**
- **Abilitare l'estenzione di Kubernets su Docker Desktop**    
### **Passaggi**
Portarsi in ogni sottodirtectory

1. **Fare le build di tutte le immagini** 
 Eseguire il seguente comando per costruire tutti i servizi:

docker build -t <nome_utente>/<nome_dell'immagine> -f nome del file .

 ```
2. **Fare la push di tutte le immagini create**
 Eseguire il seguente comando per pushare tutte le immagini su Docker Hub:

docker push <nome_utente>/<nome_dell'immagine>
 
 ```
3. **Applicare i manifest**
 Eseguire il seguente comando per applicare tutti i manifest della diretory corrente:

kubectl apply -f .
 ```

4. **Eseguire il Client**
 Spostarsi nella directory /server ed eseguire il seguente comando per far partire il client:

python client.py
