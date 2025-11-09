from flask import Flask, request, jsonify, render_template, send_from_directory, session, redirect, url_for
import sqlite3
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, static_folder='static')
app.secret_key = 'sio_admin_secret_key_2025'
app.config['UPLOAD_FOLDER'] = 'uploads'

# Garante que as pastas existem
os.makedirs('uploads', exist_ok=True)
os.makedirs('static', exist_ok=True)
os.makedirs('database', exist_ok=True)

DB_PATH = 'database/ocorrencias.db'

def get_conn():
    """Cria conexão com o banco SQLite"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inicializa o banco de dados com todas as tabelas"""
    print("🔄 Inicializando banco de dados...")
    
    try:
        conn = get_conn()
        
        # Tabela de ocorrências
        conn.execute('''
            CREATE TABLE IF NOT EXISTS ocorrencias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                descricao TEXT NOT NULL,
                categoria TEXT NOT NULL,
                anexo TEXT,
                status TEXT DEFAULT 'Pendente',
                data DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # VERIFICA E ADICIONA COLUNA STATUS SE NÃO EXISTIR
        cursor = conn.execute("PRAGMA table_info(ocorrencias)")
        colunas = [coluna[1] for coluna in cursor.fetchall()]
        if 'status' not in colunas:
            print("➕ Adicionando coluna 'status' à tabela ocorrências...")
            conn.execute('ALTER TABLE ocorrencias ADD COLUMN status TEXT DEFAULT "Pendente"')
        
        # Tabela de administradores
        conn.execute('''
            CREATE TABLE IF NOT EXISTS administradores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT UNIQUE NOT NULL,
                senha_hash TEXT NOT NULL,
                nome TEXT NOT NULL,
                email TEXT,
                data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de respostas
        conn.execute('''
            CREATE TABLE IF NOT EXISTS respostas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ocorrencia_id INTEGER NOT NULL,
                administrador_id INTEGER NOT NULL,
                mensagem TEXT NOT NULL,
                anexo TEXT,
                data_resposta DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de histórico de status
        conn.execute('''
            CREATE TABLE IF NOT EXISTS historico_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ocorrencia_id INTEGER NOT NULL,
                status_anterior TEXT NOT NULL,
                status_novo TEXT NOT NULL,
                administrador_id INTEGER NOT NULL,
                data_mudanca DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        
        # Cria um administrador padrão se não existir
        cursor = conn.execute("SELECT COUNT(*) as total FROM administradores")
        if cursor.fetchone()['total'] == 0:
            senha_hash = generate_password_hash('admin123')
            conn.execute('''
                INSERT INTO administradores (usuario, senha_hash, nome, email)
                VALUES (?, ?, ?, ?)
            ''', ('admin', senha_hash, 'Administrador Principal', 'admin@sio.com'))
            conn.commit()
            print("👤 Administrador padrão criado: usuario='admin', senha='admin123'")
        
        # Verifica tabelas criadas
        tabelas = ['ocorrencias', 'administradores', 'respostas', 'historico_status']
        for tabela in tabelas:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (tabela,))
            if cursor.fetchone():
                print(f"✅ Tabela '{tabela}' criada/verificada")
            else:
                print(f"❌ ERRO: Tabela '{tabela}' não foi criada!")
        
        conn.close()
        print("✅ Banco de dados inicializado com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro grave ao inicializar banco: {e}")

# ========== DECORATOR ADMIN REQUIRED ==========
def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            return redirect('/admin')
        return f(*args, **kwargs)
    return decorated_function

# ========== ROTAS PRINCIPAIS ==========
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/registrar')
def registrar():
    return render_template('registrar.html')

@app.route('/consultar')
def consultar():
    return render_template('consultar.html')

# ========== APIs PÚBLICAS ==========
@app.route('/api/registrar', methods=['POST'])
def registrar_ocorrencia():
    try:
        titulo = request.form.get('titulo', '').strip()
        descricao = request.form.get('descricao', '').strip()
        categoria = request.form.get('categoria', '').strip()
        anexo = request.files.get('anexo')
        
        if not titulo or not descricao or not categoria:
            return jsonify({'erro': 'Preencha todos os campos obrigatórios!'}), 400

        nome_arquivo = None
        if anexo and anexo.filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_arquivo = f"{timestamp}_{anexo.filename}"
            caminho_arquivo = os.path.join(app.config['UPLOAD_FOLDER'], nome_arquivo)
            anexo.save(caminho_arquivo)

        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO ocorrencias (titulo, descricao, categoria, anexo, status)
            VALUES (?, ?, ?, ?, 'Pendente')
        ''', (titulo, descricao, categoria, nome_arquivo))
        
        conn.commit()
        id_gerado = cursor.lastrowid
        conn.close()
        
        return jsonify({
            'mensagem': 'Ocorrência registrada com sucesso!',
            'id': id_gerado
        }), 201

    except Exception as e:
        print(f"❌ Erro ao registrar ocorrência: {e}")
        return jsonify({'erro': f'Erro interno: {str(e)}'}), 500

@app.route('/api/ocorrencias', methods=['GET'])
def listar_ocorrencias():
    try:
        conn = get_conn()
        
        ocorrencias = conn.execute('''
            SELECT id, titulo, descricao, categoria, anexo, status,
                   strftime('%d/%m/%Y às %H:%M', data) AS data
            FROM ocorrencias 
            ORDER BY data DESC
        ''').fetchall()
        
        conn.close()

        lista = []
        for o in ocorrencias:
            item = dict(o)
            if item.get('anexo'):
                item['anexo'] = f"/uploads/{item['anexo']}"
            lista.append(item)
            
        print(f"✅ Enviando {len(lista)} ocorrências para o frontend")
        return jsonify(lista)
        
    except Exception as e:
        print(f"❌ ERRO ao buscar ocorrências: {e}")
        return jsonify({'erro': 'Erro ao carregar ocorrências'}), 500

@app.route('/api/estatisticas')
def estatisticas():
    try:
        conn = get_conn()
        
        total = conn.execute("SELECT COUNT(*) as total FROM ocorrencias").fetchone()['total']
        
        categorias = conn.execute("""
            SELECT categoria, COUNT(*) as count 
            FROM ocorrencias 
            GROUP BY categoria
        """).fetchall()
        
        conn.close()
        
        return jsonify({
            'total': total,
            'categorias': [dict(cat) for cat in categorias],
            'total_categorias': len(categorias)
        })
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@app.route('/api/ocorrencia/<int:ocorrencia_id>')
def detalhes_ocorrencia(ocorrencia_id):
    """API para usuários verem detalhes de uma ocorrência específica com respostas"""
    try:
        conn = get_conn()
        
        # Busca a ocorrência
        ocorrencia = conn.execute('''
            SELECT o.*, strftime('%d/%m/%Y às %H:%M', o.data) AS data_formatada
            FROM ocorrencias o
            WHERE o.id = ?
        ''', (ocorrencia_id,)).fetchone()
        
        if not ocorrencia:
            return jsonify({'erro': 'Ocorrência não encontrada'}), 404
            
        # Busca as respostas
        respostas = conn.execute('''
            SELECT r.*, a.nome as admin_nome, 
                   strftime('%d/%m/%Y às %H:%M', r.data_resposta) AS data_resposta_formatada
            FROM respostas r
            JOIN administradores a ON r.administrador_id = a.id
            WHERE r.ocorrencia_id = ?
            ORDER BY r.data_resposta ASC
        ''', (ocorrencia_id,)).fetchall()
        
        conn.close()

        ocorrencia_dict = dict(ocorrencia)
        if ocorrencia_dict.get('anexo'):
            ocorrencia_dict['anexo'] = f"/uploads/{ocorrencia_dict['anexo']}"
            
        respostas_list = []
        for r in respostas:
            resposta_dict = dict(r)
            if resposta_dict.get('anexo'):
                resposta_dict['anexo'] = f"/uploads/{resposta_dict['anexo']}"
            respostas_list.append(resposta_dict)

        return jsonify({
            'ocorrencia': ocorrencia_dict,
            'respostas': respostas_list
        })
        
    except Exception as e:
        print(f"❌ ERRO ao buscar detalhes da ocorrência: {e}")
        return jsonify({'erro': 'Erro ao carregar detalhes'}), 500

# ========== ROTAS DE ADMIN ==========
@app.route('/admin')
def admin_login_page():
    return render_template('admin_login.html')

@app.route('/admin/login', methods=['POST'])
def admin_login():
    try:
        dados = request.json
        usuario = dados.get('usuario', '').strip()
        senha = dados.get('senha', '').strip()

        if not usuario or not senha:
            return jsonify({'erro': 'Usuário e senha são obrigatórios!'}), 400

        conn = get_conn()
        admin = conn.execute(
            'SELECT * FROM administradores WHERE usuario = ?', 
            (usuario,)
        ).fetchone()
        conn.close()

        if admin and check_password_hash(admin['senha_hash'], senha):
            session['admin_id'] = admin['id']
            session['admin_usuario'] = admin['usuario']
            session['admin_nome'] = admin['nome']
            
            return jsonify({
                'mensagem': 'Login realizado com sucesso!',
                'admin': {
                    'id': admin['id'],
                    'nome': admin['nome'],
                    'usuario': admin['usuario']
                }
            })
        else:
            return jsonify({'erro': 'Usuário ou senha incorretos!'}), 401

    except Exception as e:
        print(f"❌ Erro no login admin: {e}")
        return jsonify({'erro': 'Erro interno do servidor'}), 500

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    return render_template('admin_dashboard.html')

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect('/admin')

# ========== APIs DO PAINEL ADMIN ==========
@app.route('/admin/api/estatisticas')
@admin_required
def admin_estatisticas():
    try:
        conn = get_conn()
        
        total = conn.execute("SELECT COUNT(*) as total FROM ocorrencias").fetchone()['total']
        pendentes = conn.execute("SELECT COUNT(*) as count FROM ocorrencias WHERE status = 'Pendente'").fetchone()['count']
        em_andamento = conn.execute("SELECT COUNT(*) as count FROM ocorrencias WHERE status = 'Em Andamento'").fetchone()['count']
        resolvidas = conn.execute("SELECT COUNT(*) as count FROM ocorrencias WHERE status = 'Resolvido'").fetchone()['count']
        
        ocorrencias_com_resposta = conn.execute("""
            SELECT COUNT(DISTINCT ocorrencia_id) as count 
            FROM respostas
        """).fetchone()['count']
        
        conn.close()
        
        return jsonify({
            'total': total,
            'pendentes': pendentes,
            'em_andamento': em_andamento,
            'resolvidas': resolvidas,
            'com_resposta': ocorrencias_com_resposta
        })
        
    except Exception as e:
        print(f"❌ Erro ao buscar estatísticas admin: {e}")
        return jsonify({'erro': 'Erro ao carregar estatísticas'}), 500

@app.route('/admin/api/ocorrencias')
@admin_required
def admin_ocorrencias():
    try:
        conn = get_conn()
        
        ocorrencias = conn.execute('''
            SELECT o.*, 
                   strftime('%d/%m/%Y às %H:%M', o.data) AS data,
                   COUNT(r.id) as resposta_count
            FROM ocorrencias o
            LEFT JOIN respostas r ON o.id = r.ocorrencia_id
            GROUP BY o.id
            ORDER BY o.data DESC
        ''').fetchall()
        
        conn.close()

        lista = []
        for o in ocorrencias:
            item = dict(o)
            if item.get('anexo'):
                item['anexo'] = f"/uploads/{item['anexo']}"
            lista.append(item)
            
        print(f"✅ Enviando {len(lista)} ocorrências para o painel admin")
        return jsonify(lista)
        
    except Exception as e:
        print(f"❌ ERRO ao buscar ocorrências para admin: {e}")
        return jsonify({'erro': 'Erro ao carregar ocorrências'}), 500

@app.route('/admin/api/ocorrencias/<int:ocorrencia_id>')
@admin_required
def admin_detalhes_ocorrencia(ocorrencia_id):
    try:
        conn = get_conn()
        
        ocorrencia = conn.execute('''
            SELECT o.*, strftime('%d/%m/%Y às %H:%M', o.data) as data_formatada
            FROM ocorrencias o WHERE o.id = ?
        ''', (ocorrencia_id,)).fetchone()
        
        if not ocorrencia:
            return jsonify({'erro': 'Ocorrência não encontrada'}), 404
        
        respostas = conn.execute('''
            SELECT r.*, a.nome as admin_nome, 
                   strftime('%d/%m/%Y às %H:%M', r.data_resposta) as data_resposta_formatada
            FROM respostas r
            JOIN administradores a ON r.administrador_id = a.id
            WHERE r.ocorrencia_id = ?
            ORDER BY r.data_resposta DESC
        ''', (ocorrencia_id,)).fetchall()
        
        historico = conn.execute('''
            SELECT h.*, a.nome as admin_nome,
                   strftime('%d/%m/%Y às %H:%M', h.data_mudanca) as data_mudanca_formatada
            FROM historico_status h
            JOIN administradores a ON h.administrador_id = a.id
            WHERE h.ocorrencia_id = ?
            ORDER BY h.data_mudanca DESC
        ''', (ocorrencia_id,)).fetchall()
        
        conn.close()
        
        ocorrencia_dict = dict(ocorrencia)
        if ocorrencia_dict.get('anexo'):
            ocorrencia_dict['anexo'] = f"/uploads/{ocorrencia_dict['anexo']}"
            
        return jsonify({
            'ocorrencia': ocorrencia_dict,
            'respostas': [dict(r) for r in respostas],
            'historico': [dict(h) for h in historico]
        })
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@app.route('/admin/api/ocorrencias/<int:ocorrencia_id>/status', methods=['PUT'])
@admin_required  
def admin_alterar_status(ocorrencia_id):
    try:
        dados = request.json
        novo_status = dados.get('status')
        
        status_validos = ['Pendente', 'Em Andamento', 'Resolvido']
        if novo_status not in status_validos:
            return jsonify({'erro': 'Status inválido'}), 400
        
        conn = get_conn()
        cursor = conn.cursor()
        
        status_atual = conn.execute(
            'SELECT status FROM ocorrencias WHERE id = ?', 
            (ocorrencia_id,)
        ).fetchone()
        
        if not status_atual:
            return jsonify({'erro': 'Ocorrência não encontrada'}), 404
            
        cursor.execute(
            'UPDATE ocorrencias SET status = ? WHERE id = ?',
            (novo_status, ocorrencia_id)
        )
        
        cursor.execute('''
            INSERT INTO historico_status 
            (ocorrencia_id, status_anterior, status_novo, administrador_id)
            VALUES (?, ?, ?, ?)
        ''', (ocorrencia_id, status_atual['status'], novo_status, session['admin_id']))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'mensagem': f'Status alterado de {status_atual["status"]} para {novo_status}',
            'status_anterior': status_atual['status'],
            'novo_status': novo_status
        })
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@app.route('/admin/api/responder', methods=['POST'])
@admin_required
def admin_responder():
    try:
        ocorrencia_id = request.form.get('ocorrencia_id')
        mensagem = request.form.get('mensagem', '').strip()
        anexo = request.files.get('anexo')
        
        if not ocorrencia_id or not mensagem:
            return jsonify({'erro': 'Ocorrência e mensagem são obrigatórios!'}), 400

        nome_arquivo = None
        if anexo and anexo.filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_arquivo = f"resposta_{timestamp}_{anexo.filename}"
            caminho_arquivo = os.path.join(app.config['UPLOAD_FOLDER'], nome_arquivo)
            anexo.save(caminho_arquivo)

        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO respostas (ocorrencia_id, administrador_id, mensagem, anexo)
            VALUES (?, ?, ?, ?)
        ''', (ocorrencia_id, session['admin_id'], mensagem, nome_arquivo))
        
        cursor.execute('''
            UPDATE ocorrencias 
            SET status = 'Em Andamento' 
            WHERE id = ? AND status = 'Pendente'
        ''', (ocorrencia_id,))
        
        conn.commit()
        resposta_id = cursor.lastrowid
        conn.close()
        
        return jsonify({
            'mensagem': 'Resposta enviada com sucesso!',
            'id': resposta_id
        }), 201

    except Exception as e:
        return jsonify({'erro': f'Erro interno: {str(e)}'}), 500

