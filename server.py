# server.py
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

# --- Configuração ---
basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- Modelo do Banco de Dados ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    total_block_seconds = db.Column(db.Integer, default=0)

# --- Endpoints da API ---
@app.route('/register', methods=['POST'])
def register():
    print("\n[REGISTRO] Recebida requisição para /register")
    data = request.get_json()
    print(f"[REGISTRO] Dados recebidos: {data}")

    if not data or not 'username' in data or not 'password' in data:
        print("[REGISTRO] ERRO: Dados ausentes na requisição.")
        return jsonify({'message': 'Dados ausentes!'}), 400
        
    username = data['username']
    password = data['password']
    
    print(f"[REGISTRO] Verificando se o usuário '{username}' já existe...")
    if User.query.filter_by(username=username).first():
        print(f"[REGISTRO] ERRO: Usuário '{username}' já existe.")
        return jsonify({'message': 'Usuário já existe'}), 409

    print(f"[REGISTRO] Usuário '{username}' é novo. Criando hash da senha...")
    hashed_password = generate_password_hash(password)
    new_user = User(username=username, password_hash=hashed_password)
    
    print(f"[REGISTRO] Salvando novo usuário '{username}' no banco de dados.")
    db.session.add(new_user)
    db.session.commit()
    
    print("[REGISTRO] Retornando sucesso (201).")
    return jsonify({'message': 'Usuário registrado com sucesso!'}), 201

@app.route('/login', methods=['POST'])
def login():
    print("\n[LOGIN] Recebida requisição para /login")
    data = request.get_json()
    
    if not data or not 'username' in data or not 'password' in data:
        print("[LOGIN] ERRO: Dados ausentes na requisição.")
        return jsonify({'message': 'Dados ausentes!'}), 400

    username = data['username']
    password = data['password']
    print(f"[LOGIN] Tentativa de login para usuário: '{username}'")

    print(f"[LOGIN] Buscando usuário '{username}' no banco de dados...")
    user = User.query.filter_by(username=username).first()

    if not user:
        print(f"[LOGIN] ERRO: Usuário '{username}' não encontrado.")
        return jsonify({'message': 'Credenciais inválidas'}), 401
    
    print("[LOGIN] Usuário encontrado. Verificando senha...")
    if not check_password_hash(user.password_hash, password):
        print(f"[LOGIN] ERRO: Senha incorreta para o usuário '{username}'.")
        return jsonify({'message': 'Credenciais inválidas'}), 401

    print(f"[LOGIN] Senha correta para '{username}'. Login bem-sucedido.")
    print("[LOGIN] Retornando sucesso (200).")
    return jsonify({'message': 'Login bem-sucedido'}), 200

@app.route('/add_time', methods=['POST'])
def add_time():
    print("\n[ADD_TIME] Recebida requisição para /add_time")
    data = request.get_json()
    print(f"[ADD_TIME] Dados recebidos: {data}")

    if not data or not 'username' in data or not 'seconds' in data:
        print("[ADD_TIME] ERRO: Dados ausentes na requisição.")
        return jsonify({'message': 'Dados ausentes!'}), 400
        
    username = data['username']
    user = User.query.filter_by(username=username).first()
    
    if not user:
        print(f"[ADD_TIME] ERRO: Usuário '{username}' não encontrado.")
        return jsonify({'message': 'Usuário não encontrado'}), 404
        
    seconds_to_add = data.get('seconds', 0)
    print(f"[ADD_TIME] Adicionando {seconds_to_add}s ao total do usuário '{username}'. Total anterior: {user.total_block_seconds}s")
    
    user.total_block_seconds += seconds_to_add
    db.session.commit()
    
    print(f"[ADD_TIME] Salvamento concluído. Novo total: {user.total_block_seconds}s")
    print("[ADD_TIME] Retornando sucesso (200).")
    return jsonify({
        'message': 'Tempo adicionado com sucesso', 
        'new_total_seconds': user.total_block_seconds
    }), 200

@app.route('/ranking', methods=['GET'])
def get_ranking():
    print("\n[RANKING] Recebida requisição para /ranking")
    print("[RANKING] Buscando e ordenando usuários do banco de dados...")
    top_users = User.query.order_by(db.desc(User.total_block_seconds)).limit(100).all()
    print(f"[RANKING] {len(top_users)} usuários encontrados.")
    
    ranking_data = []
    for i, user in enumerate(top_users):
        ranking_data.append({
            'rank': i + 1,
            'username': user.username,
            'total_seconds': user.total_block_seconds
        })
        
    print("[RANKING] Retornando lista de ranking (200).")
    return jsonify(ranking_data), 200

# --- Ponto de Execução Principal ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    print(">>> Servidor Flask iniciando...")
    app.run(host='0.0.0.0', port=5000, debug=True)
