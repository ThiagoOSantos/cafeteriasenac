import os #Biblioteca para lidar com arquivos e diretórios
import re #Biblioteca para validações com expressões regulares (senha)
import sqlite3 #Biblioteca padrão do Python para banco de dados SQLite
from flask import Flask, render_template, request, redirect, url_for, session, g #Bibliotecas importantes do Flask
from werkzeug.utils import secure_filename #Biblioteca que garante nomes seguros para arquivos enviados

# ---------------------- Configuração Inicial do App ------------------------------------

app = Flask(__name__) #Criação da aplicação Flask
app.config['SECRET_KEY'] = 'chave_mauri' #Chave secreta utilizada nas sessões
app.config['UPLOAD_FOLDER'] = 'static/uploads' #Pasta para onde imagens serão salvas
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024 #Limite do tamanho de uploads para 2mb

EXTENSOES = {'png', 'jpg', 'jpeg', 'gif'} #Extensões permitidas

DATABASE = 'users.db' #Nome do banco SQLite

# ---------------------- Função para Conectar o Banco ------------------------------------

def get_db():
    # Estabelecer e retornar a conexão com o banco de dados SQLite.
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row #Permite acessar os dados como dicionario (ex: linha['email'])
    return g.db

@app.teardown_appcontext #Automatiza a execução após cada requisição por conta desse decorador
def close_db(error):
    #Fechar a conexão com o banco após cada requisição
    #Esse 'g' é um objeto especial do Flask usado para armazenar dados globais da aplicação durante uma requisição (como variáveis que você quer acessar em vários lugares durante uma requisição HTTP).
    db = g.pop('db', None) #Remove a conexão com o banco de g e armazena em db. Se não existir, retorna None.
    if db is not None: #Se havia uma conexão, ela é fechada 
        db.close()

# ---------------------- Função Auxiliar para Verificar Extensão da Imagem ------------------------------------

def extensao_valida(nome_arquivo):
    # Verificar se a extensão do arquivo enviado é uma das permitidas
    # Verifica se o nome do arquivo possui um ponto
    #'nome_arquivo.rsplit('.', 1): separa o nome do arquivo da extensão, da direita para a esquerda, uma vez só'
    return '.' in nome_arquivo and nome_arquivo.rsplit('.', 1)[1].lower() in EXTENSOES

# ---------------------- Criação das Tabelas (executar uma única vez) ------------------------------------

def inicializar_banco():
    #Criar as tabelas do banco caso não existam
    with app.app_context():
        db = get_db()
        db.execute('''
            CREATE TABLE IF NOT EXISTS usuarios(
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   nome TEXT NOT NULL,
                   cpf TEXT UNIQUE NOT NULL,
                   email TEXT UNIQUE NOT NULL,
                   senha TEXT NOT NULL
            );
        ''') 
        db.execute('''
            CREATE TABLE IF NOT EXISTS posts(
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   titulo TEXT NOT NULL,
                   conteudo TEXT NOT NULL,
                   imagem TEXT,
                   autor_id INTEGER NOT NULL,
                   FOREIGN KEY (autor_id) REFERENCES usuarios (id)
                );
            ''')
        db.commit()

# ---------------------- Rota Principal (Index) ------------------------------------

@app.route('/')
def index():
    # Exibir todos os posts públicos na página inicial
    db = get_db()
    posts = db.execute('''
        SELECT p.titulo, p.conteudo, p.imagem, u.nome 
        FROM posts p
        JOIN usuarios u ON p.autor_id = u.id
    ''').fetchall()
    return render_template('index.html', posts=posts)

# ---------------------- Rota Registro de Usuário (register) ------------------------------------

@app.route('/register', methods=['GET', 'POST'])
def register():
    #Exibir o formulário de cadastro e processar os dados enviados.
    if request.method == 'POST':
        nome = request.form['nome']
        cpf = request.form['cpf']
        email = request.form['email']
        senha = request.form['senha']

        #Validar se a senha digitada possui no mínimo 8 caracteres, 1 maiuscula, 1 nímero e 1 símbolo
        if len(senha) < 8:
            return "Senha fraca. Requisitos: 8+ caracteres, 1 maiuscula, 1 número e 1 símbolo."
        
        db = get_db()
        try:
            db.execute('INSERT INTO usuarios (nome, cpf, email, senha) VALUES (?, ?, ?, ?)', (nome, cpf, email, senha))
            db.commit()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return "Error: CPF ou email já cadastrados."
    return render_template('register.html')

# ---------------------- Rota de Login (login) ------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    #Exibir e processar o formulário de login
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        db = get_db()
        usuario = db.execute('SELECT * FROM usuarios WHERE email=? AND senha=?', (email, senha)).fetchone()
        if usuario:
            session['usuario_id'] = usuario['id']
            session['usuario_nome'] = usuario['nome']
            return redirect(url_for('dashboard'))
        else:
            return "Login inválido."
    return render_template('login.html')

# ---------------------- Painel do Usuário ------------------------------------
@app.route('/dashboard')
def dashboard():
#Exibir os posts do usuário logado.
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    db = get_db()
    posts = db.execute('SELECT * FROM posts WHERE autor_id=?', (session['usuario_id'],)).fetchall()
    return render_template('dashboard.html', posts=posts)

# ---------------------- Rota para Criar Novo Post ------------------------------------
@app.route('/new_post', methods=['GET', 'POST'])
def new_post():
    #Permitir que o usuário logado crie um novo post com ou sem imagem
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        titulo = request.form['titulo']
        conteudo = request.form['conteudo']
        imagem = request.files['imagem']

        nome_arquivo = None
        if imagem and extensao_valida(imagem.filename):
            nome_arquivo = secure_filename(imagem.filename)
            imagem.save(os.path.join(app.config['UPLOAD_FOLDER'], nome_arquivo))

        db = get_db()
        db.execute('INSERT INTO posts (titulo, conteudo, imagem, autor_id) VALUES (?, ?, ?, ?)', (titulo, conteudo, nome_arquivo, session['usuario_id']))
        db.commit()
        return redirect(url_for('dashboard'))
    
    return render_template('new_post.html')
    
# ---------------------- Rota para Logout ------------------------------------    
@app.route('/logout')    
def logout():
    #Remove o usuário da sessão atual.
    session.clear()
    return redirect(url_for('index'))

# ---------------------- Execução Principal ------------------------------------
if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True) # Cria a pasta de uploads se ela não existir
    inicializar_banco() # Garante que o banco e tabelas sejam criados
    app.run(debug=True)
