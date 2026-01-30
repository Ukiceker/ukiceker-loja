# -------------------------------------------------------------------------
# ARQUIVO: insert_ml_products.py
# FUNÇÃO: Inserir produtos de teste do Mercado Livre
# -------------------------------------------------------------------------

import mysql.connector
import os

def inserir_ml():
    print("Conectando ao banco para inserir produtos Mercado Livre...")
    
    try:
        conexao = mysql.connector.connect(
            host='127.0.0.1',
            user='ukiceker_app',
            password='Ukiceker@123',
            database='ukiceker_db',
            use_pure=True
        )
        cursor = conexao.cursor()
        
        # Dados de Teste Mercado Livre
        produtos = [
            (
                "Chromecast 4 com Google TV", 
                289.90, 
                "https://placehold.co/300x300/png?text=Chromecast", 
                "https://mercadolivre.com.br/exemplo-1", 
                "Mercado Livre"
            ),
            (
                "Controle Xbox Series S/X", 
                350.00, 
                "https://placehold.co/300x300/png?text=Controle+Xbox", 
                "https://mercadolivre.com.br/exemplo-2", 
                "Mercado Livre"
            )
        ]
        
        sql = "INSERT INTO produtos (nome, preco, imagem, link, plataforma) VALUES (%s, %s, %s, %s, %s)"
        cursor.executemany(sql, produtos)
        conexao.commit()
        print(f"SUCESSO: {cursor.rowcount} produtos Mercado Livre inseridos.")
        cursor.close()
        conexao.close()
        
    except Exception as e:
        print(f"ERRO: {e}")

if __name__ == "__main__":
    inserir_ml()