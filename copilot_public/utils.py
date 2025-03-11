import requests
import inspect
import functools
import streamlit as st
from openai import OpenAI

def handle_file_not_found_error(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError:
            return f"Encountered FileNotFoundError! Current working directory is: {args[0].get_work_dir()}"
    return wrapper

def function_args_to_streamlit_ui(func, args=None, tool_call_id=None):
    # clicked = False
    signature = inspect.signature(func)
    docstring = inspect.getdoc(func)
    if docstring:
        st.write(docstring)
    args_values = {}
    for name, param in signature.parameters.items():
        if param.annotation is str:
            if name == "seq":
                args_values[name] = st.text_area(name, key=f"{tool_call_id}_{name}", value=args[name] if name in args else None)
            else:
                args_values[name] = st.text_input(name, key=f"{tool_call_id}_{name}", value=args[name] if name in args else None)
        elif param.annotation is int:
            args_values[name] = st.number_input(name, key=f"{tool_call_id}_{name}", value=args[name] if name in args else None)
        else:
            args_values[name] = st.text_input(name, key=f"{tool_call_id}_{name}", value=args[name] if name in args else None)
    # while not clicked:
    if st.button('Submit'):
            # clicked = True
        print(args_values)
        result = func(**args_values)
        st.write(result)
        return result
        # else:
        #     st.write("Waiting for submission...")
            

def test_openai_api(api_key):
    client = OpenAI(api_key=api_key)
    try:
        response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": "Test prompt"}],
                    max_tokens=10,
                )
        print(response)
        return True

    except Exception as e:
        print("OpenAI API is not working")
        return False
    
def test_ds_api(api_key):
    client = OpenAI(api_key=api_key)
    try:
        response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "user", "content": "Test prompt"}],
                    max_tokens=10,
                )
        print(response)
        return True

    except Exception as e:
        print("DeepSeek API is not working")
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
        # 'https://u48777-a763-8569dc34.westa.seetacloud.com:8443/scan/',
        'https://api.cloudmol.org/protein/pythia_scan/',
        params=params,
        headers=headers,
        files=files,
    )
    if response.status_code != 200:
        return "wrong file!"
    return response.text