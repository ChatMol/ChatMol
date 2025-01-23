# ChatMol PyMOL Plugin
This is a PyMOL plugin built by ChatMol, for automating the process of creating a biomoelcular figure in PyMOL. 

### Installation

We provide a up-to-date version of the plugin on our website. You can download the plugin from [here](https://chatmol.com/pymol_plugins/chatmol-latest.py). Or, in PyMOL command line, you can run the following command to install the plugin:

```python
load https://chatmol.com/pymol_plugins/chatmol-latest.py
```

### Supported LLM providers
| Provider  | Models               | GPU Required | API Key Required | Notes               |
| --------- | -------------------- | ------------ | ---------------- | ------------------- |
| OpenAI    | GPT Models           | No           | Yes              | Commercial API      |
| Anthropic | Claude Models        | No           | Yes              | Commercial API      |
| DeepSeek  | DeepSeek Models      | No           | Yes              | Commercial API      |
| Ollama    | LLaMA, Mixtral, etc. | Yes          | No               | Self-hosted models  |
| ChatMol   | ChatMol Model        | No           | No               | Free hosted service |

### Usage
1. The most easy way to get started is to use the `chatlite` command in PyMOL. 
```pymol
chatlite "show me a protein"
```

2. Comercial API providers
- OpenAI, Anthropic, and DeepSeek require an API key. You can get an API key from the respective provider's website.
- We suggest adding the API key to the environment variable:
```bash
export OPENAI_API_KEY=sk-proj-xxxx
export ANTHROPIC_API_KEY=sk-ant-xxxx
export DEEPSEEK_API_KEY=sk-xxxx
```
or you can use the `set_api_key` command in PyMOL:
```python
set_api_key openai, sk-proj-xxxx
set_api_key anthropic, sk-ant-xxxx
set_api_key deepseek, sk-xxxx
```
- Currently supported models are:

| **Provider** | **Models**                                                                                                |
| ------------ | --------------------------------------------------------------------------------------------------------- |
| OpenAI       | gpt-4o, gpt-4o-mini                                                                                       |
| Anthropic    | claude-3-5-sonnet-20241022, claude-3-5-haiku-20241022, claude-3-opus-20240229, claude-3-5-sonnet-20240620 |
| DeepSeek     | deepseek-chat                                                                                             |

Use `update_model` command to get the latest models from the provider.

```pymol
update_model deepseek-chat
```

Once the model and API key are set, you can use the `chat` command to generate text from the model.
```pymol
chat "show me a protein"
```

3. Self-hosted models
- Ollama provides self-hosted models. You can use any model you like, tell the plugin to use ollama models by adding `@ollama` to the model name. Refer to the [Ollama documentation](https://ollama.com/docs) for more information.
```pymol
update_model phi-4@ollama
```

### Examples

**1. ChatMol as a Task Execution Agent**

The ChatGPT Plugin automates PyMOL tasks with ease. In the PyMOL command line, just enter `chat` as the trigger word for the ChatMol plugin, followed by your PyMOL task description or questions about specific PyMOL commands. After entering your requests, a set of instructions will appear, and the commands for completing your tasks will be automatically executed by default. For example, use `chat Show me how to color a protein by its secondary structures` to view a protein molecule in the PyMOL 3D window, with colors representing its secondary structures.

![img](../assets/img_ss.png)

**2. ChatMol as a Q&A Chatbot**

ChatMol also serves as a Q&A chatbot, answering your queries about executing PyMOL tasks without actually performing the PyMOL. 
You can disable the automatic execution by adding a question mark `?` at the end of ChatMol prompt, e.g., `chat How do I align two proteins?`. You will receive a helpful response such as:
   
````
ChatGPT: To align two proteins in PyMOL, you can use the `align` command. Here's an example:

```
# Load two proteins
fetch 1ake
fetch 1ttt

# Align the two proteins
align 1ake, 1ttt

# Show the aligned proteins
show cartoon
```

In this example, we first load two proteins using the `fetch` command. If you already have the proteins loaded, you can skip this step.

Next, we use the `align` command to align the two proteins. The first argument is the reference protein (the one that will not move), and the second argument is the mobile protein (the one that will be aligned to the reference). In this case, we're aligning 1ake to 1ttt.

Finally, we use the `show` command to display the aligned proteins in cartoon representation.

Note that the `align` command will superimpose the mobile protein onto the reference protein, so that the two proteins have the same orientation and position.

````
  commands from each query will be saved internally. if you want to execute all saved commands, run `chat e` or `chat execute`. After execution, the stashed commands are cleared.

**3. Want to start over again?**
To start a new chat session, just enter the following in the PyMOL command line: `chat new`. This will let ChatMol clear the conversation history.