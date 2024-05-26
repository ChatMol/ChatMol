import json
import requests
import os
import pprint

os.environ["REGISTRY_HOST_PORT"]="100.89.180.132:9999"
api_key = os.getenv("OPENAI_API_KEY")
app_pw = os.getenv("GMAIL_APP_PASSWORD")
registry_host_port = os.getenv("REGISTRY_HOST_PORT")

registry = requests.get("http://"+registry_host_port+"/registry").json()
pymol_endpoint = ""
for key in registry.keys():
    r = registry[key]
    if (r['service_name'] == 'PyMOL'):
        pymol_endpoint = r['endpoint']
        print("Endpoint PyMOL = ", pymol_endpoint)     
try:
    response = requests.post("http://"+pymol_endpoint)
    pprint.pprint(response)
except:
    print("Something is wrong")

GPT_MODEL = "gpt-3.5-turbo"
def chat_completion_request(messages, functions=None, function_call=None, model=GPT_MODEL):
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + api_key,
    }
    json_data = {"model": model, "messages": messages}
    if functions is not None:
        json_data.update({"functions": functions})
    if function_call is not None:
        json_data.update({"function_call": function_call})
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=json_data,
        )
        return response
    except Exception as e:
        print("Unable to generate ChatCompletion response")
        print(f"Exception: {e}")
        return e

service_ip = pymol_endpoint.split(":")[0]
print("PyMOL service IP = ",service_ip)

# dictionaries for function schema, code and funcs
func_sche_dict = {}
func_code_dict = {}
func_comp_dict = {}

code_str = """
def load_protein_into_pymol(arguments):
    param_obj = json.loads(arguments)
    obj_id = param_obj.get('protein_pdb_id','')
    obj_id = obj_id.lower()
    loaded_objects = cmd.get_names('objects')
    print("Existing Objects: ", loaded_objects)
    if (obj_id in loaded_objects):
        print("Object "+obj_id+" already loaded")
    else:
        cmd.fetch(obj_id)
        print("Send this cmd to PyMOL:","fetch "+obj_id)
        command = f"fetch {obj_id};"
        #response = requests.post('http://localhost:8101/send_message', data=command)
        print("command",command)
        response = requests.post('http://'+service_ip+':8101/send_message', data=command)
        loaded_objects = cmd.get_names('objects')
        print("Loaded Objects: ", loaded_objects)    
"""
    
func_code_dict['load_protein_into_pymol'] = code_str
func_sche_dict['load_protein_into_pymol'] =     {
        "name": "load_protein_into_pymol",
        "description": "fetch a protein from PDB",
        "parameters": {
            "type": "object",
            "properties": {
                "protein_pdb_id": {
                    "type": "string",
                    "description": "PDB ID of a protein. It is usually a four character code",
                },
            },
            "required": ["protein_pdb_id"],
        },
    }

code_str = """ 
def remove_object_from_3D_view(arguments):
    param_obj = json.loads(arguments)
    obj_id = param_obj.get('object_id','')
    obj_id = obj_id.lower()
    loaded_objects = cmd.get_names('objects')
    print("Existing Objects: ", loaded_objects)
    if (obj_id in loaded_objects):
        print("Delete object "+obj_id+"!")
        print("Send this cmd to PyMOL:","delete "+obj_id)
        command = f"delete {obj_id};"
        response = requests.post('http://'+service_ip+':8101/send_message', data=command)
        cmd.delete(obj_id)
    else:
        print("Objects: "+obj_id+ " does not exist.")
"""
        
func_code_dict['remove_object_from_3D_view'] = code_str
func_sche_dict['remove_object_from_3D_view'] = {
        "name": "remove_object_from_3D_view",
        "description": "delete an object from 3D view of PyMOL",
        "parameters": {
            "type": "object",
            "properties": {
                "object_id": {
                    "type": "string",
                    "description": "The object name in a 3D view of PyMOL",
                },
            },
            "required": ["object_id"],
        },
    }

 
code_str = """
def color_protein_chains(arguments):
    param_obj = json.loads(arguments)
    obj_id = param_obj.get('protein_pdb_id','')
    obj_id = obj_id.lower()
    colors = ['red','blue','yellow','purple','magenta','brown']
    
    loaded_objects = cmd.get_names('objects')
    print("Existing Objects: ", loaded_objects)
    
    if (obj_id in loaded_objects):
        print("Object "+obj_id+" already loaded")
    else:
        cmd.fetch(obj_id)
        print("Send this cmd to PyMOL:","fetch "+obj_id)
        command = f"fetch {obj_id};"
        response = requests.post('http://'+service_ip+':8101/send_message', data=command)
        loaded_objects = cmd.get_names('objects')
        print("Loaded Objects: ", loaded_objects)
        if (obj_id not in loaded_objects):
            print("Protein "+obj_id+" does not exist")

    # Get the list of chains in the structure
    chains = cmd.get_chains(obj_id)
    if (len(chains) == 0):
        print("Not chain exist for protein "+obj_id)

    # You can also iterate over the chains and perform operations
    commands = ""
    for i in range(len(chains)):
        i6 = i%6
        chain = chains[i]
        cmd_str = f" color {colors[i6]}, chain {chain};"
        commands += cmd_str
        print(f" color {colors[i6]}, chain {chain};")
        cmd.color(colors[i6], "chain "+chain)
    print("Send the following command to PyMol")
    print(commands)
    response = requests.post('http://'+service_ip+':8101/send_message', data=commands)
"""

