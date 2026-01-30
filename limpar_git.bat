@echo off
chcp 65001 >nul
echo ==========================================
echo      CORRECAO E LIMPEZA DO GIT
echo ==========================================
echo.
echo 1. Removendo pastas pesadas do rastreamento (mantendo local)...
git rm -r --cached chrome_profile/ 2>nul
git rm -r --cached edge_profile/ 2>nul
git rm -r --cached instaladores/ 2>nul
git rm -r --cached "Material de apoio/" 2>nul

echo.
echo 2. Removendo logs e dumps temporarios...
git rm -r --cached *.log 2>nul
git rm -r --cached dump_*.json 2>nul
git rm -r --cached "Material de apoio/Imagens/temp_import_*" 2>nul

echo.
echo 3. Confirmando a limpeza...
git add .gitignore
git commit -m "Fix: Removendo cache do navegador e arquivos temporarios do repositorio"

echo.
echo 4. Atualizando GitHub (Push)...
git push
pause