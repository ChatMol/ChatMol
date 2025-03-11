from openai import OpenAI
import subprocess
import streamlit as st
import chatmol_fn as cfn_
from stmol import showmol
from streamlit_float import *
from viewer_utils import show_pdb
from utils import test_openai_api, function_args_to_streamlit_ui, test_ds_api
from streamlit_molstar import st_molstar
import hashlib
import new_function_template
import shutil
from chat_helper import ConversationHandler, compose_chat_completion_message
import os
import json
import pickle
import re
import streamlit_analytics

m = hashlib.sha256()
st.set_page_config(layout="wide")
st.session_state.new_added_functions = []

# Command to start the server
if "file_sever" not in st.session_state:
    command = "python3 -m http.server 3333"
    subprocess.Popen(command, shell=True)
    st.session_state.file_sever = True

pattern = r"<chatmol_sys>.*?</chatmol_sys>"
# wide
if "function_queue" not in st.session_state:
    st.session_state["function_queue"] = []

if "cfn" in st.session_state:
    cfn = st.session_state["cfn"]
else:
    cfn = cfn_.ChatmolFN()
    st.session_state["cfn"] = cfn

st.title("ChatMol Copilot", anchor="center")
st.sidebar.write("2025 Mar 11 public version")
st.sidebar.write(
    "ChatMol copilot is a AI platform for protein engineering, molecular design and computation. Also chekcout our [GitHub](https://github.com/ChatMol/ChatMol)."
)
st.write("The LLM Powered Agent for Protein Modeling and Molecular Computation 🤖️ 🧬")
float_init()

st.sidebar.title("Settings")
mode = st.sidebar.selectbox("Mode", ["automatic", "manual"], index=0)
with streamlit_analytics.track():
    project_id = st.sidebar.text_input("Project Name", "Project-X")
openai_api_key = st.sidebar.text_input("OpenAI API key", type="password")

try:
    openai_api_key = os.getenv("OPENAI_API_KEY", openai_api_key)
except:
    print("No OPENAI_API_KEY found in environment variables")

if project_id + str(openai_api_key) == "Project-X":
    st.warning(
        "Please change the project name to your own project name, and provide your own OpenAI API key."
    )
    st.stop()

model = st.sidebar.selectbox(
    "Model",
    ["gpt-4o",  "gpt-4o-mini",  "deepseek-chat"],
)
st.session_state["openai_model"] = model

if st.session_state["openai_model"].startswith("gpt"):
    if "api_key" in st.session_state:
        api_key_test = st.session_state["api_key"]
        if st.session_state.api_key is False:
            # api_key_test = True
            api_key_test = test_openai_api(openai_api_key)
            st.session_state.api_key = api_key_test
            if api_key_test is False:
                st.warning(
                    "The provided OpenAI API key seems to be invalid. Please check again. If you don't have an OpenAI API key, please visit https://platform.openai.com/ to get one."
                )
                st.stop()
    else:
        # api_key_test = True
        api_key_test = test_openai_api(openai_api_key)
        st.session_state["api_key"] = api_key_test

elif st.session_state["openai_model"].startswith("deepseek"):
    openai_api_key = os.getenv("DEEPSEEK_API_KEY", openai_api_key)
    if "api_key" in st.session_state:
        api_key_test = st.session_state["api_key"]
        if st.session_state.api_key is False:
            # api_key_test = True
            api_key_test = test_ds_api(openai_api_key)
            st.session_state.api_key = api_key_test
            if api_key_test is False:
                st.warning(
                    "The provided DeepSeek API key seems to be invalid. Please check again. If you don't have an DeepSeek API key, please visit https://api-docs.deepseek.com/ to get one."
                )
                st.stop()
    else:
        # api_key_test = True
        api_key_test = test_ds_api(openai_api_key)
        st.session_state["api_key"] = api_key_test
else:
    st.warning("Please select a valid model.")
    st.stop()

