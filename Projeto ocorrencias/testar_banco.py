import sqlite3
import os

def testar_banco():
    print("🔍 TESTANDO BANCO DE DADOS...")
    
    # Conecta ao banco
    conn = sqlite3.connect('database/ocorrencias.db')
    cursor = conn.cursor()
    
    # Verifica se a tabela existe
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ocorrencias'")
    tabela_existe = cursor.fetchone()
    
    if tabela_existe:
        print("✅ Tabela 'ocorrencias' existe")
        
        # Conta ocorrências
        cursor.execute("SELECT COUNT(*) FROM ocorrencias")
        total = cursor.fetchone()[0]
        print(f"📊 Total de ocorrências: {total}")
        
        # Mostra todas as ocorrências
        cursor.execute("SELECT * FROM ocorrencias")
        ocorrencias = cursor.fetchall()
        
        if ocorrencias:
            print("📋 Ocorrências no banco:")
            for occ in ocorrencias:
                print(f"  ID: {occ[0]}, Título: {occ[1]}, Data: {occ[5]}")
        else:
            print("📭 Nenhuma ocorrência no banco")
    else:
        print("❌ Tabela 'ocorrencias' NÃO existe")
    
    conn.close()

if __name__ == "__main__":
    testar_banco()