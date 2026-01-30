# -------------------------------------------------------------------------
# ARQUIVO: gerar_site.py
# FUNÇÃO: Gerador de Site Estático (Static Site Generator)
# DESCRIÇÃO: Conecta no banco, pega os produtos e preenche o template HTML.
# -------------------------------------------------------------------------

import mysql.connector
import os
from jinja2 import Environment, FileSystemLoader

def gerar_site_estatico():
    print("Iniciando geração do site...")
    
    senha_root = os.environ.get('DB_ROOT_PASSWORD')
    
    try:
        # --- PASSO 1: Conectar ao Banco de Dados ---
        conexao = mysql.connector.connect(
            host='db',
            user='root',
            password=senha_root,
            database='ukiceker_db'
        )
        cursor = conexao.cursor()
        
        # --- PASSO 2: Buscar Produtos da Shopee ---
        cursor.execute("SELECT nome, preco, imagem, link FROM produtos WHERE plataforma='Shopee'")
        
        lista_shopee = []
        for (nome, preco, imagem, link) in cursor:
            lista_shopee.append({
                'nome': nome,
                'preco': str(preco).replace('.', ','), # Formata preço (ponto para vírgula)
                'imagem': imagem,
                'link': link
            })
            
        print(f"Encontrados {len(lista_shopee)} produtos da Shopee.")
        
        # --- PASSO 3: Configurar o Template (Jinja2) ---
        env = Environment(loader=FileSystemLoader('/app/templates'))
        template = env.get_template('index_template.html') # Usando o novo nome do template
        
        # --- PASSO 4: Renderizar (Preencher o molde com dados) ---
        html_final = template.render(produtos_shopee=lista_shopee)
        
        # --- PASSO 5: Salvar o arquivo final na pasta pública ---
        with open('/app/frontend_output/index.html', 'w', encoding='utf-8') as arquivo:
            arquivo.write(html_final)
            
        print("SUCESSO: Site atualizado em 'frontend/index.html'!")
        
    except Exception as e:
        print(f"ERRO: {e}")

if __name__ == "__main__":
    gerar_site_estatico()