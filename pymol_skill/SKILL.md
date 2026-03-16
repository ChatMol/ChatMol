---
name: pymol-visualization
description: >
  Generate publication-quality molecular visualization images using PyMOL.
  Use this skill whenever the user mentions PyMOL, molecular visualization,
  protein rendering, structure figures, PDB visualization, ray tracing
  molecules, or wants to create images of proteins, ligands, binding sites,
  protein-protein interactions, or any biomolecular structure. Also trigger
  when the user wants to: make a figure of a crystal structure for a paper
  or presentation; render a protein surface; show binding pockets; visualize
  protein-ligand interactions; create Goodsell-style illustrations; produce
  cartoon representations with highlighted residues; compare multiple
  structures side by side; or generate any molecular graphics output —
  even if they don't mention "PyMOL" by name. Trigger for any request
  involving PDB files, molecular surfaces, cartoon ribbons, stick models,
  electron density, or structural biology figures.
---

# PyMOL Visualization Skill

Generate publication-quality molecular structure images using PyMOL.

## Prerequisites

PyMOL must be installed. Check with:
```bash
pymol -c -q -e "print('ok')" 2>/dev/null && echo "PyMOL available" || echo "PyMOL not found"
```
If missing: `conda install -c conda-forge pymol-open-source`.

## Workflow

### 1. Ask the User

Before writing any script, clarify:
- **Structure**: PDB ID, uploaded file path, or AlphaFold model?
- **Goal**: What does the figure show? (e.g. protein overview, binding site, PPI interface, active site, mutation, surface, alignment)
- **Style preference**: Any preferred colors or theme? Journal figure vs. presentation vs. artistic?

### 2. Write a .pml Script and Run It

```bash
pymol -c -q script.pml
```
`-c` = no GUI (headless), `-q` = quiet. For Python API logic, use `pymol -c -q -r script.py`.

### 3. Read the Reference Before Writing

Read `references/recipes.md` before writing — it contains scene-specific recipes and
essential PyMOL commands organized by visualization goal.

### 4. Deliver Output

Always deliver **three files**:
1. **PNG image** — the rendered figure
2. **PML script** — so the user can reproduce or tweak
3. **PSE session** — so the user can open in PyMOL GUI and adjust interactively

Save all to user's desktop and use `present_files`.

## Script Template

Every script should follow this structure:

```pml
reinitialize

# --- Load ---
fetch 4HHB, async=0
# or: load /path/to/structure.pdb, myprotein

# --- Clean ---
remove solvent
remove elem H
set valence, 0

# --- Base look ---
bg_color white
space cmyk
set ray_shadow, 0
set ray_trace_mode, 1
set antialias, 3
set ambient, 0.5
set spec_count, 5
set shininess, 50
set specular, 1
set reflect, 0.1
set orthoscopic, on
set opaque_background, off
set cartoon_oval_length, 1
set cartoon_rect_length, 1
set cartoon_discrete_colors, on
dss

# --- Representation (scene-specific) ---
hide everything
show cartoon
# ...

# --- Color ---
util.color_chains("(all) and elem C", _self=cmd)
util.cnc("all", _self=cmd)

# --- Camera ---
orient
# zoom sele, 8

# --- Save session BEFORE ray tracing ---
save /mnt/user-data/outputs/structure.pse

# --- Render ---
ray 2400, 1800
png /mnt/user-data/outputs/structure.png, dpi=150
quit
```

## Essential Patterns

**Show sidechains cleanly:**
```pml
cmd.show("sticks", "((byres (sele)) & (sc. | (n. CA) | (n. N & r. PRO)))")
```

**Molecule-agnostic coloring:**
```pml
util.color_chains("(sele) and elem C", _self=cmd)
util.cnc("sele", _self=cmd)
```

**Surface + cartoon as separate objects:**
```pml
create surf_obj, sele, zoom=0
show surface, surf_obj
set transparency, 0.5, surf_obj
cmd.color_deep("white", "surf_obj", 0)
```

**Ball-and-stick for ligands:**
```pml
show sticks, ligand
show spheres, ligand
set sphere_scale, 0.25, ligand
set stick_radius, 0.15, ligand
```

**Goodsell style (flat, illustrative):**
```pml
set ray_trace_mode, 3
set ray_trace_color, black
unset specular
set ray_trace_gain, 0
unset depth_cue
set ambient, 1.0
set direct, 0.0
set reflect, 0.0
```

## Key Rules

1. **Always `space cmyk`** for print colors
2. **Always `remove elem H`** unless user needs hydrogens
3. **Always save `.pse`** before ray tracing — this is the user's editable session
4. **`set valence, 0`** unless showing ligand bond orders
5. **Create separate objects** for surface overlays (transparency is per-object)
6. **Use `async=0`** with `fetch` — otherwise structure isn't loaded when next command runs
7. **End script with `quit`** — otherwise PyMOL hangs in batch mode
8. **Render large** (1200x900+) — downscale later for quality
