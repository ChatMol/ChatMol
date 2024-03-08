# ChatMol Python Package

ChatMol is a Python package that provides a seamless integration of large language models into PyMOL, enabling users to interact with PyMOL using natural language instructions. This robust tool simplifies PyMOL tasks and offers suggestions, explanations, and guidance on a wide range of PyMOL-related topics. ChatMol provides various interaction modes with PyMOL, including the PyMOL command line, Python, miniGUI chatbot, and web browsers.

## Installation

```bash
pip install chatmol
```

## Usage

Here are some examples of how to use the package:

```python
import chatmol as cm
output_chatmol_llm = cm.chatlite("download chain A of 3wzm and color it by secondary structure") # use the chatmol llm, free and no API key required
print(output_chatmol_llm)
```

```python
print(cm.defaul_client.gpt_model) # check the current ChatGPT model
output_chatgpt = cm.chat_with_gpt("download 4eb0 and highlight residue number 208") # use the GPT-3.5-turbo llm, API key required
print(output_chatgpt)
```

```python
print(cm.defaul_client.claude_model) # check the current Claude model
output_claude = cm.chat_with_claude("download 1pga from rcsb and show a transprant surface") # use the claude llm, API key required
print(output_claude)
```

You can send results to PyMOL:

```python
import chatmol as cm
ps = cm.start_pymol() # open a PyMOL session with XML-RPC server
ps.chatlite("download 1pga")

# send commands to PyMOL
ps.server.do("esmfold MTYKLILNGKTLKGETTTEAVDAATAEKVFKQYANDNGVDGEWTYDDATKTFTVTE, 1pga_esmfold") # make sure you have pymolfold plugin installed
```

enjoy!