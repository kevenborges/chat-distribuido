import subprocess
import time

print("Iniciando Servidor Principal...")
servidor_principal = subprocess.Popen(["python", "server.py"])
time.sleep(1)

print("Iniciando Servidor de Backup...")
servidor_backup = subprocess.Popen(["python", "server_backup.py"])
time.sleep(1)

print("Iniciando Cliente Web (Flask)...")
cliente_web = subprocess.Popen(["python", "web_client.py"])

# Mantém o script principal rodando
try:
    cliente_web.wait()
except KeyboardInterrupt:
    print("Encerrando o sistema...")
    servidor_principal.terminate()
    servidor_backup.terminate()
    cliente_web.terminate()