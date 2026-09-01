@echo off
if not exist venv py -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt
if not exist .env copy .env.example .env
venv\Scripts\python.exe app.py
