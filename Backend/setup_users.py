# -------------------------------------------------------------------------
# ARQUIVO: setup_users.py
# FUNÇÃO: Configuração da Tabela de Usuários e Admin Padrão
# DESCRIÇÃO: Cria tabela com suporte a hash seguro e flag de troca de senha.
# -------------------------------------------------------------------------

import mysql.connector
import os
import hashlib
import binascii

def hash_password(password):
    """Cria um hash seguro da senha usando PBKDF2 e Salt (Padrão seguro)."""
    # Gera um salt aleatório (tempero) para que senhas iguais tenham hashs diferentes
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
    # Cria o hash criptográfico
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), 
                                salt, 100000)
    pwdhash = binascii.hexlify(pwdhash)
    # Retorna salt + hash para salvar no banco (precisaremos disso para validar depois)
    return (salt + pwdhash).decode('ascii')

def configurar_usuarios():
    print("Iniciando configuração de Usuários e Segurança...")
    
    try:
        # Usando as credenciais da aplicação (127.0.0.1) para garantir consistência
        conexao = mysql.connector.connect(
            host='127.0.0.1',
            user='ukiceker_app',
            password='Ukiceker@123',
            database='ukiceker_db',
            use_pure=True
        )
        cursor = conexao.cursor()
        
        # 1. Criar Tabela de Usuários
        # Inclui campos para Hierarquia (nivel_acesso) e Segurança (senha_hash, trocar_senha)
        tabela_sql = """
        CREATE TABLE IF NOT EXISTS usuarios (
            id INT AUTO_INCREMENT PRIMARY KEY,
            usuario VARCHAR(50) NOT NULL UNIQUE,
            senha_hash VARCHAR(255) NOT NULL,
            nivel_acesso VARCHAR(20) DEFAULT 'operador',
            trocar_senha TINYINT(1) DEFAULT 1,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        cursor.execute(tabela_sql)
        print("Tabela 'usuarios' verificada.")
        
        # 2. Verificar se o Usuário de Teste já existe
        cursor.execute("SELECT id FROM usuarios WHERE usuario = 'teste'")
        if cursor.fetchone():
            print("Usuário 'teste' já existe. Nenhuma ação necessária.")
        else:
            # 3. Criar Usuário Padrão para Primeiro Acesso
            senha_padrao = "123456"
            # Criptografa a senha antes de salvar
            senha_segura = hash_password(senha_padrao)
            
            sql_insert = "INSERT INTO usuarios (usuario, senha_hash, nivel_acesso, trocar_senha) VALUES (%s, %s, %s, %s)"
            # Nível 'admin' para controle total, trocar_senha=1 para forçar mudança
            cursor.execute(sql_insert, ("teste", senha_segura, "admin", 1))
            conexao.commit()
            print(f"SUCESSO: Usuário 'teste' criado.")
            print(f"AVISO: A senha é '{senha_padrao}' e será solicitada a troca no primeiro login.")
            
        cursor.close()
        conexao.close()
        
    except Exception as e:
        print(f"ERRO: {e}")

if __name__ == "__main__":
    configurar_usuarios()