# ========== SERVIÇOS DE ARQUIVOS ==========
@app.route('/uploads/<filename>')
def servir_arquivo(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ========== ROTAS DE DEBUG ==========
@app.route('/debug/banco')
def debug_banco():
    try:
        conn = get_conn()
        
        cursor = conn.execute("SELECT COUNT(*) as total FROM ocorrencias")
        total = cursor.fetchone()['total']
        
        ocorrencias = conn.execute('SELECT * FROM ocorrencias ORDER BY data DESC').fetchall()
        conn.close()
        
        resultado = []
        for o in ocorrencias:
            resultado.append(dict(o))
            
        return jsonify({
            'status': 'ok',
            'total_ocorrencias': total,
            'ocorrencias': resultado
        })
    except Exception as e:
        return jsonify({'erro': str(e)})

@app.route('/debug/adicionar-teste')
def adicionar_teste():
    try:
        conn = get_conn()
        
        conn.execute('''
            INSERT INTO ocorrencias (titulo, descricao, categoria, anexo, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            'Ocorrência de Teste', 
            'Esta é uma ocorrência de teste automaticamente gerada.', 
            'Infraestrutura', 
            None,
            'Pendente'
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'mensagem': 'Ocorrência de teste adicionada!'})
        
    except Exception as e:
        return jsonify({'erro': str(e)})

# --- INICIALIZAÇÃO ---
if __name__ == '__main__':  
    print("  ⚠️ INICIANDO SISTEMA SIO...")  
    init_db()  
    print("  🔴 Sistema pronto!")  
    print("  💡 Servidor: http://localhost:5000")  # ✅ MUDOU AQUI
    print("  🔴 Admin: http://localhost:5000/admin")  # ✅ MUDOU AQUI  
    print("  🔴 Credenciais: usuario='admin', senha='admin123'")  
    app.run(debug=True, host='0.0.0.0', port=5000)  # ✅ Este está correto!