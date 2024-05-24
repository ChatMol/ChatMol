import types
import os
import re
import requests
import urllib.parse
from enum import Enum
from build_from_registry import *

registry_host_port = os.getenv("REGISTRY_HOST_PORT")
print("registry_host_PORT  ", registry_host_port)

test_data = []

def call_fastapi(service: str, params={}):
    # call fastapi endpoint
    # From service, find the available endpoint
    global registry_host_port
    print("1 input service name = ", service)
    print("2 Get all registerred services")
    registry = requests.get("http://"+registry_host_port+"/registry").json()
    print("3 Length of Registry = ",len(registry))

    # Search for service endpoint by service name
    service_endpoint = ""
    status = "Inactive"
    for key in registry.keys():
        r = registry[key]
        print("Registry = ",r)
        if (r['service_name'] == service):
            service_endpoint = r['endpoint']
            status = r['status']
    if (service_endpoint == ""):
        print("Service not found")
        return "Service not found"
    if  (service_endpoint != "" and status== "Inactive"):
        print("Service is inactive")
        return "Service is inactive"

    # Now, constructure encoded_url for FastAPI call

    if (len(params) == 0):
        # just check the status 
        url = url = "http://" + service_endpoint + "/status"
        message = requests.get(url).json()
    else:
        url = "http://" + service_endpoint+"?" + urllib.parse.urlencode(params)
        message  = requests.post(url).json()
    return message

func_code_list = []
func_sche_list = []
func_list = []

for key in func_code_dict.keys():
    sche = {"type": "function", "function": func_sche_dict[key]}
    func_code_list.append(func_code_dict[key])
    func_sche_list.append(sche)


for i in range(len(func_code_list)):
    code = func_code_list[i]
    sche = func_sche_list[i]
    service_name = sche['function']['name']
    code_obj = compile(code, service_name, 'exec')
    # Execute the compiled code object in the prepared namespace
    exec(code_obj, globals())
    service_func = globals().get(service_name)
    print("service_func", service_func)
    func_list.append(service_func)


### DO NOT MODIFY BELOW THIS LINE ###
def get_all_functions():
    all_functions = []
    global_functions = globals()
    for _, func in global_functions.items():
        # Made one line change
        if isinstance(func, types.FunctionType) and func in func_list:
            all_functions.append(func)
    return all_functions

def get_info():
    #return {"functions": get_all_functions(), "descriptions": function_descriptions}
    return {"functions": func_list, "descriptions": func_sche_list}

def test_new_function(function, function_name, test_data):
    return (
        function(**test_data[function_name]["input"])
        == test_data[function_name]["output"]
    )
