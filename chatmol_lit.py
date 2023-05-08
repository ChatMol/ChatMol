import requests
import json
from pymol import cmd

def query_qaserver(question):
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    data = 'question=' + question.replace('"','')

    response = requests.post('https://chatmol.org/qa/answer/', headers=headers, data=data)
    return response.text

def chatlit(question):
    answer = query_qaserver(question)
    data = json.loads(answer)
    commands = data['answer']
    commands = commands.split('\n')
    for command in commands:
        if command == '':
            continue
        else:
            cmd.do(command)
    print("Answers from ChatMol-QA: ")
    for command in commands:
        if command == '':
            continue
        else:
            print(command)


cmd.extend("chatlit", chatlit)