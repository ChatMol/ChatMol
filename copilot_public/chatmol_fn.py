import json
import requests
import py3Dmol
from tqdm import tqdm
import matplotlib.pyplot as plt
from cloudmol.cloudmol import PymolFold
from utils import query_pythia, handle_file_not_found_error
import os
from io import StringIO
from stmol import showmol
from rdkit import Chem
from rdkit.Chem import AllChem
import time
import pandas as pd

from Bio.PDB import PDBParser

def read_first_model_pdbqt(pdbqt_filename):
    parser = PDBParser(QUIET=True)
    structure = parser.get_structure("PDBQT", pdbqt_filename)[0]
    atoms = []
    for atom in structure.get_atoms():
        atoms.append(atom)
    return atoms

def format_as_pdb_hetatm(serial:int, atom_name:str, element:str, resseq:int, x, y, z):

    x = "{:6s}{:5d} {:^4s}{:1s}{:3s} {:1s}{:4d}{:1s}   {:8.3f}{:8.3f}{:8.3f}{:6.2f}{:6.2f}          {:>2s}{:2s}".format('HETATM', serial, atom_name, "", "LIG", 'X', 1, "", float(x), float(y), float(z), 1.00, 0, element, '')
    return x + '\n'

def concate_ligand_to_receptor(ligand_file_path, receptor_file_path, output_filename):
    parser = PDBParser(QUIET=True)
    structure = parser.get_structure("receptor", receptor_file_path)[0]
    ligand_atoms = read_first_model_pdbqt(ligand_file_path)
    resseqs = [residue.id[1] for residue in structure.get_residues()]
    serial = max([atom.serial_number for atom in structure.get_atoms()]) + 1
    resseq = max(resseqs) + 1
    with open(output_filename, 'w+') as f:
        with open(receptor_file_path, 'r') as receptor_file:
            for line in receptor_file:
                if line.startswith("ATOM"):
                    f.write(line)
        for i, atom in enumerate(ligand_atoms):
            x, y, z = atom.get_coord()
            f.write(format_as_pdb_hetatm(serial+i, atom.get_name(), atom.element, resseq, x, y, z))
        f.write("TER\n")
    return output_filename

def parse_vina_output(vina_output):
    start = vina_output.find("mode |   affinity")
    end = vina_output.find("Writing output")
    result_str = vina_output[start:end].strip()
    result_data = StringIO(result_str)
    df = pd.read_csv(result_data, delim_whitespace=True, skiprows=3, names=['Mode', 'Affinity (kcal/mol)', 'RMSD l.b.', 'RMSD u.b.'])
    return df

def submit_docking_task(protein_file, ligand_file, center_x=0, center_y=0, center_z=0, box_size_x=20, box_size_y=20, box_size_z=20, aa_list=None):
    headers = {
        'accept': 'application/json',
    }

    files = {
        'protein_file': open(protein_file, 'rb'),
        'ligand_file': open(ligand_file, 'rb'),
        'center_x': (None, str(center_x)),
        'center_y': (None, str(center_y)),
        'center_z': (None, str(center_z)),
        'box_size_x': (None, str(box_size_x)),
        'box_size_y': (None, str(box_size_y)),
        'box_size_z': (None, str(box_size_z)),
    }
    if aa_list:
        files['aa_list'] = (None, aa_list)
    response = requests.post('https://dockingapi.cloudmol.org/api/dock', headers=headers, files=files)
    return response.json()

def submit_pocket_prediction_task(protein_file):
    headers = {
        'accept': 'application/json',
    }
    files = {
        'file': open(protein_file, 'rb'),
    }
    response = requests.post('https://pocketapi.cloudmol.org/predict', headers=headers, files=files)
    return response.json()

def query_docking_status(docking_code):
    response = requests.get(f'https://dockingapi.cloudmol.org/task_status/{docking_code}')# .decode('utf-8')
    return response.text

def get_docking_result(docking_code):
    response = requests.get(f'https://dockingapi.cloudmol.org/task_progress/{docking_code}')
    return response.text

def save_best_docking_result(docking_code ,file_path):
    response = requests.get(f'https://dockingapi.cloudmol.org/get_best_pose/{docking_code}/best_pose.pdb')
    with open(file_path, 'w') as f:
        f.write(response.text)
        # with open(receptor_file_path, 'r') as receptor:
        #     f.write(receptor.read())
    return f"Docking result saved as {file_path}"