m.update((openai_api_key + project_id).encode())
hash_string = m.hexdigest()

# try to bring back the previous session
work_dir = f"./{project_id}"
cfn.WORK_DIR = work_dir

if st.sidebar.button("Clear Project History"):
    if os.path.exists(f"./{work_dir}"):
        shutil.rmtree(f"./{work_dir}")
        st.session_state.messages = []
        st.session_state.function_queue = []
        st.session_state.new_added_functions = []
        st.session_state.cfn = cfn_.ChatmolFN()


# button_1, button_2 = st.columns([1, 1])
if st.sidebar.button("Show/Hide Mol*"):
    if (st.session_state.get('molstar',True)):
        st.session_state['molstar'] = False
        _, chatcol, _ = st.columns([1, 3, 1])
    else:
        chatcol, displaycol = st.columns([1, 1])
        st.session_state['molstar'] = True

if not os.path.exists(work_dir):
    os.makedirs(work_dir)
if os.path.exists(f"{work_dir}/.history"):
    with open(f"{work_dir}/.history", "rb") as f:
        st.session_state.messages = pickle.load(f)

if model.startswith("gpt"):
    client = OpenAI(api_key=openai_api_key)
else:
    client = OpenAI(api_key=openai_api_key, base_url="https://api.deepseek.com")

conversation = ConversationHandler(client, cfn, model_name=model)

# if load_example := st.sidebar.selectbox("Load example (this overrides your current history)", ["", "enzyme for toxin degradation"]):
#     if load_example == "enzyme for toxin degradation":
#         shutil.rmtree(work_dir)
#         shutil.copytree("examples/enzyme-for-toxin-degradation", work_dir)
#         # work_dir_h "examples/enzyme-for-toxin-degradation"
#         with open(f"{work_dir}/.history", "rb") as f:
#             st.session_state.messages = pickle.load(f)

# if add_translator := st.sidebar.checkbox("Add translator"):
#     def translate_to_protein(self, seq:str, pname=None):
#         from Bio.Seq import Seq
#         nucleotide_seq = Seq(seq)
#         protein_seq = nucleotide_seq.translate()
#         if pname:
#             return f"The protein sequence of {seq} is `>protein\n{protein_seq}`\n{pname}"
#         else:
#             return f"The protein sequence of {seq} is `>protein\n{protein_seq}`"

#     cfn.translate_to_protein = translate_to_protein.__get__(cfn)

#     conversation.tools.append(
#         {
#             "type": "function",
#             "function": {
#                 "name": "translate_to_protein",
#                 "description": "Translate a DNA/RNA sequence to a protein sequence",
#                 "parameters": {
#                     "type": "object",
#                     "properties": {
#                         "seq": {"type": "string", "description": "The DNA/RNA sequence"},
#                     },
#                 },
#                 "required": ["seq"],
#             },
#         }
#     )
#     conversation.available_functions["translate_to_protein"] = cfn.translate_to_protein

if add_from_template := st.sidebar.checkbox("Add from template"):
    function_info = new_function_template.get_info()
    descriptions = function_info['descriptions']
    new_funcs = function_info['functions']
    test_data = new_function_template.test_data
    for description, new_func in zip(descriptions, new_funcs):
        try:
            #test_results = new_function_template.test_new_function(new_func, description['function']['name'], test_data)
            conversation.tools.append(description)
            conversation.available_functions[description['function']['name']] = new_func.__get__(cfn)
            if description['function']['name'] not in st.session_state.new_added_functions:
                st.sidebar.success(f"Function `{description['function']['name']}` added successfully.")
                st.session_state.new_added_functions.append(description['function']['name'])
        except Exception as e:
            st.warning(f"Failed to add function from template. Error: {e}")

