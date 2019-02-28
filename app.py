from __future__ import print_function

import json

import dict_digger
import watson_developer_cloud
from flask import Flask, redirect, request
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

global workspace_id
workspace_id = '{your assistant workspace/skill id}'

global assistant_id
assistant_id = '{your assistant id}'


def create_assistant():
    global assistant

    assistant = watson_developer_cloud.AssistantV2(
        username='{your assistant username}',
        password='{your assistant password}',
        version='2018-07-10',
        url='https://gateway.watsonplatform.net/assistant/api')
    assistant.set_detailed_response(True)


def create_session(workspace_id, assistant_id, assistant):
    global session

    print("####----------Session Start-----------####")

    session = assistant.create_session(
        workspace_id=workspace_id,
        assistant_id=assistant_id,
        input={
            'message_type': 'text',
            'text': ''
        },
    ).get_result()

    print(json.dumps(session, indent=2))

    json_string = json.dumps(session)
    json_dict = json.loads(json_string)
    global session_id
    session_id = json_dict.get("session_id")


@app.route("/")
def index():
    return '<a href="/zap">ZAP</a>'


@app.route("/zap", methods=['GET', 'POST'])
def sms_start():

    # Pega os parâmetros provindos do Twilio
    from_number = request.values.get('From')
    message_body = request.values.get('Body')
    to_number = request.values.get('To')

    # Instancia servico Twilio
    account_sid = '{your twilio service id}'
    auth_token = '{your twilio auth token}'

    twilio_client = Client(account_sid, auth_token)

    # print(request.values)

    try:
        assistant
    except UnboundLocalError:
        # instancia serviço do waston assistant caso não tenha sido
        create_assistant()
    except NameError:
        create_assistant()

    try:
        session
    except UnboundLocalError:
        # instancia sessão de conversa caso não tenha sido
        create_session(workspace_id, assistant_id, assistant)
    except NameError:
        create_session(workspace_id, assistant_id, assistant)

    # Inicializa variáveis utilizadas pelo chat
    user_input = ''
    context = {}
    current_action = ''

    # Principal loop de entrada/saída:
    while current_action != 'end_conversation':
        while True:
            # Captura mensagem do cliente para o chatbot
            response = assistant.message(
                workspace_id=workspace_id,
                assistant_id=assistant_id,
                session_id=session_id,
                input={
                    'text': message_body},
                context=context).get_result()  # Gera resposta do chatbot

            # INICIO FUNÇOES DE LOG
            print("####----------Round Start-----------####")
            print("INPUT")
            print("      Mensagem de " + from_number +
                  ": '" + message_body + "'")
            if len(dict_digger.dig(response, 'output', 'intents')) != 0:
                print("      Intenções: " +
                      str(dict_digger.dig(response, 'output', 'intents', 0, 'intent')))
                if 'General_Ending' == dict_digger.dig(response, 'output', 'intents', 0, 'intent'):
                    current_action = 'end_conversation'
                    print(current_action)

            if len(dict_digger.dig(response, 'output', 'entities')) != 0:
                print("      Entidades: " +
                      str(dict_digger.dig(response, 'output', 'entities', 0, 'entity')))

            print("      Contexto: " + str(dict_digger.dig(response, 'context')))
            # FIM FUNÇOES DE LOG

            # INICIO FUNÇOES DE LOG
            print("OUTPUT")

            if len(dict_digger.dig(response, 'output', 'intents')) != 0:
                print("      Intenções: " +
                      str(dict_digger.dig(response, 'output', 'intents', 0, 'intent')))

            if len(dict_digger.dig(response, 'output', 'entities')) != 0:
                print("      Entidades: " +
                      str(dict_digger.dig(response, 'output', 'entities', 0, 'entity')))

            print("      Contexto: " + str(dict_digger.dig(response, 'context')))

            reponse_text = str(dict_digger.dig(
                response, 'output', 'generic', 0, 'text'))
            print("      Resposta do Bot: '" + reponse_text + "'")
            # FIM FUNÇOES DE LOG

            # instancia resposta no twilio
            resp = MessagingResponse()

            # Define mensagem de resposta twilio
            resp.message(reponse_text)

            # Atualize o contexto armazenado com o recebido mais recentemente do diálogo.
            context = dict_digger.dig(response, 'context')
            print("####----------Round End-----------####")

            # envia respota twilio
            return str(resp)

    # Finaliza sessão de conversa em caso de intenção de despedida
    if current_action == 'end_conversation':
        print("####----------Session End-----------####")
        response = service.delete_session(
            assistant_id=assistant_id,
            session_id=session_id
        ).get_result()


app.run(debug=True)
