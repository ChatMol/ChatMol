# PyMOL ChatGPT Plugin

## Table of contents
- [PyMOL ChatGPT Plugin](#pymol-chatgpt-plugin)
  - [Table of contents](#table-of-contents)
  - [Overview](#overview)
  - [ChatMol Website](#chatmol-website)
  - [Requirements \& Installation](#requirements--installation)
  - [Usage](#usage)
    - [ChatMol](#chatmol)
      - [ChatMol can do what you ask for:](#chatmol-can-do-what-you-ask-for)
      - [ChatMol can answer your questions:](#chatmol-can-answer-your-questions)
      - [Want to start over?](#want-to-start-over)
    - [ChatMol-Lite](#chatmol-lite)
    - [miniGUI](#minigui)
  - [License](#license)

## Overview
The PyMOL ChatGPT Plugin seamlessly integrates OpenAI's GPT-3.5-turbo model into PyMOL, enabling users to interact with PyMOL through natural language instructions. This powerful tool simplifies PyMOL tasks and provides suggestions, explanations, and guidance on various PyMOL-related topics.

## ChatMol Website

- The [official website](https://chatmol.org) of ChatMol. It provides all information about ChatMol development and use cases. 

- [Online Chatbot](https://chatmol.org/qa/) to chat with.

- [ChatMol web-browser interface](http://xp.chatmol.org/chatmol.html) to interact with PyMOL via ChatMol (This feature depends on your browser setting).

## Requirements & Installation
<img src="./assets/install.png" alt="alt text" width="400px" align="right"/>

- PyMOL
- OpenAI Python package: To install, enter `pip install openai` in the PyMOL command line.
<!-- ![img](./assets/install.png) -->

1. Download the plugin script `chatmol.py` and save it to a convenient location on your computer.
2. Open PyMOL.
3. In the PyMOL command line, enter `run /path/to/chatmol.py` (replace `/path/to` with the actual path to the script).
4. Create a .PyMOL folder in your home director for saving PyMOL related files, like ChatGPT API keys, PyMOL license file etc.
5. The plugin is now installed and ready to use.

Alternatively, you can use the following command to load the plugin directly:

```
load https://raw.githubusercontent.com/JinyuanSun/ChatMol/main/chatmol.py
```

If you want a permentally installation, click `Plugin`, go to the `Plugin Manager`, navigate to the `Install New Plugin`, choose the local file or fetch from the url: `https://raw.githubusercontent.com/JinyuanSun/ChatMol/main/chatmol.py`

## Usage

We present two options for utilizing ChatMol: ChatMol and ChatMol-Lite. ChatMol directly calls OpenAI's GPT3.5 model and requires you to set up your own API key. On the other hand, ChatMol-Lite is a system we developed using additional PyMol-related resources. It offers faster performance and eliminates the need for an API key setup.

### ChatMol

Set your OpenAI API key by entering the following command in the PyMOL command line: `set_api_key your_api_key_here` (replace `your_api_key_here` with your actual API key). The API key will be saved in the same directory as the plugin script for future use.

#### ChatMol can do what you ask for:
Automate PyMOL commands effortlessly with the ChatGPT Plugin. In the PyMOL command line, simply type `chat` as the trigger word for the plugin, followed by your PyMOL tasks or questions about using specific PyMOL commands. Clear instructions will be shown, and the commands will be executed automatically by default. For instance, use `chat Show me example to color a protein by its secondary structures` to view a protein molecule in the PyMOL 3D window with colors representing its secondary structures.

![img](./assets/img_ss.png)

#### ChatMol can answer your questions:
Ask ChatMol about how to perform PyMOL tasks without execution the PyMOL commands. You can disable the automatic execution by adding a question mark `?` at the end of ChatMol prompt, e.g., `chat How do I align two proteins?`. You will receive a helpful response such as:
   
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

#### Want to start over?
To start a new chat session, just enter the following in the PyMOL command line: `chat new`. This will let ChatMol clear the conversation history.

### ChatMol-Lite
We found the response of gpt-3.5 is slow and people might don't have access to OpenAI's API, we developed chatmol-lite as an alternative. This is installed with the chatmol automatically. You can use it by typing `chatlite` in the PyMOL command line:
```bash
chatlite "Something you want chatmol to do for you"
```
**`chatlite` is different from the `chat`:**
1. Although it is a chatbot and have memory, it is designed to directly execute commnads based on your instructions. 
2. You can chat with ChatMol-Lite at [here](https://chatmol.org/qa/), the model is the same as the `chatlite`
3. It is much faster than the `chat` and you don't need to set up the OpenAI API key. And the response is more short than the `chat` .

### miniGUI
We also provide a miniGUI for ChatMol-Lite. You can start it from the terminal:
```bash
git clone https://github.com/JinyuanSun/ChatMol.git
cd ChatMol/miniGUI
python miniGUI.py
```

## License
This project is released under the MIT License.
