import os #biblioteca para lidar com arquivos e diretorios
import re #biblioteca para validações com expressões regulares, ou seja, (senha)
import sqlite3 #biblioteca padrão do Python para Banco de dados SQLite
from flask import Flask, render_template, request, redirect, url_for, session, g #bibiliotecas importantes do Flask

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chave_Oliveira' #chave secreta utilizada nas sessões
app.config['UPLOAD_FOLDER'] = 'static/uploads' #pasta para onde imagens serão salvas
app.config['MAX_CONTENT_LENGTH'] = 2*1024 * 1024 #Limite do tamanho de uploads para 2mb

#EXTENSOES = ['png', 'jpg', 'jpeg', 'gif'] #Extensões permitidas
DiasSemana = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado']
DATABASE = 'Caferetia.db' #Nome do banco SQLite

#--------------------- Configuração Inicial do App ----------------------------------------

def get_db():
    # Estabelecer e retornar a conexão com o banco de dados SQLite.
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.teardown_appcontext #Automatiza a execução após cada execução por conta desse decorador
def close_db(error):
    # Fechar a conexão com o banco após cada requisição
    #Esse 'g'é um objeto especial do Flask usado para armazenar dados globais da aplicação durante uma requisição (como variaveis)
    ''' da aplicaçção durante uma requisição como variaveis q vc quer acessar em varios lugares durante uma requisiscao http - se n existir retorna none'''
    db = g.pop('db', None) #Remove a conexão com o banco de g e armazena em db. Se não existir, retorna None
    if db is not None: #Se havia uma conexão, ela é fechada
        db.close()

 #--------------------- Função auxiliar para Verificar Extensão da Imagem ----------------------------------------       

'''def extensao_valida(nome_arquivo):
    # Vverificar se a extensao do arquivo enviado é uma das permitidas
    #Verifica se o nome do arquivo possui um ponto
    #'nome_arquivo.rsplit('.',1): separa o nome do aqruivo da extensao, da direita para a esquerda, uma vez só
    return '.' in nome_arquivo and nome_arquivo.rsplit('.', 1).lower in EXTENSOES
'''
 #--------------------- Criação das Tabelas (executar uma única vez) ----------------------------------------       

def inicializar_banco():
    # Criar as tabelas do banco caso não existam
    with app.app_context():
        db = get_db()
        db.execute('''
            CREATE TABLE IF NOT EXISTS usuarios(
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   nome TEXT NOT NULL,
                   email TEXT UNIQUE NOT NULL,
                   senha TEXT NOT NULL
            );
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS pratos(
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   titulo TEXT NOT NULL,
                   descricao TEXT NOT NULL,
                   preco INTEGER NOT NULL,
                   autor_id INTEGER NOT NULL
            );
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS bebidas(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    titulo TEXT NOT NULL,
                    descricao TEXT NOT NULL,
                    preco INTEGER NOT NULL
    
            );

        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS sugestoes(
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   titulo TEXT NOT NULL,
                   conteudo TEXT NOT NULL, 
                   autor_id INTEGER NOT NULL,
                   FOREIGN KEY (autor_id) REFERENCES usuarios (id)
                );
            ''')
        db.commit()

#--------------------- Rota Principal(index) ----------------------------------------       

@app.route('/')
def index():
    # Exibir todos os posts públicos na página inicial
#     db = get_db()
#     pratos = db.execute('''
#         SELECT titulo, descricao, preco FROM pratos
        
# ''').fetchall()
#     bebidas = db.execute('''
#         SELECT titulo, descricao, preco FROM bebidas    
# ''').fetchall()
#     return render_template('indexcafeteria.html', pratos = pratos, bebidas = bebidas)
   return render_template('indexcafeteria.html')
#--------------------- Rota Registro de Usuario ----------------------------------------       

@app.route('/cadastro_usuario', methods=['GET', 'POST'])
def cadastro_usuario():
    #Exibir o formulario de cadastro e processar os dados enviados.
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        #validar se a senha digitada possui no minimo 8 caracteres, 1 maiuscula, 1 numero e 1 simbolo
        if len(senha) <8:
            return "Senha fraca. Requisitos: 8+ caracteres, 1 maiuscula, 1 número e 1 símbolo"
        db = get_db()
        try:
            db.execute('INSERT INTO usuarios (nome, email, senha) VALUES (?,?,?)', (nome, email, senha))
            db.commit()
            return redirect(url_for('logincafe'))
        except sqlite3.IntegrityError:
            return "Error: Usuario ou Email já cadastrados."
    return render_template('cadastro_usuario.html')

