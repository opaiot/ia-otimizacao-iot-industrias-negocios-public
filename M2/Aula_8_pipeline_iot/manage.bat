@echo off
REM Script de gerenciamento do Pipeline IoT


setlocal enabledelayedexpansion


if "%1"=="" goto help
if /I "%1"=="start" goto start
if /I "%1"=="stop" goto stop
if /I "%1"=="restart" goto restart
if /I "%1"=="status" goto status
if /I "%1"=="logs" goto logs
if /I "%1"=="clean" goto clean
if /I "%1"=="test" goto test
if /I "%1"=="psql" goto psql
if /I "%1"=="build" goto build


echo Comando desconhecido: %1
goto end


:start
echo 🚀 Iniciando serviços...
docker-compose up -d
echo ✓ Serviços iniciados!
echo.
echo Acesse:
echo   - Grafana: http://localhost:3001 (admin/admin)
echo   - API:     http://localhost:3000/api/latest
echo   - MQTT:    mqtt://localhost:1883
echo.
echo Aguarde 30-60 segundos para todos os serviços estarem prontos...
goto end


:stop
echo 🛑 Parando serviços...
docker-compose down
echo ✓ Serviços parados!
goto end


:restart
echo 🔄 Reiniciando serviços...
docker-compose restart
echo ✓ Serviços reiniciados!
goto end


:status
echo 📊 Status dos serviços:
echo.
docker-compose ps
goto end


:logs
echo 📋 Exibindo logs em tempo real...
echo (Pressione Ctrl+C para sair)
echo.
docker-compose logs -f
goto end


:clean
echo 🧹 Removendo containers...
docker-compose down --remove-orphans
echo ✓ Containers removidos!
goto end


:test
echo 🧪 Testando conexão MQTT...
goto end


:psql
echo 🗄️ Conectando ao PostgreSQL...
docker-compose exec postgres psql -U iot_user -d iot_database
goto end


:build
echo 🏗️ Reconstruindo imagens Docker...
docker-compose build --no-cache
echo ✓ Imagens reconstruídas!
goto end


:help
echo.
echo ╔════════════════════════════════════════╗
echo ║   Pipeline IoT - Gerenciador Docker   ║
echo ╚════════════════════════════════════════╝
echo.
echo Comandos disponíveis:
echo   start
echo   stop
echo   restart
echo   status
echo   logs
echo   clean
echo   test
echo   psql
echo   build


:end

