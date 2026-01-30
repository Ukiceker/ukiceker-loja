@echo off
title ATUALIZACAO GIT
cls
echo =================================================
echo      SALVANDO PROGRESSO NO GITHUB
echo =================================================
echo.

git add .
git commit -m "Migracao Completa: Windows Nativo + Python 3.14 + MySQL Local"
git push -u origin main

echo.
echo [SUCESSO] Codigo salvo e sincronizado!
echo           Bom descanso!
pause