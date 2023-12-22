# ChatMol copilot

[![IMAGE ALT TEXT HERE](https://img.youtube.com/vi/9uMFZMQqTf8/0.jpg)](https://www.youtube.com/watch?v=9uMFZMQqTf8)


## Introduction
This is ChatMol copilot, just like other copilot, it is designed to help your work. Here the LLM is enpowered by computational biology tools and databases. We showed some cases in the video, and you can also try it by yourself.

## Installation

```bash
git https://github.com/JinyuanSun/ChatMol
cd ChatMol/copilot_public
pip install -r requirements.txt
```

## Usage
```bash
streamlit run main.py
```
## Want more funtionality?

You can easily add more functionality to ChatMol copilot. 

```python

# 1. Define a function
def translate_to_protein(self, seq:str, pname=None):
    from Bio.Seq import Seq
    nucleotide_seq = Seq(seq)
    protein_seq = nucleotide_seq.translate()
    if pname:
        return f"The protein sequence of {seq} is `>{pname}\n{protein_seq}`"
    else:
        return f"The protein sequence of {seq} is `>protein\n{protein_seq}`"

# 2. Add it to the conversation
cfn.translate_to_protein = translate_to_protein.__get__(cfn)
conversation.tools.append(
    { # This is the description of the function
        "type": "function",
        "function": {
            "name": "translate_to_protein",
            "description": "Translate a DNA/RNA sequence to a protein sequence",
            "parameters": {
                "type": "object",
                "properties": {
                    "seq": {"type": "string", "description": "The DNA/RNA sequence"},
                },
            },
            "required": ["seq"],
        },
    }
)
conversation.available_functions["translate_to_protein"] = cfn.translate_to_protein
```
By adding the above code to `main.py` at line 97 after `conversation = ConversationHandler(client, cfn, model_name=model)`, you can add this translation function to ChatMol copilot.

You are more than welcome to contribute any function to ChatMol copilot.
1. Fork this repo
2. Create a new branch
3. Add your function in `copilot_public/new_function_template.py`.  
   In this file, you need to define a function and clearly define the parameters and return value of this function, also add test case in `test_data`. You can refer to the existing content in `copilot_public/new_function_template.py`. We have a button named `Add from template`. You can click it to add your function to ChatMol copilot.
4. Create a pull request
5. We will review your code and merge it to the main branch  

**If you still don't know what to do, just paste this and the content in `copilot_public/new_function_template.py` to the input box of ChatGPT and ask it to do all the coding for you.**  
*Remeber to add the magic prompt: "I don't have fingers, can you write the complete code for me."*


## TODO
### Analysis tools
- [ ] **Protein Docking Simulation**: Develop a simulation tool for docking small molecule ligands to protein targets, exploring potential binding modes.
  - AutoDock Vina (High priority)
  - DiffDock (Low priority)
  
- [ ] **Protein Structure and Sequence Comparison**: Build a tool for comparing the structures of multiple proteins, identifying similarities, differences, and motifs.
  - TM-align (High priority)
  - Kalign (Medium priority)
  - MMseqs2 (Low priority)

- [ ] **Ligand Binding Affinity Prediction**: Create a tool to predict the binding affinity of ligands with protein targets, aiding in understanding ligand-protein interaction strength.
  - RF-Score (High priority)
  - 

- [ ] **Protein Design and Engineering**: Design a tool for engineering proteins with specific functions or properties, like enzyme activity or substrate binding.

- [ ] **Protein-Protein Interaction Prediction**: Develop a tool to predict protein-protein interaction partners and binding sites based on their 3D structures.

- [ ] **Protein Function Prediction**: Build a tool for predicting the biological function of proteins based on their structure and sequence.


### visualization tools
- [ ] **Protein-Ligand Interaction Visualization**: Create a tool for visualizing and analyzing protein-ligand interactions, focusing on key binding residues.


## Online Version
We provided an online version for you. [Click here](https://chatmol.org/copilot/) to try it.  