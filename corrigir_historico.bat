@echo off
chcp 65001 >nul
echo ==========================================
echo      CORRECAO DE HISTORICO GIT
echo ==========================================
echo.
echo O envio falhou porque o arquivo gigante (Docker)
echo ainda esta gravado no historico dos commits anteriores.
echo.
echo Vamos resetar o historico local para o estado do GitHub
echo e refazer o commit apenas com os arquivos corretos.
echo.
pause

echo.
echo 1. Resetando para o ultimo estado valido do GitHub...
git reset --mixed origin/main

echo.
echo 2. Adicionando arquivos novamente (respeitando o .gitignore)...
git add .

echo.
echo 3. Criando novo commit limpo...
git commit -m "Reset: Atualizacao limpa do codigo (sem instaladores)"

echo.
echo 4. Forcando envio (Push)...
git push origin main

echo.
echo ==========================================
echo      CORRECAO CONCLUIDA!
echo ==========================================
pause