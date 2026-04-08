@echo off
echo Iniciando AlphaDash (MetaTrader 5 Dashboard)...

:: Iniciar el Backend en una nueva ventana
echo Iniciando el Servidor Backend (Python)...
start "AlphaDash Backend" cmd /k "cd backend && python run.py"

:: Iniciar el Frontend en una nueva ventana
echo Iniciando el Servidor Frontend (React/Vite)...
start "AlphaDash Frontend" cmd /k "cd frontend && npm run dev"

echo =======================================================
echo ¡Los dos servidores se estan ejecutando en segundo plano!
echo Tus pestañas de la consola se abrieron en ventanas nuevas.
echo =======================================================
pause