if add_from_registry := st.sidebar.checkbox("Add from registry"):
    try:
        import new_function_registry
        function_info = new_function_registry.get_info()
        descriptions = function_info['descriptions']
        new_funcs = function_info['functions']
        test_data = new_function_registry.test_data
        for description, new_func in zip(descriptions, new_funcs):
            try:
                #test_results = new_function_registry.test_new_function(new_func, description['function']['name'], test_data)
                conversation.tools.append(description)
                conversation.available_functions[description['function']['name']] = new_func.__get__(cfn)
                if description['function']['name'] not in st.session_state.new_added_functions:
                    st.sidebar.success(f"Function `{description['function']['name']}` added successfully.")
                    st.session_state.new_added_functions.append(description['function']['name'])
            except Exception as e:
                st.sidebar.warning(f"Failed to add function from template. Error: {e}")
    except Exception as e:
        st.sidebar.warning(f"Failed to add functions from registry. Check your access to the registry server.")
        print(f"Failed to add functions from registry. Error: {e}")
    print("Add from registry is on")

available_functions = conversation.available_functions
available_tools = conversation.tools
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = model

if "messages" not in st.session_state or st.session_state.messages == []:
    st.session_state.messages = [
        {
            "role": "system",
            "content": f"You are ChatMol copilot, a helpful copilot in molecule analysis with tools. You think step-by-step before you conclude correctly. Use tools only when you need them. Answer to questions related molecular modelling. When providing file path for downloading, use the realpath of the file without modification, it should be looks like: [link name](http://localhost:3333/work_dr/filename.suffix), the current work_dir is {work_dir}",
        }
    ]
    if st.session_state.openai_model.startswith("glm"):
        st.session_state.messages[0]["content"] += " Do not show details of function callings. Make sure you use correct file path all the time."

chatcol, displaycol = st.columns([1, 1])


with chatcol:
    for message in st.session_state.messages:
        try:
            if message["role"] != "system" and message["role"] != "tool":
                cleaned_string = re.sub(
                    pattern, "", message["content"], flags=re.DOTALL
                )
                if cleaned_string != "":
                    with st.chat_message(message["role"]):
                        st.markdown(cleaned_string)
        except:
            if message.role != "system" and message.role != "tool":
                cleaned_string = re.sub(pattern, "", message.content, flags=re.DOTALL)
                if cleaned_string != "":
                    with st.chat_message(message.role):
                        st.markdown(cleaned_string)
    function_called = False

    for tool_call in st.session_state.function_queue:
        if tool_call["status"] == "pending":
            function_called = True
            # with st.chat_message("assistant"):
                # st.write(f"Please provide arguments for {tool_call['name']}")
            try:
                function_name = tool_call["name"]
                function_to_call = tool_call["func"]
                function_args = json.loads(tool_call["args"])
            except Exception as e:
                print(f"The error is:\n{e}")
                print("Error in function_args")

            try:
                function_response = function_to_call(**function_args)
                if function_response:
                    st.session_state.messages.append(
                        {
                            "tool_call_id": tool_call["tool_call_id"],
                            "role": "tool",
                            "name": function_name,
                            "content": function_response,
                        }
                    )
                    tool_call["status"] = "done"
                    
            except Exception as e:
                print(f"The error is:\n{e}")
                print("Error in function_response")
                st.session_state.messages.append(
                    {
                        "tool_call_id": tool_call["tool_call_id"],
                        "role": "tool",
                        "name": function_name,
                        "content": f"error: {e}",
                    }
                )
                tool_call["status"] = "done"
    if function_called:
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            for response in client.chat.completions.create(
                model=st.session_state["openai_model"],
                messages=st.session_state.messages,
                stream=True,
            ):
                full_response += response.choices[0].delta.content or ""
                message_placeholder.markdown(full_response)
    
for i_, mx in enumerate(st.session_state.messages):
    print(i_)
    print(mx)

