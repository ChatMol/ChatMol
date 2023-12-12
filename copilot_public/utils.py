import requests
import functools

def handle_file_not_found_error(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError:
            return f"Current working directory is: {args[0].get_work_dir()}"
    return wrapper

def test_openai_api(api_key):
    url = "https://api.openai.com/v1/engines/davinci-codex/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "prompt": "Test prompt",
        "max_tokens": 10
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return True
    else:
        print(response)
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