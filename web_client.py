import socket
import threading
import time
import uuid
import os
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, session

# Inicializa o framework web Flask
app = Flask(__name__)
app.secret_key = 'chave_super_secreta_furg' # Chave de criptografia necessária para usar Sessões

# Lista de servidores para a Tolerância a Falhas: Principal na [0], Backup na [1]
SERVIDORES = [('127.0.0.1', 5000), ('127.0.0.1', 5005)]

# Dicionário que armazena os dados de cada aba de navegador aberta
# Estrutura: { "id_sessao_do_usuario": { socket, mensagens, conectado, apelido } }
usuarios_web = {}

def conectar_servidor_disponivel(user_id):
    """
    Tenta conectar o socket deste usuário ao servidor principal. 
    Se falhar, tenta o próximo da lista (backup).
    """
    for host, port in SERVIDORES:
        try:
            # Cria um socket TCP novo para este usuário web
            novo_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            novo_socket.connect((host, port))
            # Salva o socket no dicionário do usuário
            usuarios_web[user_id]['socket'] = novo_socket
            usuarios_web[user_id]['conectado'] = True
            return True # Retorna verdadeiro se conseguiu conectar
        except:
            continue # Se deu erro, tenta o próximo servidor da lista
    return False # Retorna falso se todos os servidores estiverem fora do ar

def receber_mensagens(user_id):
    """
    Thread dedicada para cada navegador web. Fica escutando o Socket TCP em background.
    Aqui ocorre a Tolerância a Falhas ativa!
    """
    user = usuarios_web.get(user_id)
    while user and user_id in usuarios_web:
        if user['conectado']:
            try:
                # Tenta receber os pacotes do servidor
                mensagem = user['socket'].recv(1024).decode('utf-8')
                if mensagem:
                    user['mensagens'].append(mensagem)
                else:
                    raise Exception("Conexão TCP perdida")
            except:
                # O SISTEMA DETECTOU UMA QUEDA DO SERVIDOR!
                user['conectado'] = False
                user['mensagens'].append("[SISTEMA]: Conexão perdida. Tentando reconectar no servidor de backup...")
                
                # Inicia o resgate: Tenta conectar no próximo servidor imediatamente
                while not user['conectado'] and user_id in usuarios_web:
                    if conectar_servidor_disponivel(user_id):
                        user['mensagens'].append("[SISTEMA]: Reconectado ao backup com sucesso!")
                        break # Se conectou, sai do loop de resgate
                    time.sleep(2) # Se ambos estiverem fora, dorme 2 segundos e tenta de novo
        else:
            time.sleep(1)

@app.route('/')
def index():
    """Rota inicial que carrega a interface gráfica em HTML."""
    # Se o usuário não tiver uma Sessão, cria um ID único (UUID) para ele
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
    return render_template('index.html')

@app.route('/conectar', methods=['POST'])
def conectar():
    """Rota chamada pelo Javascript quando o usuário digita o apelido e clica em Iniciar."""
    user_id = session.get('user_id')
    apelido = request.json.get('apelido')
    
    # Prepara o espaço na memória para este usuário
    if user_id not in usuarios_web:
        usuarios_web[user_id] = {'socket': None, 'mensagens': [], 'conectado': False, 'apelido': apelido}
    
    # Evita duplas conexões
    if usuarios_web[user_id]['conectado']:
        return jsonify({"status": "sucesso"})
        
    # Tenta conectar via Socket. Se conseguir, inicia a Thread receptora.
    if conectar_servidor_disponivel(user_id):
        thread = threading.Thread(target=receber_mensagens, args=(user_id,))
        thread.daemon = True # Thread daemon morre automaticamente quando o Flask fecha
        thread.start()
        
        # Ajusta o Fuso Horário de UTC para Horário de Brasília (-3)
        hora = (datetime.utcnow() - timedelta(hours=3)).strftime('%H:%M')
        msg_entrada = f"[{hora}] [SISTEMA]: {apelido} entrou no chat."
        usuarios_web[user_id]['socket'].send(msg_entrada.encode('utf-8'))
        return jsonify({"status": "sucesso"})
    else:
        return jsonify({"status": "erro", "mensagem": "Nenhum servidor disponível."})

@app.route('/enviar', methods=['POST'])
def enviar():
    """Rota para disparar mensagens do navegador para o Servidor TCP."""
    user_id = session.get('user_id')
    if user_id in usuarios_web and usuarios_web[user_id]['conectado']:
        texto = request.json.get('texto')
        
        # Filtro de Comando local: Esvazia a memória de mensagens deste usuário
        if texto.strip() == '/clear':
            usuarios_web[user_id]['mensagens'].clear() 
            return jsonify({"status": "sucesso"})
        
        apelido = usuarios_web[user_id]['apelido']
        hora = (datetime.utcnow() - timedelta(hours=3)).strftime('%H:%M')
        
        # Formata a mensagem no padrão [Hora] [Apelido]: Texto
        mensagem_formatada = f"[{hora}] [{apelido}]: {texto}"
        try:
            # Envia via Socket e salva na tela do remetente
            usuarios_web[user_id]['socket'].send(mensagem_formatada.encode('utf-8'))
            usuarios_web[user_id]['mensagens'].append(mensagem_formatada)
            return jsonify({"status": "sucesso"})
        except:
            return jsonify({"status": "erro"})
    return jsonify({"status": "nao_conectado"})

@app.route('/mensagens', methods=['GET'])
def get_mensagens():
    """Rota de Polling: O JS pergunta a cada 1 segundo se há mensagens novas."""
    user_id = session.get('user_id')
    if user_id in usuarios_web:
        return jsonify({"mensagens": usuarios_web[user_id]['mensagens']})
    return jsonify({"mensagens": []})

if __name__ == '__main__':
    # Lê a porta dinâmica fornecida pelo Render na nuvem (ou 10000 como padrão)
    porta_render = int(os.environ.get('PORT', 10000))
    print(f"Cliente Web hospedado na porta {porta_render}...")
    # host='0.0.0.0' permite que a rede externa acesse o Flask
    app.run(host='0.0.0.0', port=porta_render, debug=False)
