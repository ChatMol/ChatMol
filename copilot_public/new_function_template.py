import types

def translate_to_protein(self, seq: str, pname=None):
    from Bio.Seq import Seq

    nucleotide_seq = Seq(seq)
    protein_seq = nucleotide_seq.translate()
    if pname:
        return f"The protein sequence of {seq} is `>{pname}\n{protein_seq}`"
    else:
        return f"The protein sequence of {seq} is `>protein\n{protein_seq}`"

function_descriptions = [{  # This is the description of the function
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
}]

test_data = {
    "translate_to_protein": {
        "input": {
            "self": None,
            "seq": "ATGCGAATTTGGGCCC",
        },
        "output": "The protein sequence of ATGCGAATTTGGGCCC is `>protein\nMRFL`",
    }
}

### DO NOT MODIFY BELOW THIS LINE ###
def get_all_functions():
    all_functions = []
    global_functions = globals()
    for _, func in global_functions.items():
        if isinstance(func, types.FunctionType):
            all_functions.append(func)
    return all_functions

def get_info():
    return {"functions": get_all_functions(), "descriptions": function_descriptions}

def test_new_function(function, function_name, test_data):
    return (
        function(**test_data[function_name]["input"])
        == test_data[function_name]["output"]
    )