if prompt := st.chat_input("What is up?"):
    with chatcol:
        if os.path.exists(f"{work_dir}/.workspace"):
            chatmol_sys_info = open(f"{work_dir}/.workspace", "r").read()
            prompt += chatmol_sys_info
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            cleaned_string = re.sub(pattern, "", prompt, flags=re.DOTALL)
            st.markdown(cleaned_string)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            tool_calls = []
            tool_call = None
            for response in client.chat.completions.create(
                model=st.session_state["openai_model"],
                messages=st.session_state.messages,
                stream=True,
                tools=available_tools,
                tool_choice="auto",
            ):
                full_response += response.choices[0].delta.content or ""
                message_placeholder.markdown(full_response + "▌")
                tool_call_chunk_list = response.choices[0].delta.tool_calls
                if tool_call_chunk_list:
                    for tool_call_chunk in tool_call_chunk_list:
                        if len(tool_calls) <= tool_call_chunk.index:
                            tool_calls.append(
                                {
                                    "id": "",
                                    "type": "function",
                                    "function": {"name": "", "arguments": ""},
                                }
                            )
                        tool_call = tool_calls[tool_call_chunk.index]
                        if tool_call_chunk.id:
                            tool_call["id"] += tool_call_chunk.id
                        if tool_call_chunk.function.name:
                            tool_call["function"][
                                "name"
                            ] += tool_call_chunk.function.name
                        if tool_call_chunk.function.arguments:
                            tool_call["function"][
                                "arguments"
                            ] += tool_call_chunk.function.arguments
            function_response = ""
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": full_response,
                }
            )
            print("Debug: Full response from assistant", full_response)
            with open(f"{work_dir}/workspace", "a") as f:
                f.write(full_response)

            if tool_call:
                st.session_state.messages = st.session_state.messages[:-1]
                if st.session_state.openai_model == "glm-4":
                    response_message = {
                        "role": "assistant",
                        "content": full_response,
                        "tool_calls": tool_calls,
                    }
                else:
                    response_message = compose_chat_completion_message(
                        role="assistant",
                        content=full_response,
                        tool_call_dict_list=tool_calls,
                    )
                st.session_state.messages.append(response_message)
                if mode == "automatic":
                    for tool_call in tool_calls:
                        function_name = tool_call["function"]["name"]
                        function_to_call = available_functions[function_name]
                        try:
                            function_args = json.loads(tool_call["function"]["arguments"])
                            if st.session_state["openai_model"].startswith("glm"):
                                function_args = json.loads(tool_call["function"]["arguments"]['content'])
                            function_response = function_to_call(**function_args)
                            if function_response:
                                st.session_state.messages.append(
                                    {
                                        "tool_call_id": tool_call["id"],
                                        "role": "tool",
                                        "name": function_name,
                                        "content": function_response,
                                    }
                                )
                        except Exception as e:
                            print(f"The error is:\n{e}")
                            st.session_state.messages.append(
                                {
                                    "tool_call_id": tool_call["id"],
                                    "role": "tool",
                                    "name": function_name,
                                    "content": f"error: {e}",
                                }
                            )

                if mode == "manual":
                    print("manual mode")
                    for tool_call in tool_calls:
                        function_name = tool_call["function"]["name"]
                        function_to_call = available_functions[function_name]
                        function_arg_string = tool_call["function"]["arguments"]
                        st.session_state.function_queue.append(
                            {
                                "tool_call_id": tool_call["id"],
                                "role": "tool",
                                "name": function_name,
                                "func": function_to_call,
                                "args": function_arg_string,
                                "status": "pending",
                                "content": "",
                            }
                        )
                    for tool_call in st.session_state.function_queue:
                        if tool_call["status"] == "pending":
                            try:
                                function_args = json.loads(function_arg_string)
                                function_response = function_args_to_streamlit_ui(function_to_call, function_args, tool_call["tool_call_id"])
                                print(function_response)
                                if function_response:
                                    st.session_state.messages.append(
                                        {
                                            "tool_call_id": tool_call["tool_call_id"],
                                            "role": "tool",
                                            "name": function_name,
                                            "content": function_response,
                                        }
                                    )
                                    tool_call["status"] = "done"
                            except Exception as e:
                                print(f"The error is:\n{e}")
                                st.session_state.messages.append(
                                    {
                                        "tool_call_id": tool_call["tool_call_id"],
                                        "role": "tool",
                                        "name": function_name,
                                        "content": f"error: {e}",
                                    }
                                )
                                tool_call["status"] = "done"
                if function_response:
                    print(st.session_state.messages)
                    for response in client.chat.completions.create(
                        model=st.session_state["openai_model"],
                        messages=st.session_state.messages,
                        # tool_choice="auto",
                        stream=True,
                    ):
                        full_response += response.choices[0].delta.content or ""
                        message_placeholder.markdown(full_response)
                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": full_response,
                        }
                    )
                    print("Debug: Full response from tool calling", full_response)

                message_placeholder.markdown(full_response)
