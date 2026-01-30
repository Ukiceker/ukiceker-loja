@echo off
chcp 65001 >nul
echo ==========================================
echo      AUTOMACAO DE UPDATE - GITHUB
echo ==========================================
echo.

cd /d "%~dp0"

echo 1. Verificando status...
git status
echo.

set /p commit_msg="Digite a mensagem do Commit (Enter para 'Atualizacao Diaria'): "
if "%commit_msg%"=="" set commit_msg="Atualizacao Diaria"

echo.
echo 2. Adicionando arquivos...
git add .

echo.
echo 3. Realizando Commit...
git commit -m "%commit_msg%"

echo.
echo 4. Enviando para o GitHub (Push)...
git push

echo.
echo ==========================================
echo      PROCESSO FINALIZADO!
echo ==========================================
pause