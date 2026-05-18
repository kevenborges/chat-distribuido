import socket
import threading
import time
import uuid
import os
from datetime import datetime, timedelta # <-- Adicionado timedelta aqui
from flask import Flask, render_template, request, jsonify, session

app = Flask(__name__)
app.secret_key = 'chave_super_secreta_furg'
SERVIDORES = [('127.0.0.1', 5000), ('127.0.0.1', 5005)]
usuarios_web = {}

def conectar_servidor_disponivel(user_id):
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
                while not user['conectado'] and user_id in usuarios_web:
                    time.sleep(3)
                    if conectar_servidor_disponivel(user_id):
                        user['mensagens'].append("[SISTEMA]: Reconectado ao backup com sucesso!")
        else:
            time.sleep(1)

@app.route('/')
def index():
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
        thread = threading.Thread(target=receber_mensagens, args=(user_id,))
        thread.daemon = True
        thread.start()
        
        # --- FUSO HORÁRIO (UTC - 3 Horas) ---
        hora = (datetime.utcnow() - timedelta(hours=3)).strftime('%H:%M')
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
        
        if texto.strip() == '/clear':
            usuarios_web[user_id]['mensagens'].clear() 
            return jsonify({"status": "sucesso"})
        
        apelido = usuarios_web[user_id]['apelido']
        
        # --- FUSO HORÁRIO (UTC - 3 Horas) ---
        hora = (datetime.utcnow() - timedelta(hours=3)).strftime('%H:%M')
        
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
    porta_render = int(os.environ.get('PORT', 10000))
    print(f"Cliente Web hospedado na porta {porta_render}...")
    app.run(host='0.0.0.0', port=porta_render, debug=False)
