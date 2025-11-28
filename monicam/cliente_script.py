import psutil
import requests
import time
import json
import socket

#config
SERVER_URL = "http://127.0.0.1:5000" 
#rota para receber as info do py
API_ENDPOINT = f"{SERVER_URL}/api/data"

COMPUTER_ID = "1" 

#rotas

def get_system_metrics():
    cpu_usage = psutil.cpu_percent(interval=1)

    memory = psutil.virtual_memory()
    ram_percent = memory.percent
    
    disk = psutil.disk_usage('/')
    disk_percent = disk.percent

    hostname = socket.gethostname()

    timestamp = time.time()
    
    return {
        "computer_id": COMPUTER_ID,
        "timestamp": timestamp,
        "hostname": hostname,
        "cpu_usage": cpu_usage,
        "ram_percent": ram_percent,
        "disk_percent": disk_percent
    }

def send_data_to_server(data):
    try:
#enviar os dados em JSON
        response = requests.post(API_ENDPOINT, json=data)
        
        if response.status_code == 200:
            print(f"[{time.strftime('%H:%M:%S')}] Dados enviados com sucesso! Resposta: {response.json().get('message')}")
        else:
            print(f"[{time.strftime('%H:%M:%S')}] ERRO ao enviar dados. Status: {response.status_code}. Resposta: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print(f"[{time.strftime('%H:%M:%S')}] ERRO: Não foi possível conectar ao servidor {SERVER_URL}. Verifique se o Flask está a correr.")
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] ERRO inesperado: {e}")

#loop principal

if __name__ == "__main__":
    if COMPUTER_ID == "1":
        print("!!! ATENÇÃO: Por favor, substitua COMPUTER_ID pelo ID real do seu computador !!!")
        
    print(f"--- Script Cliente de Monitoramento Iniciado (ID: {COMPUTER_ID}) ---")
    
#loop que envia dados em 5 segundos
    while True:
        metrics = get_system_metrics()
        
        send_data_to_server(metrics)
        time.sleep(5)