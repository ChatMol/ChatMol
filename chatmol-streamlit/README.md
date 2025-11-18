# chatmol-streamlit
Streamlit interface for ChatMol's Agentic Molecular Visualization (AMV).

## Overview
This app runs a Streamlit GUI that lets you interact with an LLM-powered PyMOL agent. The agent can:
- Generate PyMOL command sequences from natural-language instructions.
- Execute commands in a running PyMOL GUI session.
- Produce a publication-quality view analysis from a rendered PyMOL screenshot.

## Requirements
- Python 3.10+ recommended
- PyMOL (open-source build)
- `streamlit` (tested with 1.35.0+)
- `openai` Python SDK
- `chatmol` package [at here](/ChatMol/chatmol_pkg)

You can install the main dependencies with conda/pip:

```bash
conda install -c conda-forge pymol-open-source
pip install streamlit==1.35.0 openai chatmol
```


## Environment variables
The app expects one or more API key environment variables. By default the UI is configured to use `OPENAI_API_KEY` for all models. Set it before starting Streamlit:

```bash
export OPENAI_API_KEY="sk-..."
```

If you prefer different env var names for different model roles (PyMOL commands, view analysis, agent) you can change them in the sidebar at runtime — the app lets you specify the name of the environment variable to read for each role.

## Running the app
From the `chatmol-streamlit` directory run:

```bash
streamlit run app.py
```

The Streamlit sidebar contains a **Model & API settings** section where you can:
- Choose model names for `PyMOL commands`, `View analysis`, and the `Agent`.
- Set the base URL for each model (default: `https://api.openai.com/v1`).
- Set the environment variable name that stores the API key for each model role.

Changes are applied immediately for new requests.

## Example prompt
Try the test prompt shown in the sidebar (also used in the app):

```
Highlight aromatic sidechains of 1pga and prepare to scientific publication level.
```

When you submit a prompt the app will display assistant messages in the chat area and show the latest `screenshot.png` produced by PyMOL.

## Troubleshooting
- If you see "Environment variable '... is not set'" errors, export the API key env var specified in the sidebar (default `OPENAI_API_KEY`).
- If PyMOL doesn't start, ensure `pymol-open-source` is installed and that `chatmol`'s `start_pymol_gui()` works on your platform.
- The app saves a screenshot as `screenshot.png` in the working directory — check permissions if saving fails.