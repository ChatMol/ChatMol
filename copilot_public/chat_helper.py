import json
import os
import rdkit
import time
import pandas as pd
from openai.types.chat.chat_completion_message import ChatCompletionMessage
from openai.types.chat.chat_completion_message_tool_call import (
    Function,
    ChatCompletionMessageToolCall,
)
import requests
import chatmol_fn as cfn


class ConversationHandler:
    def __init__(self, client, cfn, model_name="gpt-3.5-turbo-1106"):
        self.client = client
        self.model_name = model_name
        self.cfn = cfn
        self.messages = []
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "fetch_asked_pdb",
                    "description": "Show the 3D structure of a specified protein by ID. This function supports three databases:\
    - RCSB PDB: Uses PDB IDs to download protein structures from the RCSB Protein Data Bank.\
    - AlphaFoldDB: Requires UniProt IDs to download predicted protein structures from AlphaFold Database.\
    - ESM: Uses MGnify IDs to download predicted structures from ESM (Evolutionary Scale Modeling).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pdb_id": {
                                "type": "string",
                                "description": "The PDB ID of the molecule",
                            },
                            "database": {
                                "type": "string",
                                "description": "The database name, chose in 'rcsb', 'afdb', 'esm' based on the id provided",
                            },
                        },
                        "required": ["pdb_id", "database"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "pocket_prediction",
                    "description": "query pocketapi.cloudmol.org to predict ligand binding sites of input pdb file.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pdb_file": {
                                "type": "string",
                                "description": "The file path to a local pdb file",
                            },
                        },
                        "required": ["pdb_file"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "protein_structure_prediction",
                    "description": "Preict the structure of a protein sequence",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "seq": {
                                "type": "string",
                                "description": "The protein sequence",
                            },
                            "name": {
                                "type": "string",
                                "description": "The name of the protein sequence",
                            },
                        },
                        "required": ["seq", "name"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "display_protein_structure",
                    "description": "display a protein pdb file structure",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pdb_file": {
                                "type": "string",
                                "description": "The file path to a local pdb file",
                            },
                        },
                        "required": ["pdb_file"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "protein_single_point_mutation_prediction",
                    "description": "Predict the effect of mutations on protein stability",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pdb_file": {
                                "type": "string",
                                "description": "The file path to a local pdb file",
                            },
                            "mutations": {
                                "type": "string",
                                "description": "The mutations to be displayed, in format of 'A_12_F,C_45_D' (a comma separated list of mutations, where each mutation is of the form <wildtype>_<residue_number>_<mutation>",
                            },
                        },
                        "required": ["pdb_file", "mutations"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "recommand_stable_mutations",
                    "description": "design stablizing mutations for a protein",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pdb_file": {
                                "type": "string",
                                "description": "The file path to a local pdb file",
                            },
                            "cutoff": {
                                "type": "string",
                                "description": "The cutoff of the stability score, default is -2",
                            },
                        },
                        "required": ["pdb_file"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_protein_sequence_from_pdb",
                    "description": "Get the sequence of a protein from a pdb file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pdb_file": {
                                "type": "string",
                                "description": "The file path to a local pdb file",
                            },
                            "chain_id": {
                                "type": "string",
                                "description": "The chain id of the protein, default is A",
                            },
                        },
                        "required": ["pdb_file"],
                    },
                },
            },
            {  # get the smiles string of a compound by its name
                "type": "function",
                "function": {
                    "name": "get_smiles_from_name",
                    "description": "Get the SMILES string of a compound by its name",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "compound_name": {
                                "type": "string",
                                "description": "The name of the compound",
                            },
                        },
                        "required": ["compound_name"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_3D_conformation_and_save",
                    "description": "Generate 3D conformation and save as PDB",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "smiles": {
                                "type": "string",
                                "description": "The SMILES string of the compound",
                            },
                            "file_name": {
                                "type": "string",
                                "description": "The file name of the PDB file, e.g. 'lys.pdb'",
                            },
                        },
                        "required": ["smiles", "file_name"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "search_rcsb",
                    "description": "Search RCSB PDB database and get some pdb IDs",
                    "parameters": {
                        "type": "object",
                        "properties": {"query": {"type": "string", "description": "The query"}, "max_num": {"type": "string", "description": "The max number of results"}},
                        "required": ["query"],
                        # "required": [],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "query_uniprot",
                    "description": "Query UniProt database and get some UniProt IDs or informations of fasta content",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "The query"},
                            "type": {
                                "type": "string",
                                "description": "should be one of 'search_query', 'get_txt', or 'get_fasta', search_query is to search UniProt database and get some UniProt IDs, get_txt is to get the txt content of a UniProt ID containing annotations, get_fasta is to get the fasta content of a UniProt ID",
                            },
                        },
                    },
                    "required": ["query", "type"],
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "blind_docking",
                    "description": "Perform blind docking using the input protein and ligand",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "protein_pdb_file_path": {"type": "string", "description": "The file path to a local pdb file of the protein"},
                            "ligand_pdb_file_path": {"type": "string","description": "The file path to a local pdb file of the ligand"},
                            "complex_file_path": {"type": "string","description": "The path to save the complex PDB file. Need to be in the same directory as the protein and ligand pdb files"},
                        },
                    },
                    "required": ["query", "type"],
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "call_proteinmpnn_api",
                    "description": "Calls the ProteinMPNN API to design protein sequences based on structures",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path_to_pdb": {"type": "string", "description": "The path to the PDB file."},
                            "designed_chain": {"type": "string", "description": "The designed chain identifier."},
                            "num_seqs": {"type": "string", "description": "The number of sequences to generate."},
                            "homonomer": {"type": "string", "description": "Indicates whether the protein is a homomer or not."},
                            "sampling_temp": {"type": "string", "description": "The sampling temperature."},
                            "fixed_chain": {"type": "string", "description": "The fixed chain identifier, optional.", "default": None},
                        },
                    },
                    "required": ["path_to_pdb", "designed_chain","num_seqs", "homonomer", "sampling_temp","fixed_chain"],
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "compare_protein_structures",
                    "description": "Compare the structures of two proteins with TMAlign",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pdb_file1": {"type": "string", "description": "The file path to a local pdb file of the first protein"},
                            "pdb_file2": {"type": "string", "description": "The file path to a local pdb file of the second protein"},
                        },
                    },
                    "required": ["pdb_file1", "pdb_file2"],
                }
            },
            { "type": "function",
                "function": {
                    "name": "python_executer",
                    "description": "Python executer creates a python function from python code (string), and execute it.",
                     "parameters": {
                        "type": "object",
                        "properties": {
                            "function_name": {"type": "string", "description": "The python funciton name"},
                        },
                    },
                    "required": ["function_name"],                   
                }
            }
            
        ]
        self.available_functions = {
            "fetch_asked_pdb": self.cfn.fetch_asked_pdb,
            "pocket_prediction": self.cfn.pocket_prediction,
            "display_protein_structure": self.cfn.display_protein_structure,
            "protein_structure_prediction": self.cfn.protein_structure_prediction,
            "get_work_dir": self.cfn.get_work_dir,
            "recommand_stable_mutations": self.cfn.recommand_stable_mutations,
            "protein_single_point_mutation_prediction": self.cfn.protein_single_point_mutation_prediction,
            "get_smiles_from_name": self.cfn.get_smiles_from_name,
            "generate_3D_conformation_and_save": self.cfn.generate_3D_conformation_and_save,
            "get_protein_sequence_from_pdb": self.cfn.get_protein_sequence_from_pdb,
            "search_rcsb": self.cfn.search_rcsb,
            "query_uniprot": self.cfn.query_uniprot,
            "blind_docking": self.cfn.blind_docking,
            "call_proteinmpnn_api": self.cfn.call_proteinmpnn_api,
            "compare_protein_structures": self.cfn.compare_protein_structures,
            "python_executer": self.cfn.python_executer,
        }

    def setup_workdir(self, work_dir):
        self.cfn.WORK_DIR = work_dir

    def run_round(self, user_message):
        self.messages.append(
            {
                "role": "user",
                "content": user_message,
            }
        )

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=self.messages,
            tools=self.tools,
            tool_choice="auto",
        )

        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls
        self.messages.append(response_message)
        second_response = None
        if tool_calls:
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_to_call = self.available_functions[function_name]
                function_args = json.loads(tool_call.function.arguments)
                function_response = function_to_call(**function_args)

                self.messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": function_response,
                    }
                )
            second_response = client.chat.completions.create(
                model=self.model_name,
                messages=self.messages,
            )  # get a new response from the model where it can see the function response
        return response, second_response


# class GLMConversationHandler(ConversationHandler):
#     from zhipuai import ZhipuAI


def compose_chat_completion_message(
    role="assistant", content="", tool_call_dict_list=[]
):
    tool_calls = []
    for tool_call_dict in tool_call_dict_list:
        tool_call = ChatCompletionMessageToolCall(
            id=tool_call_dict["id"],
            function=Function(
                name=tool_call_dict["function"]["name"],
                arguments=tool_call_dict["function"]["arguments"],
            ),
            type="function",
        )
        tool_calls.append(tool_call)
    message = ChatCompletionMessage(
        role=role,
        content=content,
        tool_calls=tool_calls,
    )
    return message

def extract_function_and_execute(llm_output, messages):
    name = llm_output.choices[0].message.tool_calls[0].function.name
    params = json.loads(llm_output.choices[0].message.tool_calls[0].function.arguments)
    function_to_call = globals().get(name)
    if not function_to_call:
        raise ValueError(f"Function '{name}' not found")

    messages.append(
        {
            "role": "tool",
            "content": str(function_to_call(**params))
        }
    )
    return messages