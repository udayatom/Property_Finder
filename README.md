### Run the backend, Files under Backend/Fast
    uvicorn app_colive:app --port 8001 --reload 
    uvicorn app_sza:app --port 8002 --reload  
    uvicorn app_zolo:app --port 8003 --reload 

### Databases placed in Backend/DB

### Start chainlit 
    chainlit run BotChain_Colive.py -w --port 8004
    chainlit run BotChain_Stanza.py -w --port 8005
    chainlit run BotChain_Zolo.py -w --port 8006

### Ollama run
ollama run llama3:latest
Notes:
Previous version written into flask, But faced the issue due to call the web page call of the google map. Because flask doesn't handle async calls. But Fast API Handles.
