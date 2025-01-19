# ChatMol
Started from a PyMol plugin, towards a comprehensive molecular design assistant.

![GitHub license](https://img.shields.io/github/license/ChatMol/ChatMol)  ![GitHub issues](https://img.shields.io/github/issues/ChatMol/ChatMol) ![GitHub forks](https://img.shields.io/github/forks/ChatMol/ChatMol)  ![GitHub stars](https://img.shields.io/github/stars/ChatMol/ChatMol)

## Overview
<details>
<summary>Table of contents</summary>

- [ChatMol](#chatmol)
  - [Overview](#overview)
  - [PyMOL Plugin](#pymol-plugin)
  - [ChatMol + Streamlit](#chatmol--streamlit)
  - [ChatMol python package](#chatmol-python-package)
  - [Copilot](#copilot)
  - [ChatMol Website](#chatmol-website)
  - [License](#license)
</details>

We aim to leverage the capabilities of large language models to better assist scientists in designing new biomolecules. Our journey began with developing a [PyMOL plugin](#pymol-plugin) that automatically translates natural language into commands. From there, we expanded into several domains, including:

- An interactive [Streamlit interface](#chatmol--streamlit)
- A dedicated [Python package](#chatmol-python-package)
- [ChatMol Copilot](#copilot): an automated system capable of executing various tasks including: 
  - Structure prediction
  - Molecular docking
  - Sequence design
  - Small molecule analysis & generation

Through these tools, we strive to empower scientists to better utilize large language models in solving scientific problems. Our goal is to bridge the gap between advanced AI capabilities and practical scientific research needs in molecular biology and related fields.

## PyMOL Plugin

**Installation**  
Simply run the following command in PyMOL command line to install the plugin:

```python
load https://raw.githubusercontent.com/ChatMol/ChatMol/main/chatmol.py
```

For permanent installation, go to `Plugin` -> `Plugin Manager` -> `Install New Plugin` and enter the URL `https://raw.githubusercontent.com/ChatMol/ChatMol/main/chatmol.py`.

**Usage**  
The simplest way to get started is to use the `chatlite` command in PyMOL. 
```pymol
chatlite download 1ake and color it by secondary structures
```

![img](./assets/img_ss.png)

Refer to the [doc](./pymol_plugin/README.md) for more details.

**miniGUI**  
We also provide a miniGUI for ChatMol-Lite, which can be used as a task execution agent or Q&A chatbot. It retains your entire conversation history with ChatMol, and you have the flexibility to modify the execution plan suggested by ChatMol. For example, you can delete certain commands or add additional commands before sending them to PyMOL. You can launch the miniGUI from a terminal.

```bash
cd miniGUI
python miniGUI.py
```
Here is a screenshot of the miniGUI:
![img](./assets/chatmol_lite.png)

## ChatMol + Streamlit

We also provide a Streamlit app for ChatMol, which can be used as a task execution agent or Q&A chatbot. It retains your entire conversation history with ChatMol, and you have the flexibility to modify the execution plan suggested by ChatMol. See more details in [here](./chatmol-streamlit/README.md).

## ChatMol python package

See this [README](./chatmol_pkg/README.md) for more details.

```bash
pip install chatmol
```

## Copilot
This is ChatMol copilot, just like other copilot, it is designed to help your work.  
[![IMAGE ALT TEXT HERE](https://img.youtube.com/vi/9uMFZMQqTf8/0.jpg)](https://www.youtube.com/watch?v=9uMFZMQqTf8)
See more details in [here](./copilot_public/README.md)

## ChatMol Website

- Visit the [official website](https://chatmol.org) for comprehensive information about its development and use cases.

- The [ChatMol web-browser interface](http://xp.chatmol.org/chatmol.html) allows you to submit PyMOL requests and execute them in PyMOL via ChatMol. (Please note that this feature is browser setting-dependent)

## Acknowledgements

As an open source project, we thank the support from [ChemXAI](https://www.chemxai.com/), [WeComput](https://www.wecomput.com/) and [levinthal](https://www.levinthal.bio/).

## License
This project is released under the MIT License.