#--------------------- Rota Registro de Menu ----------------------------------------   

@app.route('/cadastromenu', methods=['GET', 'POST'])
def criarpratos():
    #Exibir o formulario de cadastro e processar os dados enviados.
    if request.method == 'POST':
        titulo = request.form['titulo']
        descricao = request.form['descricao']
        preco = request.form['preco']

        db = get_db()
        try:
            db.execute('INSERT INTO pratos (titulo, descricao, preco) VALUES (?,?,?)', (titulo, descricao, preco))
            db.commit()
            return redirect(url_for('indexcafeteria'))
        except sqlite3.IntegrityError:
            return "Error: Produto já cadastrado."
    return render_template('cadastrocafe.html')

'''def criarbebidas():
    #Exibir o formulario de cadastro e processar os dados enviados.
    if request.method == 'POST':
        titulo = request.form['titulo']
        descricao = request.form['conteudo']
        preco = request.form['preco']

        db = get_db()
        try:
            db.execute('INSERT INTO bebidas (titulo, descricao, preco) VALUES (?,?,?)', (titulo, descricao, preco))
            db.commit()
            return redirect(url_for('indexcafeteria'))
        except sqlite3.IntegrityError:
            return "Error: Produto já cadastrado."
    return render_template('cadastrocafe.html')'''
#--------------------- Rota de Login ----------------------------------------       

@app.route('/logincafe', methods=('GET', 'POST'))
def logincafe():
    #Exibir e processar o formulario de login
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        db = get_db()
        usuario = db.execute('SELECT * FROM usuarios WHERE email=? AND senha=?', (email, senha)).fetchone()
        if usuario:
            session['usuario_id'] = usuario['id']#A sessão vai servir para identificar aquele usuario enquanto ele estiver logado e usando a aplicação
            session['usuario_nome'] = usuario['nome']
            return redirect(url_for('indexcafeteria'))
        else:
            return "Login inválido"
    
    return render_template('logincafe.html')

#--------------------- Painel do Usuario ----------------------------------------       

# @app.route('/indexcafeteria')
# #Exibir os posts do usuario logado.
# def indexcafeteria():
#     # if 'usuario.id' not in session:
#     #     return redirect(url_for('logincafe'))
    
#     db = get_db()
#     posts = db.execute('SELECT * FROM pratos WHERE autor_id=?', (session['usuario_id'])).fetchall() #Vai buscar dentro do banco de dados os posts do usuario q estiver logado
#     return render_template('indexcafeteria.html', posts=posts)

#--------------------- Rota para Criar Sugestao ---------------------------------------- 

@app.route('/sugestao')
def sugestao():
    #Permitir que o usuario logado crie uma sugestao de cardapio
    if 'usuario_id' not in session:
        return redirect(url_for('logincafe'))
    
    if request.method == 'POST':
        titulo = request.form['titulo']
        conteudo = request.form['conteudo']
        
        db = get_db()
        db.execute('INSERT INTO sugestoes (titulo, conteudo, autor_id) VALUES(?,?,?)', (titulo, conteudo, session['usuario_id']))
        db.commit()
    return redirect(url_for('confirma.html'))
#--------------------- Rota para Confirmação ----------------------------------------       

@app.route('/confirma')
def confirma():
    #Permitir que o usuario logado crie uma sugestao de cardapio
    if 'usuario_id' not in session:
        return redirect(url_for('logincafe'))
    
    print("Parabéns!")
    return redirect(url_for('confirma.html'))

'''@app.route('/cadastromenu', methods=['GET', 'POST'])
def new_post():
    #Permitir que o usuario logado crie um novo post com ou sem imagem
    if 'usuario_id' not in session:
        return redirect(url_for('logincafe'))
    
    if request.method == 'POST':
        titulo = request.form['titulo']
        conteudo = request.form['conteudo']
        preco = request.form['preco']

        
        db = get_db()
        db.execute('INSERT INTO pratos (titulo, conteudo, preco, VALUES(?,?,?)', (titulo, conteudo, preco, session['usuario_id']))
        db.commit()
        return redirect(url_for('indexcafeteria'))
    
    return render_template('cadastromenu.html')'''
    
#--------------------- Rota para Logout ----------------------------------------       

@app.route('/logout')
def logout():
    #Remove o usuario da sessão atual
    session.clear()
    return redirect(url_for('indexcafeteria'))    

#--------------------- Rota para execução principal ----------------------------------------       

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok = True) #Cria a pasta uploads se ela não existir
    inicializar_banco() #Garante que o banco e tabelas sejam criados
    app.run(debug = True)