class ChatmolFN:
    def __init__(self, work_dir="./"):
        self.WORK_DIR = "./"
        self.STREAMLIT_GUI = True
        self.VIEW_DICTS = {}
        self.viewer_height = 300
        self.viewer_width = 300

    def query_uniprot(self, query, type=["search_query", "get_txt", "get_fasta"]):
        query = query.replace(" ", "+")
        if type == "search_query":
            url = f"https://rest.uniprot.org/uniprot/search?query={query}&format=tsv"
            response = requests.get(url)
            if response.status_code == 200:
                return "\n".join(response.text.split("\n")[:10])
            else:
                return f"Failed to query {query}. HTTP Status Code: {response.status_code}"
        if type == "get_txt":
            url = f"https://www.uniprot.org/uniprot/{query}.txt"
            response = requests.get(url)
            if response.status_code == 200:
                return f"Full uniprot record:\n{response.text}"
            else:
                return f"Failed to query {query}. HTTP Status Code: {response.status_code}"
        if type == "get_fasta":
            url = f"https://www.uniprot.org/uniprot/{query}.fasta"
            response = requests.get(url)
            if response.status_code == 200:
                return f"Fasta of {query}:\n{response.text}\n"
            else:
                return f"Failed to query {query}. HTTP Status Code: {response.status_code}"

    def fetch_asked_pdb(self, pdb_id, database=["rcsb", "afdb", "esm"]):
        """
        Download the PDB file for a given protein from RCSB (pdb_id), AlphaFoldDB (uniprot id) or esmatlas (MGnifyid),
        show it using p3dmol
        Parameters:
        - pdb_id (str): The ID of the protein. The format depends on the selected database.
        - database (str): A database name, includes 'rcsb', 'afdb', 'esm'.
        """
        if database == "rcsb":
            url = f"https://files.rcsb.org/download/{pdb_id}.pdb"
            response = requests.get(url)
            if response.status_code == 200:
                system = response.text
                with open(f"{self.WORK_DIR}/{pdb_id}.pdb", "w") as ofile:
                    ofile.write(system)
            else:
                return f"Failed to download PDB file for {pdb_id}. HTTP Status Code: {response.status_code}"
        if database == "esm":
            url = f"https://api.esmatlas.com/fetchPredictedStructure/{pdb_id}.pdb"
            response = requests.get(url, verify=False)
            if response.status_code == 200:
                system = response.text
                with open(f"{self.WORK_DIR}/{pdb_id}.pdb", "w") as ofile:
                    ofile.write(system)
            else:
                return f"Failed to download PDB file for {pdb_id}. HTTP Status Code: {response.status_code}"

        if database == "afdb":
            url = f"https://alphafold.ebi.ac.uk/files/AF-{pdb_id}-F1-model_v4.pdb"
            response = requests.get(url)
            if response.status_code == 200:
                system = response.text
                with open(f"{self.WORK_DIR}/{pdb_id}.pdb", "w") as ofile:
                    ofile.write(system)
            else:
                return f"Failed to download PDB file for {pdb_id}. HTTP Status Code: {response.status_code}"

        view = py3Dmol.view(height=self.viewer_height, width=self.viewer_width)
        view.addModelsAsFrames(system)
        view.setStyle({"model": -1}, {"cartoon": {"color": "spectrum"}})
        view.zoomTo()
        if self.STREAMLIT_GUI:
            self.VIEW_DICTS[pdb_id] = view
            showmol(view, height=self.viewer_height, width=self.viewer_width)
        else:
            view.show()
        return f"{pdb_id} shows here and saved to {self.WORK_DIR}/{pdb_id}.pdb"

    def get_work_dir(self):
        return self.WORK_DIR

    def get_smiles_from_name(self, compound_name: str):
        # Get CID from compound name
        cid_request_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{compound_name}/cids/TXT"
        cid_response = requests.get(cid_request_url)
        cid = cid_response.text.strip()

        # Get SMILES from CID
        smiles_request_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/property/CanonicalSMILES/TXT"
        smiles_response = requests.get(smiles_request_url)
        smiles = smiles_response.text.strip()

        return f"The SMILES of {compound_name} is {smiles}"

    def display_protein_structure(self, pdb_file):
        try:
            system = open(pdb_file, "r").read()
            view = py3Dmol.view(height=self.viewer_height, width=self.viewer_width)
            view.addModelsAsFrames(system)
            view.setStyle({"model": -1}, {"cartoon": {"color": "spectrum"}})
            view.zoomTo()
            if self.STREAMLIT_GUI:
                self.VIEW_DICTS[pdb_file] = view
                showmol(view, height=self.viewer_height, width=self.viewer_width)
            else:
                view.show()
            return "The protein is showed here!"
        except Exception as e:
            print(f"The error is:\n{e}")
            return "wrong file!"

    def search_rcsb(self, query, max_num=3):
        import biotite.database.rcsb as rcsb

        query = rcsb.BasicQuery(query)
        pdb_ids = rcsb.search(query)
        max_num = min(int(max_num), len(pdb_ids))
        return f"The top {max_num} PDB IDs are {pdb_ids[:max_num]}"

    def blind_docking(self, protein_pdb_file_path, ligand_pdb_file_path, complex_file_path):
        """
        Blind docking between a protein and a ligand
        Parameters:
        - protein_pdb_file_path (str): The path to the protein PDB file.
        - ligand_pdb_file_path (str): The path to the ligand PDB file.
        - complex_file_path (str): The path to save the complex PDB file.

        """
        print('Submitting pocket prediction task...')
        pocket_prediction = submit_pocket_prediction_task(protein_pdb_file_path)
            
        pocket_aas = pocket_prediction['Confident pocket residues'].replace('+', ',')
        if len(pocket_prediction['Confident pocket residues'].split('+')) < 2:
            pocket_aas = pocket_prediction['Likely pocket residues'].replace('+', ',')
        print('Pocket residues:', pocket_aas)
        print('Submitting docking task...')
        docking_code = submit_docking_task(protein_pdb_file_path, ligand_pdb_file_path, aa_list=pocket_aas)
        docking_code = docking_code['hash_code']
        print(docking_code)
        status = ""
        status_prev = ''
        print("status:")
        while status != '"completed"':
            status = query_docking_status(docking_code)
        
            print(f"Debug: {status}")
            if status == '"completed"':
                print("finished")
                save_best_docking_result(docking_code, complex_file_path)
                concate_ligand_to_receptor(complex_file_path, protein_pdb_file_path, complex_file_path)
                log = get_docking_result(docking_code)
                if log.endswith("done.\n"):
                    res_df = parse_vina_output(log)
                    # st.
                    return res_df.to_string()
            else:
                time.sleep(5)
        # save_best_docking_result(docking_code, complex_file_path)
        # concate_ligand_to_receptor(complex_file_path, protein_pdb_file_path, complex_file_path)
        # log = get_docking_result(docking_code)
        # res_df = parse_vina_output(log)
        # while res_df.empty:
        #     log = get_docking_result(docking_code)
        #     res_df = parse_vina_output(log)
        # # print(res_df.to_string())
        # # print(log)
        # return res_df.to_string()


    @handle_file_not_found_error
    def protein_single_point_mutation_prediction(self, pdb_file, mutations):
        pythia_res = query_pythia(pdb_file)
        mutation_res = ""
        for mutation in pythia_res.split("\n"):
            m, score = mutation.split()
            if m in mutations:
                mutation_res += f"{m} {score}\n"
        return mutation_res

    @handle_file_not_found_error
    def recommand_stable_mutations(self, pdb_file, cutoff=-2):
        pythia_res = query_pythia(pdb_file)
        mutation_res = ""
        for mutation in pythia_res.split("\n"):
            m, score = mutation.split()
            if float(score) < float(cutoff):
                mutation_res += f"{m} {score}\n"
        return mutation_res

    @handle_file_not_found_error
    def get_protein_sequence_from_pdb(self, pdb_file, chain_id="A"):
        from Bio.Seq import Seq
        from Bio import SeqIO

        records = SeqIO.parse(pdb_file, "pdb-atom")
        for record in records:
            if record.annotations["chain"] == chain_id:
                return f"The sequnece of chain {chain_id} in pdb file {pdb_file} is {str(record.seq)}"

    @handle_file_not_found_error
    def pocket_prediction(self, pdb_file):
        """
        query pocketapi.cloudmol.org to predict ligand binding sites of input pdb file.
        """

        headers = {"accept": "application/octet-stream",}
        files = { "file": open(pdb_file, "rb"),}
        response = requests.post("https://pocketapi.cloudmol.org/predict", headers=headers, files=files)
        x = response.json()
        system = open(pdb_file, "r").read()
        colors = ["#FF0000", "#FFFF00", "#00FF00", "#00FFFF", "#0000FF"]
        pdbview = py3Dmol.view(height=self.viewer_height, width=self.viewer_width)
        pdbview.addModel(system, "pdb")
        pdbview.setStyle({"cartoon": {"color": "#193f90"}})
        pdbview.setBackgroundColor("white")
        i = 0
        for line in system.split("\n"):
            if len(line) != 0 and line.startswith("ATOM"):
                i += 1
                resn = str(int(line[22:26]))
                color = colors[0]
                if resn in x["Likely pocket residues"].split("+"):
                    color = colors[1]
                if resn in x["Confident pocket residues"].split("+"):
                    color = colors[3]
                if resn in x["Highly confident pocket residues"].split("+"):
                    color = colors[4]
                pdbview.setStyle(
                    {"model": -1, "serial": i}, {"cartoon": {"color": color}}
                )
        pdbview.setStyle({"hetflag": True}, {"stick": {"radius": 0.3}})
        pdbview.zoomTo()
        if self.STREAMLIT_GUI:
            self.VIEW_DICTS["pocket_" + pdb_file.split("/")[-1]] = pdbview
            showmol(pdbview, height=self.viewer_height, width=self.viewer_width)
        else:
            pdbview.show()
        return response.text

    def protein_structure_prediction(self, seq, name):
        """Protein structure prediction"""
        pf = PymolFold()
        pf.set_path(self.WORK_DIR)  # change the path to save results
        pf.query_esmfold(seq, name)
        pdb_filename = os.path.join(pf.ABS_PATH, name) + ".pdb"
        return f"Predicted structure saved as {pdb_filename}"

    def generate_3D_conformation_and_save(self, smiles: str, file_name: str):
        mol = Chem.MolFromSmiles(smiles)
        mol = Chem.AddHs(mol)
        AllChem.EmbedMolecule(mol, AllChem.ETKDG())
        AllChem.MMFFOptimizeMolecule(mol)
        file_name = os.path.join(self.WORK_DIR, file_name)
        writer = Chem.PDBWriter(file_name)
        writer.write(mol)
        writer.close()
        return f"The conformation of {smiles} is saved as {file_name}"