func_code_dict['color_protein_chains'] = code_str
func_sche_dict['color_protein_chains'] = {
        "name": "color_protein_chains",
        "description": "a protein and display its chains with different colors",
        "parameters": {
            "type": "object",
            "properties": {
                "protein_pdb_id": {
                    "type": "string",
                    "description": "PDB ID of a protein. It is usually a four character code",
                },
            },
            "required": ["protein_pdb_id"],
        },
    } 

code_str = """
def clear_objects(arguments):
    print("Clear all object in PyMol view")
    loaded_objects = cmd.get_names('objects')
    commands = ""
    for obj in loaded_objects:
        cmd.delete(obj)
        commands += f"delete {obj}; "
    print("send the following command to PyMol")
    print(commands)
    response = requests.post('http://'+service_ip+':8101/send_message', data=commands)
"""

func_code_dict['clear_objects'] = code_str
func_sche_dict['clear_objects'] = {
        "name": "clear_objects",
        "description": "clear all objects if no specific object name is specified",
        "parameters": {
            "type": "object",
            "properties": {
                "protein_pdb_id": {
                    "type": "string",
                    "description": "PDB ID of a protein. It is usually a four character code",
                },
            },
        },
    }
   

# Create Funcation Calling Schema for OpenAI function calling
def func_schema_gen(registry):
    for key in registry.keys():
        r = registry[key]
        #print(r)
        func_schema = {}
        func_schema['name'] = r['service_name']
        func_schema['description'] = r['description']
        params = {}
        props ={}
        params['type'] = 'object'
        params['properties'] = props
        required = []
        param_desc_str = r['param_desc'].replace("'",'"')
        print("desc = ",param_desc_str)
        param_desc = json.loads(param_desc_str)
        for param_name in param_desc.keys():
            if (param_name == "output_sdf"):
                continue
            p_desc = param_desc[param_name]
            if (p_desc.find('Optional') == -1 and p_desc.find('optional') == -1):
                required.append(param_name)
            props[param_name] = {'type':"string","description":param_desc[param_name]}
        params['reguired'] = required
        func_schema['parameters'] = params
        func_sche_dict[r['service_name']] = func_schema
        pprint.pprint(func_schema)
    return func_sche_dict

# Get the default value for optional parameters
def get_default_value(param_desc):
    if (param_desc.find("Optional") < 0 and param_desc.find("optional") < 0):
        return None
    default_value = None
    try:
        if (param_desc.find("Default")> -1 or param_desc.find("default")> -1):
            param_desc = param_desc.replace("  "," ")
            words = param_desc.split(" ")
            for i in range(len(words)):
                w = words[i]
                if (w.find("Default") > -1 or w.find("default") > -1):
                    default_value = words[i+1]
                    if (default_value[-1] == "," or default_value[-1] == "."):
                        default_value = default_value[:-1]
                    break
    except:
        pass
    return default_value
                
    
# Dynamic generation of new python functions from registry
def func_code_gen(registry):
    molgen_funcs = ['DenovoGen','MotifExtend','SuperStructure','ScaffoldMorphine','LinkerGen']
    for key in registry.keys():
        r = registry[key]
        param_desc_str = r['param_desc'].replace("'",'"')
        param_desc = json.loads(param_desc_str)
        param_names = list(param_desc.keys())
        func_args = ",".join(param_names)
        dec_func=[]
        service_name = r['service_name']
        
        reg_args = []
        opt_args = []

        # Check for optinal parameters with default values
        for param_name in param_desc.keys():
            if (param_name == "output_sdf"):
                continue
            desc = param_desc[param_name]
            default_value = get_default_value(desc)
            if (default_value):
                opt_args.append(f"{param_name}={default_value}")
                #opt_args.append(f"{param_name}")
            else:
                reg_args.append(param_name)
        func_args = reg_args + opt_args
        print("func_args = ", func_args)
        func_arg_str = ",".join(func_args)
        print("func_arg_str = ", func_arg_str)
        dec_func.append("def "+r['service_name']+"(self," + func_arg_str +"):")
        dec_func.append("    from chatmol_fn import redis_writer, redis_reader")
        dec_func.append(f"    print('{service_name} is called')")       
        dec_func.append("    param_dict = {}")
        for param_name in param_desc.keys():
            if (param_name == 'output_sdf'):
                code = f"    param_dict['{param_name}'] = 'testout.sdf'"
            else:
                code = f"    param_dict['{param_name}'] = {param_name}"
            dec_func.append(code)
        dec_func.append("    #Call the generic FastAPI")
        code = f"    messages = call_fastapi('{service_name}', param_dict)"
        dec_func.append(code)
        dec_func.append("    message = ''")
        if (service_name in molgen_funcs):
            # create smiles_key = service_name_smiles
            dec_func.append(f"    smiles_key = '{service_name}' + '_smiles'")
            dec_func.append(f"    redis_writer(smiles_key, messages)")
            #dec_func.append("    message = 'Generated ' + str(len(messages)) + 'molecules\n'")
            dec_func.append(f"    message = 'Generated ' + str(len(messages)) + ' molecules. '")
            dec_func.append(f"    message += 'Generated SMILES list is save to redis cache with smiles_key: ' + smiles_key ") 
        dec_func.append("    return message + ' The results are: ' + str(messages)")
        code_str = "\n".join(dec_func)
        print(code_str)
        func_code_dict[service_name] = code_str
        
    return func_code_dict

func_schema_gen(registry)
func_code_dict = func_code_gen(registry)
print("D func_sche_dict", func_sche_dict.keys())
print("D func_code_dict", func_code_dict.keys())

for key in func_code_dict.keys():
    pprint.pprint(func_code_dict[key])
    pprint.pprint(func_sche_dict[key])
