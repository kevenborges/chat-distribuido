import socket
import threading
import os # Biblioteca para interagir com o sistema operacional (usada para o /crash)

HOST = '127.0.0.1' # Endereço IP local. Evita que robôs da internet acessem o socket diretamente.
PORT = 5000        # Porta de comunicação do Servidor Principal.
clientes = []      # Lista global que armazena os sockets de todos os usuários conectados.

def transmitir_mensagem(mensagem, cliente_remetente=None):
    """
    Função responsável por fazer o Broadcast (enviar para todos).
    Ela percorre a lista de clientes conectados e envia a mensagem recebida,
    garantindo que o remetente não receba a própria mensagem de volta.
    """
    for cliente in clientes:
        if cliente != cliente_remetente:
            try:
                # Tenta enviar a mensagem em bytes
                cliente.send(mensagem)
            except:
                # Se der erro (ex: cliente fechou o navegador do nada), remove ele da lista
                remover_cliente(cliente)

def gerenciar_cliente(cliente_socket, endereco):
    """
    Função executada por uma Thread dedicada para cada cliente.
    Fica em um loop infinito aguardando (escutando) mensagens daquele cliente específico.
    """
    print(f"[SERVIDOR PRINCIPAL] {endereco} conectado.")
    while True:
        try:
            # recv(1024) trava a execução desta thread até receber dados (máximo de 1024 bytes)
            mensagem = cliente_socket.recv(1024)
            if not mensagem:
                break # Se a mensagem for vazia, o cliente desconectou
            
            # Decodifica de bytes para texto para podermos fazer verificações
            texto = mensagem.decode('utf-8', errors='ignore')
            
            # --- COMANDO DE AUTODESTRUIÇÃO PARA DEMONSTRAÇÃO ---
            if "/crash" in texto:
                print("[SISTEMA] Comando /crash recebido. Simulando queda do servidor principal!")
                os._exit(0) # Encerra o processo do servidor instantaneamente
            # ---------------------------------------------------
            
            # Filtro Anti-Lixo: Bloqueia requisições HTTP perdidas de robôs do Render
            if "HTTP" in texto or "User-Agent" in texto or not texto.startswith('['):
                continue # Pula para a próxima repetição do loop ignorando a mensagem

            # Se a mensagem for válida, espalha para os outros usuários
            transmitir_mensagem(mensagem, cliente_socket)
        except:
            break # Qualquer erro de rede quebra o loop
            
    # Ao sair do loop, garante que o cliente será removido
    remover_cliente(cliente_socket)

def remover_cliente(cliente_socket):
    """Remove o socket do cliente da lista global e fecha a conexão."""
    if cliente_socket in clientes:
        clientes.remove(cliente_socket)
        cliente_socket.close()

def iniciar_servidor():
    """
    Função principal que inicializa o servidor TCP e fica escutando novas conexões.
    """
    # Cria o socket. AF_INET significa IPv4. SOCK_STREAM significa protocolo TCP.
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Permite reutilizar a porta imediatamente se o servidor reiniciar (evita erro "Address already in use")
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # Associa o socket ao IP e Porta
    servidor.bind((HOST, PORT))
    # Coloca o servidor em modo de escuta
    servidor.listen()
    print(f"[RODANDO] Servidor PRINCIPAL na porta {PORT}")
    
    while True:
        # accept() trava o código aqui até um novo cliente se conectar
        cliente_socket, endereco = servidor.accept()
        clientes.append(cliente_socket)
        
        # Cria uma Thread (linha de execução paralela) para o novo cliente não bloquear o servidor
        thread = threading.Thread(target=gerenciar_cliente, args=(cliente_socket, endereco))
        thread.start()

# Garante que o servidor só inicie se este arquivo for executado diretamente
if __name__ == "__main__":
    iniciar_servidor()
