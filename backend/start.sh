#!/bin/bash
mkdir -p ./data/chroma_db
python -m spacy download en_core_web_sm
exec gunicorn app.main:app -w 2 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
