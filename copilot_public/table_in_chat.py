import streamlit as st
import inspect

def protein_structure_prediction(seq: str):
    """
    Predict the structure of a protein sequence.

    Parameters:
    seq (str): Amino acid sequence of the protein.

    Returns:
    str: A message indicating the submission of the structure prediction.
    """
    return f"Input sequence is {seq}"

def function_args_to_streamlit_ui(func, args=None):
    signature = inspect.signature(func)
    docstring = inspect.getdoc(func)
    if docstring:
        st.write(docstring)
    args_values = {}
    for name, param in signature.parameters.items():
        if param.annotation is str:
            if name == "seq":
                args_values[name] = st.text_area(name, key=name, value=args[name] if name in args else None)
            else:
                args_values[name] = st.text_input(name, key=name, value=args[name] if name in args else None)
        elif param.annotation is int:
            args_values[name] = st.number_input(name, key=name, value=args[name] if name in args else None)
        else:
            args_values[name] = st.text_input(name, key=name, value=args[name] if name in args else None)
    if st.button('Submit'):
        result = func(**args_values)
        # st.write(result)
        return result

if prompt := st.chat_input("What is up?"):
     with st.chat_message("assistant"):
        st.write(f"you said: {prompt}")
        func_res = function_args_to_streamlit_ui(protein_structure_prediction, {'seq': prompt})
        st.write(func_res)