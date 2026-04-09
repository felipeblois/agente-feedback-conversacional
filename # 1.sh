# 1. Crie o ambiente virtual
make setup

# 2. Ative o ambiente virtual
source .venv/bin/activate

# 3. Crie o banco de dados via Alembic
make db

# 4. (Opcional) Gere dados de demonstração
make seed

# 5. Salve tudo na sua branch de desenvolvimento
git add .
git commit -m "feat: implementação completa das atividades até Passo 14"
git push

# 6. Teste e veja a aplicação rodando!
make run

O comando make run subirá o backend em http://localhost:8000 e o painel Streamlit em http://localhost:8501 em background pra você testar.

🚀 Iniciando backend e Streamlit...
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload &
.venv/bin/python -m streamlit run streamlit_app/Home.py --server.port 8501 &
✅ Backend: http://localhost:8000
✅ Admin:   http://localhost:8501
📖 API Docs: http://localhost:8000/docs
(.venv) root@DESKTOP-E2RJ2RQ:/mnt/c/Users/felip/Documents/projeto_1/agente-feedback-conversacional# INFO:     Will watch for changes in these directories: ['/mnt/c/Users/felip/Documents/projeto_1/agente-feedback-conversacional']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [1707] using WatchFiles

Collecting usage statistics. To deactivate, set browser.gatherUsageStats to false.


  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.1.108:8501
  External URL: http://45.189.161.104:8501
