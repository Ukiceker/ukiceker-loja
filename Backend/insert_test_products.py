# -------------------------------------------------------------------------
# ARQUIVO: insert_test_products.py
# FUNÇÃO: Popular Banco com Dados de Teste
# DESCRIÇÃO: Insere produtos fictícios para validar o funcionamento do frontend.
# -------------------------------------------------------------------------

import mysql.connector
import os

def inserir_produtos_teste():
    print("Conectando ao banco para inserir produtos...")
    
    senha_root = os.environ.get('DB_ROOT_PASSWORD')
    
    try:
        conexao = mysql.connector.connect(
            host='db',
            user='root',
            password=senha_root,
            database='ukiceker_db'
        )
        cursor = conexao.cursor()
        
        # --- Dados de Teste (Mock Data) ---
        # Formato: (Nome, Preço, URL Imagem, Link Afiliado, Plataforma)
        produtos = [
            (
                "Fone de Ouvido Bluetooth TWS F9-5", 
                29.90, 
                "https://placehold.co/300x300/png?text=Fone+TWS", 
                "https://shopee.com.br/produto-exemplo-1", 
                "Shopee"
            ),
            (
                "Smartwatch D20 Pro Y68", 
                19.99, 
                "https://placehold.co/300x300/png?text=Smartwatch", 
                "https://shopee.com.br/produto-exemplo-2", 
                "Shopee"
            ),
            (
                "Kit 3 Camisetas Básicas Algodão", 
                49.90, 
                "https://placehold.co/300x300/png?text=Camisetas", 
                "https://shopee.com.br/produto-exemplo-3", 
                "Shopee"
            )
        ]
        
        # --- Execução da Inserção ---
        sql = "INSERT INTO produtos (nome, preco, imagem, link, plataforma) VALUES (%s, %s, %s, %s, %s)"
        
        cursor.executemany(sql, produtos)
        conexao.commit()
        
        print(f"SUCESSO: {cursor.rowcount} produtos inseridos na tabela 'produtos'.")
        
        cursor.close()
        conexao.close()
        
    except Exception as e:
        print(f"ERRO: {e}")

if __name__ == "__main__":
    inserir_produtos_teste()