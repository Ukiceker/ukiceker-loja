# -------------------------------------------------------------------------
# ARQUIVO: insert_amazon_products.py
# FUNÇÃO: Inserir produtos de teste da Amazon
# -------------------------------------------------------------------------

import mysql.connector
import os

def inserir_amazon():
    print("Conectando ao banco para inserir produtos Amazon...")
    
    try:
        conexao = mysql.connector.connect(
            host='127.0.0.1',
            user='ukiceker_app',
            password='Ukiceker@123',
            database='ukiceker_db',
            use_pure=True
        )
        cursor = conexao.cursor()
        
        # Dados de Teste Amazon
        produtos = [
            (
                "Echo Dot 5ª Geração", 
                399.00, 
                "https://placehold.co/300x300/png?text=Echo+Dot", 
                "https://amazon.com.br/exemplo-1", 
                "Amazon"
            ),
            (
                "Kindle 11ª Geração", 
                499.00, 
                "https://placehold.co/300x300/png?text=Kindle", 
                "https://amazon.com.br/exemplo-2", 
                "Amazon"
            )
        ]
        
        sql = "INSERT INTO produtos (nome, preco, imagem, link, plataforma) VALUES (%s, %s, %s, %s, %s)"
        cursor.executemany(sql, produtos)
        conexao.commit()
        print(f"SUCESSO: {cursor.rowcount} produtos Amazon inseridos.")
        cursor.close()
        conexao.close()
        
    except Exception as e:
        print(f"ERRO: {e}")

if __name__ == "__main__":
    inserir_amazon()