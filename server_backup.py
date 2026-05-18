import socket
import threading

HOST = '0.0.0.0'
PORT = 5005

clientes = []
historico_mensagens = []

def transmitir_mensagem(mensagem, cliente_remetente=None):
    for cliente in clientes:
        if cliente != cliente_remetente:
            try:
                cliente.send(mensagem)
            except:
                remover_cliente(cliente)

def gerenciar_cliente(cliente_socket, endereco):
    print(f"[BACKUP] {endereco} conectado.")
    
    for msg in historico_mensagens:
        try:
            cliente_socket.send(msg)
        except:
            pass

    while True:
        try:
            mensagem = cliente_socket.recv(1024)
            if not mensagem:
                break
            historico_mensagens.append(mensagem)
            if len(historico_mensagens) > 20:
                historico_mensagens.pop(0)
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
    print(f"[RODANDO] Servidor de BACKUP em {HOST}:{PORT}")
    
    while True:
        cliente_socket, endereco = servidor.accept()
        clientes.append(cliente_socket)
        thread = threading.Thread(target=gerenciar_cliente, args=(cliente_socket, endereco))
        thread.start()

if __name__ == "__main__":
    iniciar_servidor()