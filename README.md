# PyMOL ChatGPT Plugin
<!-- ![img](./assets/img.png) -->
## Overview
The PyMOL ChatGPT Plugin seamlessly integrates OpenAI's GPT-3.5-turbo model into PyMOL, enabling users to interact with PyMOL through natural language instructions. This powerful tool simplifies PyMOL tasks and provides suggestions, explanations, and guidance on various PyMOL-related topics.

## Requirements
- PyMOL
- OpenAI Python package: To install, enter `pip install openai` in the PyMOL command line.

## Installation
1. Download the plugin script `chatmol.py` and save it to a convenient location on your computer.
2. Open PyMOL.
3. In the PyMOL command line, enter `run /path/to/chatmol.py` (replace `/path/to` with the actual path to the script).
4. The plugin is now installed and ready to use.

Alternatively, you can use the following command to load the plugin directly:


```
load https://raw.githubusercontent.com/JinyuanSun/ChatMol/main/chatmol.py
```

If you want a permentally installation, click `Plugin`, go to the `Plugin Manager`, navigate to the `Install New Plugin`, choose the local file or fetch from the url: `https://raw.githubusercontent.com/JinyuanSun/ChatMol/main/chatmol.py`

## Usage
1. Set your OpenAI API key by entering the following command in the PyMOL command line: `set_api_key your_api_key_here` (replace `your_api_key_here` with your actual API key). The API key will be saved in the same directory as the plugin script for future use.
2. Ask ChatGPT about how to perform PyMOL tasks. Use the `chat` command followed by your question or message in the PyMOL command line, e.g., `chat "How do I align two proteins?", False`. You will receive a helpful response such as:
```text
ChatGPT: To align two proteins in PyMOL, you can use the `align` command. Here's an example:
 
``
# Load two proteins
fetch 1ake
fetch 1tim
 
# Align 1tim onto 1ake
align 1tim, 1ake
``
 
In this example, we first load two proteins using the `fetch` command. If you already have the proteins loaded, you can skip this step.
 
Next, we use the `align` command to align `1tim` onto `1ake`. The first argument is the object to be aligned (`1tim`), and the second argument is the reference object (`1ake`). PyMOL will align the two proteins based on their structural similarity, and create a new object with the aligned structure.
 
You can also specify which atoms to use for the alignment by adding the `atommask` option. For example:
 
``
# Align 1tim onto 1ake using only the backbone atoms
align 1tim and name CA+C+N+O, 1ake and name CA+C+N+O
``
 
In this example, we use the `and` operator to select only the backbone atoms (`CA`, `C`, `N`, and `O`) for both proteins. This can be useful if you only want to align the backbone of the proteins, and ignore any side chain differences.
```
commands will be saved every time, if you believe this is what you want, run `chat e` will execute satshed commands.
3. If you trust ChatGPT, just remove the fasle from your command: `chat How do I color a protein by secondary structure?`.

![img](./assets/img_ss.png)

## Features
- Seamless integration with PyMOL.
- User-friendly command-line interface.
- Persistent API key storage for convenient one-time setup.
- Utilizes OpenAI's GPT-3.5-turbo model for powerful, context-aware suggestions and guidance.

## Limitations
- The plugin relies on the OpenAI API, so an internet connection and API key are required for usage.
- The ChatGPT model's knowledge is based on the training data available up to September 
## Support
For any questions or issues related to the PyMOL ChatGPT Plugin, please refer to the official PyMOL mailing list or OpenAI's documentation and support resources.

## License
This project is released under the MIT License.
