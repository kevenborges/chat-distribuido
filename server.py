import socket
import threading
import os # <-- Necessário para forçar o desligamento

HOST = '127.0.0.1' 
PORT = 5000 
clientes = []

def transmitir_mensagem(mensagem, cliente_remetente=None):
    for cliente in clientes:
        if cliente != cliente_remetente:
            try:
                cliente.send(mensagem)
            except:
                remover_cliente(cliente)

def gerenciar_cliente(cliente_socket, endereco):
    print(f"[SERVIDOR PRINCIPAL] {endereco} conectado.")
    while True:
        try:
            mensagem = cliente_socket.recv(1024)
            if not mensagem:
                break
            
            texto = mensagem.decode('utf-8', errors='ignore')
            
            # --- COMANDO DE AUTODESTRUIÇÃO PARA O PROFESSOR TESTAR ---
            if "/crash" in texto:
                print("[SISTEMA] Comando /crash recebido. Simulando queda do servidor principal!")
                os._exit(0) # Mata o processo deste servidor na hora!
            # ---------------------------------------------------------
            
            if "HTTP" in texto or "User-Agent" in texto or not texto.startswith('['):
                continue

            transmitir_mensagem(mensagem, cliente_socket)
        except:
            break
    remover_cliente(cliente_socket)

def remover_cliente(cliente_socket):
    if cliente_socket in clientes:
        clientes.remove(cliente_socket)
        cliente_socket.close()

def iniciar_servidor():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind((HOST, PORT))
    servidor.listen()
    print(f"[RODANDO] Servidor PRINCIPAL na porta {PORT}")
    while True:
        cliente_socket, endereco = servidor.accept()
        clientes.append(cliente_socket)
        thread = threading.Thread(target=gerenciar_cliente, args=(cliente_socket, endereco))
        thread.start()

if __name__ == "__main__":
    iniciar_servidor()
