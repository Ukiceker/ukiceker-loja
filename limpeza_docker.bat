@echo off
title LIMPEZA DE ARQUIVOS DOCKER (OBSOLETOS)
cls
echo =================================================
echo      REMOVENDO ARQUIVOS DO ANTIGO AMBIENTE
echo =================================================
echo.

:: 1. Arquivos de Configuracao Docker
if exist "docker-compose.yml" (
    del "docker-compose.yml"
    echo [REMOVIDO] docker-compose.yml
)

:: 2. Scripts de Diagnostico/Correcao Docker
if exist "diagnostico.bat" (
    del "diagnostico.bat"
    echo [REMOVIDO] diagnostico.bat
)
if exist "fix_auth.bat" (
    del "fix_auth.bat"
    echo [REMOVIDO] fix_auth.bat
)
if exist "reset_ambiente.bat" (
    del "reset_ambiente.bat"
    echo [REMOVIDO] reset_ambiente.bat
)
if exist "atualizar_servidor.bat" (
    del "atualizar_servidor.bat"
    echo [REMOVIDO] atualizar_servidor.bat
)

:: 3. Pastas de Infraestrutura Docker (Proxy)
if exist "npm" (
    rmdir /s /q "npm"
    echo [REMOVIDO] Pasta 'npm' (Nginx Proxy Manager)
)

echo.
echo [SUCESSO] Limpeza concluida! O projeto agora e 100%% Windows Nativo.
pause