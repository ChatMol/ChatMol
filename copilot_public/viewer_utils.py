import py3Dmol
import base64
from stmol import showmol
from string import ascii_uppercase, ascii_lowercase

alphabet_list = list(ascii_uppercase + ascii_lowercase)


# Color selection
color_options = {"Confidence": "pLDDT", "Rainbow": "rainbow", "Chain": "chain"}

pymol_color_list = [
    "#33ff33",
    "#00ffff",
    "#ff33cc",
    "#ffff00",
    "#ff9999",
    "#e5e5e5",
    "#7f7fff",
    "#ff7f00",
    "#7fff7f",
    "#199999",
    "#ff007f",
    "#ffdd5e",
    "#8c3f99",
    "#b2b2b2",
    "#007fff",
    "#c4b200",
    "#8cb266",
    "#00bfbf",
    "#b27f7f",
    "#fcd1a5",
    "#ff7f7f",
    "#ffbfdd",
    "#7fffff",
    "#ffff7f",
    "#00ff7f",
    "#337fcc",
    "#d8337f",
    "#bfff3f",
    "#ff7fff",
    "#d8d8ff",
    "#3fffbf",
    "#b78c4c",
    "#339933",
    "#66b2b2",
    "#ba8c84",
    "#84bf00",
    "#b24c66",
    "#7f7f7f",
    "#3f3fa5",
    "#a5512b",
]


def show_pdb(
    pdb_str,
    show_sidechains=False,
    show_mainchains=False,
    color="rainbow",
    chains=None,
    vmin=0.5,
    vmax=0.9,
    size=(550, 550),
    hbondCutoff=4.0,
    show_ligands=True,
    Ls=None,
    animate=False,
):
    if chains is None:
        chains = 1 if Ls is None else len(Ls)
    view = py3Dmol.view(
        js="https://3dmol.org/build/3Dmol.js", width=size[0], height=size[1]
    )
    if animate:
        view.addModelsAsFrames(pdb_str, "pdb", {"hbondCutoff": hbondCutoff})
    else:
        view.addModel(pdb_str, "pdb", {"hbondCutoff": hbondCutoff})
    if color == "pLDDT":
        view.setStyle(
            {
                "cartoon": {
                    "colorscheme": {
                        "prop": "b",
                        "gradient": "roygb",
                        "min": vmin,
                        "max": vmax,
                    }
                }
            }
        )
    elif color == "rainbow":
        view.setStyle({"cartoon": {"color": "spectrum"}})
    elif color == "chain":
        for n, chain, color in zip(range(chains), alphabet_list, pymol_color_list):
            view.setStyle({"chain": chain}, {"cartoon": {"color": color}})
    if show_sidechains:
        BB = ["C", "O", "N"]
        view.addStyle(
            {
                "and": [
                    {"resn": ["GLY", "PRO"], "invert": True},
                    {"atom": BB, "invert": True},
                ]
            },
            {"stick": {"colorscheme": f"WhiteCarbon", "radius": 0.3}},
        )
        view.addStyle(
            {"and": [{"resn": "GLY"}, {"atom": "CA"}]},
            {"sphere": {"colorscheme": f"WhiteCarbon", "radius": 0.3}},
        )
        view.addStyle(
            {"and": [{"resn": "PRO"}, {"atom": ["C", "O"], "invert": True}]},
            {"stick": {"colorscheme": f"WhiteCarbon", "radius": 0.3}},
        )
    if show_mainchains:
        BB = ["C", "O", "N", "CA"]
        view.addStyle(
            {"atom": BB}, {"stick": {"colorscheme": f"WhiteCarbon", "radius": 0.3}}
        )
    if show_ligands:
        view.setStyle({"hetflag": True}, {"stick": {"radius": 0.3}})
    view.zoomTo()
    if animate:
        view.animate()
    return view

def update_view(
    view,
    show_sidechains=False,
    show_mainchains=False,
    color="rainbow",
    chains=None,
    vmin=0.5,
    vmax=0.9,
    hbondCutoff=4.0,
    show_ligands=True,
    Ls=None,
    animate=False,
):
    if chains is None:
        chains = 1 if Ls is None else len(Ls)

    # Apply styles to the existing view model
    if color == "pLDDT":
        view.setStyle(
            {
                "cartoon": {
                    "colorscheme": {
                        "prop": "b",
                        "gradient": "roygb",
                        "min": vmin,
                        "max": vmax,
                    }
                }
            }
        )
    elif color == "rainbow":
        view.setStyle({"cartoon": {"color": "spectrum"}})
    elif color == "chain":
        for n, chain, color in zip(range(chains), alphabet_list, pymol_color_list):
            view.setStyle({"chain": chain}, {"cartoon": {"color": color}})
    if show_sidechains:
        BB = ["C", "O", "N"]
        view.addStyle(
            {
                "and": [
                    {"resn": ["GLY", "PRO"], "invert": True},
                    {"atom": BB, "invert": True},
                ]
            },
            {"stick": {"colorscheme": f"WhiteCarbon", "radius": 0.3}},
        )
        view.addStyle(
            {"and": [{"resn": "GLY"}, {"atom": "CA"}]},
            {"sphere": {"colorscheme": f"WhiteCarbon", "radius": 0.3}},
        )
        view.addStyle(
            {"and": [{"resn": "PRO"}, {"atom": ["C", "O"], "invert": True}]},
            {"stick": {"colorscheme": f"WhiteCarbon", "radius": 0.3}},
        )
    if show_mainchains:
        BB = ["C", "O", "N", "CA"]
        view.addStyle(
            {"atom": BB}, {"stick": {"colorscheme": f"WhiteCarbon", "radius": 0.3}}
        )
    if show_ligands:
        view.setStyle({"hetflag": True}, {"stick": {"radius": 0.3}})
    view.zoomTo()

    if animate:
        view.animate()

    return view

def plot_plddt_legend(dpi=100):
    thresh = ["pocket probability:", "<50", "60", "70", "80", ">90"]
    plt.figure(figsize=(1, 0.1), dpi=dpi)
    for c in ["#FFFFFF", "#FF0000", "#FFFF00", "#00FF00", "#00FFFF", "#0000FF"]:
        plt.bar(0, 0, color=c)
    plt.legend(
        thresh,
        frameon=False,
        loc="center",
        ncol=6,
        handletextpad=1,
        columnspacing=1,
        markerscale=0.5,
    )
    plt.axis(False)
    return plt