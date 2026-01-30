import mysql.connector
import os
import time

def testar_conexao():
    print("Tentando conectar ao banco de dados...")
    
    # Pega a senha que configuramos no docker-compose.yml
    senha_root = os.environ.get('DB_ROOT_PASSWORD')
    
    try:
        conexao = mysql.connector.connect(
            host='db',              # Nome do serviço no Docker
            user='root',            # Usuário administrador
            password=senha_root,    # Senha vinda do .env
            database='ukiceker_db'  # Nome do banco
        )

        if conexao.is_connected():
            info_banco = conexao.get_server_info()
            print(f"SUCESSO! Conectado ao MySQL versão {info_banco}")
            conexao.close()
            
    except Exception as erro:
        print(f"ERRO ao conectar: {erro}")

if __name__ == "__main__":
    testar_conexao()