import socket
import os
import threading
import time
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session

app = Flask(__name__)
app.secret_key = 'chave_super_secreta_furg' # Necessário para usar sessões no Flask

SERVIDORES = [('127.0.0.1', 5000), ('127.0.0.1', 5005)]

# Dicionário global para gerenciar os múltiplos usuários acessando pelo navegador
# Formato: { "id_sessao": {"socket": obj, "mensagens": [], "conectado": bool, "apelido": str} }
usuarios_web = {}

def conectar_servidor_disponivel(user_id):
    """Tenta conectar o socket específico deste usuário ao servidor principal ou backup."""
    for host, port in SERVIDORES:
        try:
            novo_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            novo_socket.connect((host, port))
            usuarios_web[user_id]['socket'] = novo_socket
            usuarios_web[user_id]['conectado'] = True
            return True
        except:
            continue
    return False

def receber_mensagens(user_id):
    """Fica escutando mensagens para um usuário específico. Inclui a tolerância a falhas."""
    user = usuarios_web.get(user_id)
    
    while user and user_id in usuarios_web:
        if user['conectado']:
            try:
                mensagem = user['socket'].recv(1024).decode('utf-8')
                if mensagem:
                    user['mensagens'].append(mensagem)
                else:
                    raise Exception("Conexão TCP perdida")
            except:
                user['conectado'] = False
                user['mensagens'].append("[SISTEMA]: Conexão perdida. Tentando reconectar no servidor de backup...")
                
                # Tolerância a falhas: tenta reconectar
                while not user['conectado'] and user_id in usuarios_web:
                    time.sleep(3)
                    if conectar_servidor_disponivel(user_id):
                        user['mensagens'].append("[SISTEMA]: Reconectado ao servidor de backup com sucesso!")
        else:
            time.sleep(1)

@app.route('/')
def index():
    # Cria uma sessão única para quem abrir o navegador
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
    return render_template('index.html')

@app.route('/conectar', methods=['POST'])
def conectar():
    user_id = session.get('user_id')
    apelido = request.json.get('apelido')
    
    if user_id not in usuarios_web:
        usuarios_web[user_id] = {'socket': None, 'mensagens': [], 'conectado': False, 'apelido': apelido}
    
    if usuarios_web[user_id]['conectado']:
        return jsonify({"status": "sucesso"})

    if conectar_servidor_disponivel(user_id):
        # Inicia a thread dedicada para este usuário
        thread = threading.Thread(target=receber_mensagens, args=(user_id,))
        thread.daemon = True
        thread.start()
        
        # Envia uma mensagem de entrada no sistema
        hora = datetime.now().strftime('%H:%M')
        msg_entrada = f"[{hora}] [SISTEMA]: {apelido} entrou no chat."
        usuarios_web[user_id]['socket'].send(msg_entrada.encode('utf-8'))
        
        return jsonify({"status": "sucesso"})
    else:
        return jsonify({"status": "erro", "mensagem": "Nenhum servidor disponível."})

@app.route('/enviar', methods=['POST'])
def enviar():
    user_id = session.get('user_id')
    if user_id in usuarios_web and usuarios_web[user_id]['conectado']:
        texto = request.json.get('texto')
        
        # --- FILTRO DO COMANDO /CLEAR ---
        if texto.strip() == '/clear':
            usuarios_web[user_id]['mensagens'].clear() # Limpa a lista na memória do servidor
            return jsonify({"status": "sucesso"})
        # --------------------------------
        
        apelido = usuarios_web[user_id]['apelido']
        hora = datetime.now().strftime('%H:%M')
        mensagem_formatada = f"[{hora}] [{apelido}]: {texto}"
        try:
            usuarios_web[user_id]['socket'].send(mensagem_formatada.encode('utf-8'))
            usuarios_web[user_id]['mensagens'].append(mensagem_formatada)
            return jsonify({"status": "sucesso"})
        except:
            return jsonify({"status": "erro"})
    return jsonify({"status": "nao_conectado"})

@app.route('/mensagens', methods=['GET'])
def get_mensagens():
    user_id = session.get('user_id')
    if user_id in usuarios_web:
        return jsonify({"mensagens": usuarios_web[user_id]['mensagens']})
    return jsonify({"mensagens": []})

if __name__ == '__main__':
    # Pega a porta do Render ou usa 10000 como padrão
    porta_render = int(os.environ.get('PORT', 10000))
    print(f"Cliente Web hospedado na porta {porta_render}...")
    app.run(host='0.0.0.0', port=porta_render, debug=False)
