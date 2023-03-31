# PyMOL ChatGPT Plugin
![img](./assets/img.png)
## Overview
The PyMOL ChatGPT Plugin is a simple yet powerful tool that integrates OpenAI's GPT-3.5-turbo model into PyMOL, allowing users to interact with the model and get relevant suggestions, explanations, and guidance on various PyMOL-related topics.

## Requirements
- PyMOL
- OpenAI Python package: `pip install openai`
## Installation
1. Download the plugin script `chatgpt_plugin.py` and save it to a convenient location on your computer.
2. Open PyMOL.
3. In the PyMOL command line, enter `run /path/to/chatgpt_plugin.py` (replace `/path/to` with the actual path to the script).
4. The plugin is now installed and ready to use.

Or:

```
load https://raw.githubusercontent.com/JinyuanSun/ChatMol/main/chatmol.py
```

## Usage
1. Set your OpenAI API key by entering the following command in the PyMOL command line: `set_api_key your_api_key_here` (replace `your_api_key_here` with your actual API key). The API key will be saved in the same directory as the plugin script for future use.
2. To interact with ChatGPT, simply use the `chatgpt` command followed by your question or message in the PyMOL command line, e.g., `chatgpt "How do I align two proteins?"`.
## Features
- Simple integration with PyMOL.
- Convenient command-line interface.
- Persistent API key storage, ensuring you only need to set the API key once.
- Utilizes OpenAI's GPT-3.5-turbo model for powerful, context-aware suggestions and guidance.
## Limitations
- The plugin relies on the OpenAI API, so an internet connection and API key are required for usage.
- The ChatGPT model's knowledge is based on the training data available up to September 2021.
## Support
For any questions or issues related to the PyMOL ChatGPT Plugin, please refer to the official PyMOL mailing list or OpenAI's documentation and support resources.

## License
This project is released under the MIT License.
