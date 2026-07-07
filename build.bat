@echo off
echo =======================================================
echo  Iniciando empaquetado - Sistema de Horarios
echo =======================================================

pip show flet >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Flet no esta instalado. Ejecute: pip install flet[all]
    pause
    exit /b %errorlevel%
)

flet pack main.py --name "SistemaHorarios" --add-data "ui/assets;ui/assets" --icon ui/assets/icono.ico --hidden-import pymysql --hidden-import fitz --hidden-import sqlalchemy.dialects.mysql.pymysql --hidden-import reportlab.graphics --hidden-import reportlab.lib --product-name "Sistema de Horarios" --product-version "1.0.0" --copyright "2026 Marcos David Chino"

if %errorlevel% equ 0 (
    echo =======================================================
    echo [OK] Compilacion completada con exito.
    echo El ejecutable esta en: dist\SistemaHorarios.exe
    echo.
    echo [IMPORTANTE] Copie el archivo .env a la carpeta dist\
    echo junto a SistemaHorarios.exe antes de ejecutarlo.
    echo =======================================================
) else (
    echo =======================================================
    echo [ERROR] Ocurrio un error durante la compilacion.
    echo =======================================================
)

pause
