import socket
import threading

HOST = '127.0.0.1' 
PORT = 5005        # Porta de comunicação do Servidor de Backup
clientes = []      # Lista global para armazenar os clientes que migrarem para cá

def transmitir_mensagem(mensagem, cliente_remetente=None):
    """Envia a mensagem recebida para todos os outros clientes conectados na porta 5005."""
    for cliente in clientes:
        if cliente != cliente_remetente:
            try:
                cliente.send(mensagem)
            except:
                remover_cliente(cliente)

def gerenciar_cliente(cliente_socket, endereco):
    """Escuta mensagens do cliente. Roda em uma thread separada."""
    print(f"[SERVIDOR BACKUP] {endereco} assumido.")
    while True:
        try:
            mensagem = cliente_socket.recv(1024)
            if not mensagem:
                break
            
            texto = mensagem.decode('utf-8', errors='ignore')
            
            # Filtro Anti-Lixo para ignorar robôs de monitoramento
            if "HTTP" in texto or "User-Agent" in texto or not texto.startswith('['):
                continue

            transmitir_mensagem(mensagem, cliente_socket)
        except:
            break
    remover_cliente(cliente_socket)

def remover_cliente(cliente_socket):
    """Remove e fecha o socket do cliente."""
    if cliente_socket in clientes:
        clientes.remove(cliente_socket)
        cliente_socket.close()

def iniciar_servidor():
    """Inicializa o servidor de Backup e aguarda conexões de resgate (tolerância a falhas)."""
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind((HOST, PORT))
    servidor.listen()
    print(f"[RODANDO] Servidor BACKUP na porta {PORT}")
    
    while True:
        cliente_socket, endereco = servidor.accept()
        clientes.append(cliente_socket)
        thread = threading.Thread(target=gerenciar_cliente, args=(cliente_socket, endereco))
        thread.start()

if __name__ == "__main__":
    iniciar_servidor()
