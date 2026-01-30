import mysql.connector
import os

def testar_conexao():
    print("--- TESTE DE CONEXÃO (WINDOWS NATIVO) ---")
    
    # Configuração Local
    config = {
        'host': '127.0.0.1',        # Força TCP/IP (igual ao App)
        'user': 'ukiceker_app',     # Usuário da Aplicação
        'password': 'Ukiceker@123', # Senha da Aplicação
        'database': 'ukiceker_db',  # Já conecta direto no banco
        'use_pure': True
    }
    
    try:
        print(f"Conectando em 127.0.0.1 como 'ukiceker_app'...")
        # Tenta conectar sem especificar o banco primeiro, para ver se o servidor responde
        conexao = mysql.connector.connect(**config)
        
        if conexao.is_connected():
            print(f"✅ SUCESSO! Conexão Python estabelecida.")
            print(f"Versão: {conexao.server_info}")
            
            # Verifica se o banco 'ukiceker_db' existe
            cursor = conexao.cursor()
            cursor.execute("SELECT DATABASE();")
            db_atual = cursor.fetchone()[0]
            print(f"📂 Banco conectado: {db_atual}")
            
            cursor.close()
            conexao.close()
            
    except mysql.connector.Error as e:
        print(f"❌ ERRO: {e}")
        if e.errno == 1045:
            print("   -> Verifique usuário e senha no arquivo.")
        elif e.errno == 2003:
            print("   -> Verifique se o serviço MySQL está rodando e a porta 3306 está aberta.")

if __name__ == "__main__":
    testar_conexao()