import types

"""
Before using, please ensure the wemol_sdk dependency is present in the pip
"""

function_descriptions = []
test_data = []

def alpha_mhc(self, seq: str) -> str:
    from os import getenv, remove
    from time import sleep
    from wemol_sdk import wemol
    from wemol_sdk.models.request_models import UserReq
    from wemol_sdk.models.config import config_field

    user_name = getenv("WEMOL_USER_NAME")
    user_passwd = getenv("WEMOL_USER_PASSWORD")
    wemol_base_url = getenv("WEMOL_BASE_URL")

    if user_name is None or user_passwd is None or wemol_base_url is None:
        raise Exception(
            "Please set WEMOL_USER_NAME, WEMOL_USER_PASSWORD and WEMOL_BASE_URL environment"
        )

    user = {"Name": user_name, "Passwd": user_passwd}
    config = {config_field.BASE_URL: wemol_base_url}

    session = wemol.createUserSession(user=UserReq(**user), config=config)
    file_path = "./alpha_mhc_cache"

    # Because the job accepts a file attribute, to temporarily create a file and achieve the upload effect without changing the API
    # This will have a better solution
    with open(file_path, "w", encoding="utf-8") as f:
        if seq.startswith(">"):
            f.write(seq)
        else:
            f.write(f">sequence_1\n{seq}")

    job_id = session.run_job(
        module_name="Immunogenicity Prediction (AlphaMHC v3.0 beta)",
        params={"Fasta File": file_path},
    )

    remove(file_path)

    if job_id != -1:
        while True:
            results = session.fetch_job_result(job_id=job_id)
            if results:
                for result in results:
                    if result.file_name == "MolScore.csv":
                        risk = str(result.result_info, encoding="utf-8").split(",")[4]
                        return risk
                break
            sleep(1)

    return "None risk"


function_descriptions.append(
    {
        "type": "function",
        "function": {
            "name": "alpha_mhc",
            "description": "",
            "parameters": {
                "type": "object",
                "properties": {
                    "seq": {
                        "type": "string",
                        "description": "The fasta sequence",
                    },
                },
            },
            "required": ["seq"],
        },
    }
)


test_data["alpha_mhc"] = {
    "input": {
        "self": None,
        "seq": ">sequence_1\nQAVVTQESALTTSPGETVTLTCRSSTGAVTTSNYANWVQEKPDHLFTGLIGGTNKRAPGVPARFSGSLIGDKAALTITGAQTEDEAIYFCALWYSNLWVFGGGTKLTVL",
    },
    "output": "The immunogenic risk is low",  # Example output
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
