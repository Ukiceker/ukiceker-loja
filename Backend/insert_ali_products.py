# -------------------------------------------------------------------------
# ARQUIVO: insert_ali_products.py
# FUNÇÃO: Inserir produtos de teste do AliExpress
# -------------------------------------------------------------------------

import mysql.connector
import os

def inserir_ali():
    print("Conectando ao banco para inserir produtos AliExpress...")
    
    try:
        conexao = mysql.connector.connect(
            host='127.0.0.1',
            user='ukiceker_app',
            password='Ukiceker@123',
            database='ukiceker_db',
            use_pure=True
        )
        cursor = conexao.cursor()
        
        # Dados de Teste AliExpress
        produtos = [
            (
                "Lenovo LP40 Pro", 
                45.00, 
                "https://placehold.co/300x300/png?text=Lenovo+LP40", 
                "https://aliexpress.com/exemplo-1", 
                "AliExpress"
            ),
            (
                "SSD NVMe 1TB Kingspec", 
                220.00, 
                "https://placehold.co/300x300/png?text=SSD+1TB", 
                "https://aliexpress.com/exemplo-2", 
                "AliExpress"
            )
        ]
        
        sql = "INSERT INTO produtos (nome, preco, imagem, link, plataforma) VALUES (%s, %s, %s, %s, %s)"
        cursor.executemany(sql, produtos)
        conexao.commit()
        print(f"SUCESSO: {cursor.rowcount} produtos AliExpress inseridos.")
        cursor.close()
        conexao.close()
        
    except Exception as e:
        print(f"ERRO: {e}")

if __name__ == "__main__":
    inserir_ali()