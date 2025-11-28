import psutil
import requests
import time
import socket

SERVER_URL = "http://127.0.0.1:5000"
API_ENDPOINT = f"{SERVER_URL}/api/data"
COMPUTER_ID = "1"  
API_KEY = "troque_esta_api_key_para_producao" 

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
        headers = {"X-API-KEY": API_KEY}
        response = requests.post(API_ENDPOINT, json=data, headers=headers)
        if response.status_code == 200:
            print(f"[{time.strftime('%H:%M:%S')}] Dados enviados com sucesso!")
        else:
            print(f"[{time.strftime('%H:%M:%S')}] ERRO {response.status_code}: {response.text}")
    except requests.exceptions.ConnectionError:
        print(f"[{time.strftime('%H:%M:%S')}] ERRO: Não foi possível conectar ao servidor.")
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] ERRO inesperado: {e}")

if __name__ == "__main__":
    if COMPUTER_ID == "1":
        print("!!! ATENÇÃO: Substitua COMPUTER_ID pelo ID real do seu computador !!!")
    while True:
        metrics = get_system_metrics()
        send_data_to_server(metrics)
        time.sleep(5)
