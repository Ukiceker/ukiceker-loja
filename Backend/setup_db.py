# -------------------------------------------------------------------------
# ARQUIVO: setup_db.py
# FUNÇÃO: Configuração Inicial do Banco de Dados
# DESCRIÇÃO: Cria o banco 'ukiceker_db' e a tabela 'produtos' se não existirem.
# -------------------------------------------------------------------------

import mysql.connector
import os

def configurar_banco():
    print("Iniciando configuração do Banco de Dados...")
    
    senha_root = os.environ.get('DB_ROOT_PASSWORD')
    
    try:
        # --- PASSO 1: Conectar ao MySQL (sem banco específico) ---
        conexao = mysql.connector.connect(
            host='db',
            user='root',
            password=senha_root
        )
        cursor = conexao.cursor()
        
        # --- PASSO 2: Criar o Banco de Dados ---
        cursor.execute("CREATE DATABASE IF NOT EXISTS ukiceker_db")
        print("Banco 'ukiceker_db' verificado.")
        
        # --- PASSO 3: Selecionar o Banco ---
        cursor.execute("USE ukiceker_db")
        
        # --- PASSO 4: Criar a Tabela de Produtos ---
        tabela_sql = """
        CREATE TABLE IF NOT EXISTS produtos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nome VARCHAR(255) NOT NULL,
            preco DECIMAL(10, 2),
            imagem TEXT,
            link TEXT,
            plataforma VARCHAR(50)
        )
        """
        cursor.execute(tabela_sql)
        print("SUCESSO: Tabela 'produtos' criada/verificada!")
        
        cursor.close()
        conexao.close()
        
    except Exception as e:
        print(f"ERRO: {e}")

if __name__ == "__main__":
    configurar_banco()