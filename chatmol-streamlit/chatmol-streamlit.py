import streamlit as st
import chatmol as cm

st.sidebar.title("ChatMol")
st.sidebar.markdown("Welcome to ChatMol! ChatMol is a tool that allows you to interact with PyMOL using natural language.")

openai_llms = ['gpt-4o', 'gpt-4-turbo', 'gpt-3.5-turbo']
claude_llms = ['claude-3-5-sonnet-20240620', 'claude-3-sonnet-20240229', 'claude-3-haiku-20240307', 'claude-3-opus-20240229']
chatmol_llms = ['chatlite']

introduction_of_models = {
    'gpt-4o': "GPT-4o (“o” for “omni”) is most advanced model of OpenAI. It has the same high intelligence as GPT-4 Turbo but is much more efficient—it generates text 2x faster and is 50% cheaper.",
    'gpt-4-turbo': "GPT-4 can solve difficult problems with greater accuracy than any of previous models of OpenAI, thanks to its broader general knowledge and advanced reasoning capabilities.",
    'gpt-3.5-turbo': "GPT-3.5 Turbo models can understand and generate natural language or code and have been optimized for chat.",
    'chatlite': "A model provided by ChatMol freely available to all, which is optimized for PyMOL commands generation but not good for general chat.",
    'claude-3-5-sonnet-20240620': "Most intelligent model of Anthropic, combining top-tier performance with improved speed. Currently the only model in the Claude 3.5 family.\n - Advanced research and analysis\n - Complex problem-solving\n - Sophisticated language understanding and generation\n - High-level strategic planning",
    'claude-3-sonnet-20240229': "Balances intelligence and speed for high-throughput tasks.\n - Data processing over vast amounts of knowledge\n - Sales forecasting and targeted marketing\n - Code generation and quality control",
    'claude-3-haiku-20240307': "Near-instant responsiveness that can mimic human interactions.\n - Live support chat\n - Translations\n - Content moderation\n - Extracting knowledge from unstructured data",
    'claude-3-opus-20240229': "Strong performance on highly complex tasks, such as math and coding.\n - Task automation across APIs and databases, and powerful coding tasks\n - R&D, brainstorming and hypothesis generation, and drug discovery\n - Strategy, advanced analysis of charts and graphs, financials and market trends, and forecasting"
}

if "ps" not in st.session_state:
    st.session_state["cm"] = cm
    if st.button("Start PyMOL"):
        st.session_state["ps"] = cm.start_pymol_gui()

if "available_llms" not in st.session_state:
    st.session_state["available_llms"] = []
    if st.session_state["cm"].defaul_client.client is not None:
        st.session_state["available_llms"].extend(openai_llms)
    st.session_state["available_llms"].extend(chatmol_llms)
    if st.session_state["cm"].defaul_client.client_anthropic is not None:
        st.session_state["available_llms"].extend(claude_llms)

if "llm" not in st.session_state:
    st.session_state["llm"] = ''
    
st.session_state["llm"] = st.sidebar.selectbox("Select LLM", st.session_state["available_llms"])

st.sidebar.write(introduction_of_models.get(st.session_state["llm"], "No introduction available"))

if st.session_state["llm"] in openai_llms+claude_llms:
    if st.sidebar.button("check api availability"):
        with st.spinner("Checking..."):
            results = st.session_state["cm"].defaul_client.test_api_access()
        for k, v in results.items():
            if v:
                st.sidebar.info(v)
            else:
                st.sidebar.info(f"{k.split('_')[0]} is available")

if "messages" not in st.session_state:
    st.session_state['messages'] = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if prompt := st.chat_input("What is up?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.spinner("Thinking..."):
        pymol_console = st.session_state["ps"].pymol_console
        if prompt.endswith("?"):
            if st.session_state["llm"] in openai_llms:
                response = st.session_state["cm"].chat_with_gpt(f"This is the log: \n\n{st.session_state['ps'].pymol_console}\n\n. This is my question: \n\n{prompt}")
            elif st.session_state["llm"] in claude_llms:
                response = st.session_state["cm"].chat_with_claude(f"This is the log: \n\n{st.session_state['ps'].pymol_console}\n\n. This is my question: \n\n{prompt}")
            elif st.session_state["llm"] in chatmol_llms:
                response = st.session_state["cm"].chatlite(f"This is the log: \n\n{st.session_state['ps'].pymol_console}\n\n. This is my question: \n\n{prompt}")
        else:
            if st.session_state["llm"] in openai_llms:
                response = st.session_state["ps"].chatgpt(f"This is the log: \n\n{st.session_state['ps'].pymol_console}\n\n. This is my instruction: \n\n{prompt}")
            elif st.session_state["llm"] in claude_llms:
                response = st.session_state["ps"].claude(f"This is the log: \n\n{st.session_state['ps'].pymol_console}\n\n. This is my instruction: \n\n{prompt}")
            elif st.session_state["llm"] in chatmol_llms:
                response = st.session_state["ps"].chatlite(f"This is the log: \n\n{st.session_state['ps'].pymol_console}\n\n. This is my instruction: \n\n{prompt}")
    
        st.session_state.messages.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        response = st.write(response)