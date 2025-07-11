from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore
import os
import json

app = Flask(__name__)
CORS(app)

# Inicialização do Firebase
if not firebase_admin._apps:
    try:
        firebase_json = os.environ.get("FIREBASE_CREDENTIALS")
        if not firebase_json:
            raise Exception("Variável FIREBASE_CREDENTIALS não encontrada")
        cred_dict = json.loads(firebase_json)
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        print("Erro ao inicializar o Firebase:", e)

db = firestore.client()
colecao = 'dbdenuncia'

@app.route("/api/denuncias", methods=["POST"])
def receber_denuncia():
    try:
        dados = request.json
        dados['dataEnvio'] = firestore.SERVER_TIMESTAMP
        doc_ref = db.collection(colecao).add(dados)
        return jsonify({"status": "sucesso", "id": doc_ref[1].id}), 201
    except Exception as e:
        return jsonify({"status": "erro", "mensagem": str(e)}), 500
