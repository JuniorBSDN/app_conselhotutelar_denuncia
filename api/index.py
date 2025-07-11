from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore
import os, json
import requests

app = Flask(__name__)
CORS(app)

# Inicializa Firebase
if not firebase_admin._apps:
    try:
        firebase_json = os.environ.get("FIREBASE_CREDENTIALS")
        cred_dict = json.loads(firebase_json)
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        print("Erro Firebase:", e)

db = firestore.client()
colecao = 'dbdenuncia'

# Envia e-mail via SendGrid
def enviar_email(destinatario, nome):
    try:
        sendgrid_key = os.environ.get("SENDGRID_API_KEY")
        payload = {
            "personalizations": [{
                "to": [{"email": destinatario}],
                "subject": "Confirmação de Denúncia"
            }],
            "from": {"email": "noreply@conselhotutelar.com"},
            "content": [{
                "type": "text/plain",
                "value": f"Olá {nome},\n\nRecebemos sua denúncia e ela está sendo analisada.\n\nConselho Tutelar."
            }]
        }
        headers = {
            "Authorization": f"Bearer {sendgrid_key}",
            "Content-Type": "application/json"
        }
        response = requests.post("https://api.sendgrid.com/v3/mail/send", headers=headers, json=payload)
        print("Email enviado:", response.status_code)
    except Exception as e:
        print("Erro ao enviar e-mail:", e)

# Envia WhatsApp via Twilio
def enviar_whatsapp(destino, nome):
    try:
        from twilio.rest import Client
        account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
        from_number = os.environ.get("TWILIO_WHATSAPP_NUMBER")
        client = Client(account_sid, auth_token)
        mensagem = f"Olá {nome}, recebemos sua denúncia. Obrigado por entrar em contato com o Conselho Tutelar."
        client.messages.create(
            body=mensagem,
            from_=from_number,
            to=f"whatsapp:{destino}"
        )
        print("WhatsApp enviado")
    except Exception as e:
        print("Erro WhatsApp:", e)

@app.route("/denuncias", methods=["POST"])
def receber_denuncia():
    try:
        dados = request.json
        dados['dataEnvio'] = firestore.SERVER_TIMESTAMP
        doc_ref = db.collection(colecao).add(dados)

        nome = dados.get("nome")
        contato = dados.get("contato")

        # Enviar e-mail e WhatsApp se possível
        if "@" in contato:
            enviar_email(contato, nome)
        elif contato.isdigit() or contato.startswith("+"):
            enviar_whatsapp(contato, nome)

        return jsonify({"status": "sucesso", "id": doc_ref[1].id}), 201
    except Exception as e:
        print("Erro geral:", e)
        return jsonify({"status": "erro", "mensagem": str(e)}), 500
