import requests
import functools
from openai import OpenAI

def handle_file_not_found_error(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError:
            return f"Current working directory is: {args[0].get_work_dir()}"
    return wrapper

def test_openai_api(api_key):
    client = OpenAI(api_key=api_key)
    try:
        response = client.chat.completions.create(
                    model="gpt-3.5-turbo-1106",
                    messages=[{"role": "user", "content": "Test prompt"}],
                    max_tokens=10,
                )
        print(response)
        return True

    except Exception as e:
        print("OpenAI API is not working")
        return False


def query_pythia(pdb_file):
    try:
        with open(pdb_file, "r") as infile:
            status = "OK"
    except:
        return "wrong file!"
    headers = {'accept': 'application/json',}
    params = {'output_format': '2col','energy_threshold': '1',}
    files = {'file': open(pdb_file, 'rb'),}
    response = requests.post(
        'https://u48777-a763-8569dc34.westa.seetacloud.com:8443/scan/',
        params=params,
        headers=headers,
        files=files,
    )
    if response.status_code != 200:
        return "wrong file!"
    return response.text