# PyMOL Recipes Reference

Practical recipes by visualization goal. Each recipe is a working `.pml` snippet —
adapt selections, PDB IDs, and colors to the user's structure.

## Table of Contents
1. [Protein Overview](#protein-overview)
2. [Protein-Ligand Binding Site](#protein-ligand-binding-site)
3. [Protein-Protein Interaction](#protein-protein-interaction)
4. [Active Site / Catalytic Residues](#active-site)
5. [Mutation Site](#mutation-site)
6. [Surface + Cartoon Overlay](#surface-cartoon-overlay)
7. [Multi-Structure Alignment](#multi-structure-alignment)
8. [Goodsell Style](#goodsell-style)
9. [Useful Color Commands](#useful-color-commands)
10. [Distances and Labels](#distances-and-labels)

All recipes assume the base settings from SKILL.md template have been applied.

---

## Protein Overview

```pml
hide everything
show cartoon
dss
util.color_chains("(all) and elem C", _self=cmd)
util.cnc("all", _self=cmd)
orient
```

---

## Protein-Ligand Binding Site

```pml
# define selections — adjust resn/chain as needed
select ligand, resn LIG
select binding, byres (ligand around 4.0) and not ligand
select protein, not ligand and not resn HOH

hide everything

# semi-transparent cartoon for context
show cartoon, protein
set cartoon_transparency, 0.7

# binding residues as sticks (sidechain + CA only)
cmd.show("sticks", "((byres binding) & (sc. | (n. CA) | (n. N & r. PRO)))")
color gray70, binding and elem C
util.cnc("binding", _self=cmd)
set stick_radius, 0.2

# ligand as ball-and-stick
show sticks, ligand
show spheres, ligand
set sphere_scale, 0.25, ligand
set stick_radius, 0.15, ligand
set valence, 1, ligand
color marine, ligand and elem C
util.cnc("ligand", _self=cmd)

# optional: polar contacts
dist hbonds, ligand, binding, mode=2
hide labels, hbonds
set dash_color, black, hbonds
set dash_gap, 0.3
set dash_radius, 0.06

orient ligand
zoom ligand, 6
```

---

## Protein-Protein Interaction

```pml
# adjust chain IDs
select chainA, chain A
select chainB, chain B
select interface_A, byres (chainA within 4.0 of chainB)
select interface_B, byres (chainB within 4.0 of chainA)

hide everything
show cartoon

color lightblue, chainA and elem C
color lightorange, chainB and elem C
util.cnc("all", _self=cmd)

# show interface sidechains
cmd.show("sticks", "((byres interface_A) & (sc. | n. CA))")
cmd.show("sticks", "((byres interface_B) & (sc. | n. CA))")

# optional: transparent surface at interface
create surf_A, interface_A, zoom=0
show surface, surf_A
set transparency, 0.6, surf_A
color lightblue, surf_A

create surf_B, interface_B, zoom=0
show surface, surf_B
set transparency, 0.6, surf_B
color lightorange, surf_B

orient
zoom interface_A or interface_B, 8
```

---

## Active Site

```pml
# adjust residue numbers
select active_site, resi 100+150+200 and chain A
select env, byres (active_site around 5.0) and not active_site

hide everything
show cartoon
set cartoon_transparency, 0.6

# catalytic residues — bold sticks
cmd.show("sticks", "((byres active_site) & (sc. | n. CA))")
color tv_red, active_site and elem C
util.cnc("active_site", _self=cmd)
set stick_radius, 0.25, active_site

# surrounding environment — thinner
cmd.show("sticks", "((byres env) & (sc. | n. CA))")
color gray70, env and elem C
util.cnc("env", _self=cmd)
set stick_radius, 0.15, env

# metal ions if present
show spheres, (active_site or env) and (elem Zn+Mg+Mn+Fe+Cu)
set sphere_scale, 0.4

orient active_site
zoom active_site, 8
```

---

## Mutation Site

```pml
select mut_site, resi 150 and chain A
select mut_env, byres (mut_site around 5.0) and not mut_site

hide everything
show cartoon
set cartoon_transparency, 0.5

cmd.show("sticks", "(byres mut_site) & (sc. | n. CA)")
color tv_red, mut_site and elem C
util.cnc("mut_site", _self=cmd)
set stick_radius, 0.25, mut_site

cmd.show("sticks", "(byres mut_env) & (sc. | n. CA)")
color gray70, mut_env and elem C
util.cnc("mut_env", _self=cmd)
set stick_radius, 0.15, mut_env

orient mut_site
zoom mut_site, 8
```

---

## Surface + Cartoon Overlay

```pml
hide everything
show cartoon
util.color_chains("(all) and elem C", _self=cmd)
util.cnc("all", _self=cmd)

# separate object for surface — controls transparency independently
create surf_obj, all, zoom=0
hide everything, surf_obj
show surface, surf_obj
set transparency, 0.5, surf_obj
cmd.color_deep("white", "surf_obj", 0)

set surface_quality, 1
orient
```

---

## Multi-Structure Alignment

```pml
fetch PDB1, struct1, async=0
fetch PDB2, struct2, async=0
remove solvent
remove elem H

align struct2 and name CA, struct1 and name CA

hide everything
show cartoon
color lightblue, struct1 and elem C
color salmon, struct2 and elem C
util.cnc("all", _self=cmd)

# side-by-side: set grid_mode, 1
orient
```

---

## Goodsell Style

Flat, illustrative look inspired by David Goodsell. Best for surfaces/spheres.

```pml
bg_color white
set ray_trace_mode, 3
set ray_trace_color, black
unset specular
set ray_trace_gain, 0
unset depth_cue
set ambient, 1.0
set direct, 0.0
set reflect, 0.0
set ray_shadow, 0

# pastel palette
set_color gs_blue,  [0.565, 0.714, 0.812]
set_color gs_red,   [0.855, 0.475, 0.427]
set_color gs_green, [0.631, 0.792, 0.596]
set_color gs_tan,   [0.871, 0.812, 0.682]

hide everything
show surface
# color chains with pastels
color gs_blue, chain A
color gs_red, chain B

ray 2400, 2400
```

---

## Useful Color Commands

```pml
# color carbons by chain, then fix element colors
util.color_chains("(all) and elem C", _self=cmd)
util.cnc("all", _self=cmd)

# rainbow by residue number
util.chainbow("all and not het")

# color by secondary structure
color red, ss h        # helices
color yellow, ss s     # sheets
color green, ss l+''   # loops

# B-factor / pLDDT coloring
spectrum b, blue_white_red, all

# custom color by hex
color 0x7EB6D9, chain A and elem C

# colorblind-safe palette (Wong 2011)
set_color cb_orange,     [0.902, 0.624, 0.000]
set_color cb_skyblue,    [0.337, 0.706, 0.914]
set_color cb_green,      [0.000, 0.620, 0.451]
set_color cb_blue,       [0.000, 0.447, 0.698]
set_color cb_vermillion, [0.835, 0.369, 0.000]
set_color cb_purple,     [0.800, 0.475, 0.655]
```

---

## Distances and Labels

```pml
# polar contacts
dist hbonds, sele1, sele2, mode=2
hide labels, hbonds
set dash_color, black, hbonds
set dash_gap, 0.3
set dash_radius, 0.06

# labels (better to add in Inkscape/Illustrator post-export)
label name CA and resi 100+150, "%s%s" % (resn, resi)
set label_color, black
set label_size, 16
set label_font_id, 7
set label_position, [0.0, 0.0, 2.0]
```
