# corrigir_banco.py
import sqlite3
import os

def corrigir_banco():
    print("🔧 CORRIGINDO BANCO DE DADOS...")
    
    DB_PATH = 'database/ocorrencias.db'
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Verifica se a coluna status existe
        cursor.execute("PRAGMA table_info(ocorrencias)")
        colunas = [coluna[1] for coluna in cursor.fetchall()]
        
        print("📊 Colunas atuais na tabela ocorrências:", colunas)
        
        # Se a coluna status não existe, adiciona
        if 'status' not in colunas:
            print("➕ Adicionando coluna 'status'...")
            cursor.execute('''
                ALTER TABLE ocorrencias 
                ADD COLUMN status TEXT DEFAULT 'Pendente'
            ''')
            print("✅ Coluna 'status' adicionada!")
        
        # Verifica se a tabela historico_status existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='historico_status'")
        if not cursor.fetchone():
            print("➕ Criando tabela 'historico_status'...")
            cursor.execute('''
                CREATE TABLE historico_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ocorrencia_id INTEGER NOT NULL,
                    status_anterior TEXT NOT NULL,
                    status_novo TEXT NOT NULL,
                    administrador_id INTEGER NOT NULL,
                    data_mudanca DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            print("✅ Tabela 'historico_status' criada!")
        
        conn.commit()
        conn.close()
        
        print("🎉 Banco de dados corrigido com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro ao corrigir banco: {e}")

if __name__ == "__main__":
    corrigir_banco()