uploaded_file = st.sidebar.file_uploader("Upload PDB file", type=["pdb"])

if uploaded_file:
    chatmol_system_prompt = f" <chatmol_sys> File path information: The path to protein uploaded is {work_dir}/{uploaded_file.name}, the workdir is {work_dir} </chatmol_sys>"
    with open(f"{work_dir}/.workspace", "w+") as f:
        f.write(chatmol_system_prompt)
    pdb_id = uploaded_file.name.split(".")[0]
    pdb_file = f"{cfn.WORK_DIR}/{pdb_id}.pdb"
    with open(pdb_file, "wb") as f:
        f.write(uploaded_file.getbuffer())

    pdb_string = "\n".join(
        [
            x
            for x in uploaded_file.getvalue().decode("utf-8").split("\n")
            if x.startswith("ATOM") or x.startswith("HETATM")
        ]
    )
    view = show_pdb(
        pdb_str=pdb_string,
        color=color_options["Rainbow"],
        show_sidechains=False,
        show_ligands=True,
        show_mainchains=False,
    )

    cfn.VIEW_DICTS[pdb_id] = view

if "molstar" in st.session_state and st.session_state["molstar"] == False:
    pass
else:
    with displaycol:
        container = st.container()
        with container:
            col1, col2 = st.columns([1, 1])
            with col1:
                viewer_selection = st.selectbox(
                    "Select a viewer", options=["molstar", "py3Dmol"], index=0
                )
            if viewer_selection == "molstar":
                pdb_files = [f for f in os.listdir(cfn.WORK_DIR) if f.endswith(".pdb")]
                if len(pdb_files) > 0:
                    with col2:
                        pdb_file = st.selectbox(
                            "Select a pdb file", options=pdb_files, index=0
                        )
                    st_molstar(f"{cfn.WORK_DIR}/{pdb_file}", height=500)
            # if viewer_selection == "molstar docking":
            #     st_molstar_docking(f"{cfn.WORK_DIR}/{pdb_file}", height=500)
            if viewer_selection == "py3Dmol":
                color_options = {
                    "Confidence": "pLDDT",
                    "Rainbow": "rainbow",
                    "Chain": "chain",
                }
                selected_color = st.sidebar.selectbox(
                    "Color Scheme", options=list(color_options.keys()), index=0
                )
                # print(selected_color)
                show_sidechains = st.sidebar.checkbox("Show Sidechains", value=False)
                show_mainchains = st.sidebar.checkbox("Show Mainchains", value=False)
                show_ligands = st.sidebar.checkbox("Show Ligands", value=True)
                if len(cfn.VIEW_DICTS) > 0:
                    with col2:
                        select_view = st.selectbox(
                            "Select a view", options=list(cfn.VIEW_DICTS.keys()), index=0
                        )
                    view = cfn.VIEW_DICTS[select_view]
                    showmol(view, height=400, width=500)
            float_parent()

with open(f"{work_dir}/.history", "wb") as f:
    pickle.dump(st.session_state.messages, f)
