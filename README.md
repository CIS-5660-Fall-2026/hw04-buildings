# CIS 5660 HW04 Procedural Buildings

## NORTH / Residences

One procedural building tool produces two contemporary apartment studies: **A / Terraces**, a wide four-floor building with a stepped roofline, and **B / Shift**, a narrower six-floor building with projecting volumes and automatic support brackets. Pale walls, charcoal frames, blue-gray glazing and bronze details connect the two designs.

![NORTH / Residences — both presets](renders/residences_beauty.png)

**[Watch the tool demonstration (MP4, 50 seconds)](video/tool_demo.mp4)** · **[Download the Houdini scene](hw04_residences.hipnc)**

The silent video renders 24 actual parameter states in Houdini: floor count, window dimensions and mullions, door dimensions and single/double leaves, balcony dimensions and railing styles, floor detail toggles, overhang support creation/removal, and random seed variation. Captions report the parameters used for each frame. It is an automated rendered parameter demonstration, not a screen recording of mouse interaction.

### Open and use

1. Open `hw04_residences.hipnc` in Houdini. Created and checked with **Houdini 21.0.512 Apprentice** and **SideFX Labs 21.0.512 Production**. The `.hipnc` extension and render watermark are from the Apprentice license.
2. Select `/obj/BUILDING_A/BUILDING_GENERATOR` or `/obj/BUILDING_B/BUILDING_GENERATOR`. Both are instances of the same `cis5660::hw04_residences::1.0` HDA. Use **Load A — Terraces** or **Load B — Shift** to apply the corresponding massing and facade preset.
3. Change floor count, then edit each floor's width, height, depth, X/Z offsets, columns and balconies. The **Doors / Windows / Balconies** section controls the models and automatic supports. Keep openings smaller than the floor height and footprints large enough to hold a facade bay.
4. Inside the generator, the original model controls are the Null nodes `WINDOW_CTRL`, `DOOR_CTRL` and `BALCONY_CTRL`. Their channels are linked to the exposed HDA controls. The native modeling networks are under `WINDOW_ASSETS`; the network chapters are labeled for inspection.
5. Use `/obj/BEAUTY_CAMERA` for the paired view. `/out/PREVIEW` produces the fast preview; `/out/BEAUTY_RENDER` produces the lit render. Output paths use `$HIP/renders`.

The main building HDA and the required Labs split-normal HDA definition are **embedded in the HIP file**. Opening the scene does not require a separate HDA file or the source scripts. A clean-preferences test opened and cooked the scene with no Labs package loaded beforehand.

### Assignment implementation

| Requirement | Implementation |
| --- | --- |
| Part 0 — planning | Two ODA references below, selected and documented before implementation. |
| Part 1 — box stacking HDA | Lab 06 feedback stack and Match Size workflow, packaged in an embedded HDA with two independent scene instances. |
| Part 2 — original assets | Native Houdini models for windows, doors and balconies; separate Null controls for each. Windows: width, height, mullions. Doors: width, height, single/double. Balconies: width, railing height, depth, spacing and railing style. Chain-based placement, ID-based asset copies and Boolean wall openings are retained. |
| Part 3 — pillars and borders | Corner columns and swept profiles following each floor outline, with per-floor column controls. |
| Part 4 — supports | Compare the current floor underside with the previous structural footprint. Sample the unsupported outline, ray-project connection points onto the previous floor and sweep diagonal brackets. Supports disappear when footprints align and can be disabled globally. |
| Part 5 — extension | Independent X/Z offsets for every floor; the facade, roof, entrance and supports respond to the altered massing. Preset buttons and per-floor balcony toggles extend the interface. |
| Presentation | Shared material palette, ground, lighting, camera, two-building render and parameter demonstration video. |

The support system targets **axis-aligned rectangular floors with overlapping footprints**. Its brackets are a visual procedural model; disconnected floors and rotated or arbitrary footprints are outside this implementation's scope. Preset A steps inward and has no floor-overhang supports; preset B deliberately includes overhangs that exercise the support network.

### Validation and reproducibility

All **14 parameter checks pass**; results are in [the validation report](validation/parameter_checks.json). Checks cover both presets, Null-driven dimensions, independent HDA instances, railing styles, seed changes and repeatability, per-floor toggles, support enable/disable, aligned and shifted footprints, removal of an overhang, and one- and seven-floor stacks. They also check finite geometry, facade placement on all four sides, roof elevation and node errors. [Build diagnostics](validation/build_diagnostics.json) contain no node errors.

The saved scene is ready to open. To rebuild using Houdini's `hython` executable, run from the repository directory:

```text
hython scripts/build_hw04.py --render --beauty
hython scripts/validate_hw04.py
hython scripts/render_demo.py
```

`source/lab06_base.hipnc` preserves the Lab 06 starting point; `scripts/` contains the reproducible construction, validation and demonstration scripts; `presets.json` records the two preset configurations. The video script uses Houdini's bundled FFmpeg encoder. The embedded Labs definition retains its upstream license in [licenses/SideFXLabs-LICENSE.md](licenses/SideFXLabs-LICENSE.md).

## Original design plan and references

Style: contemporary modular apartments with pale concrete, charcoal metal frames,
blue-gray glazing and warm metal accents. Two presets of one HDA will interpret
the following buildings at a reduced, course-appropriate scale. These are stylized
studies of facade rhythm and massing, not exact architectural reconstructions.

### Reference A — ODA, 251 1st Street

![251 1st Street reference](references/251-first.jpg)

Source: [ODA project page](https://oda-architecture.com/projects/251-1st/).
Photography credits listed by ODA: Frank Oudeman and Imagen Subliminal.
Reference image reproduced here solely for educational visual study; copyright
remains with its respective owner.

Preset A will translate the pale horizontal bands, dark framed glazing and
terraced outdoor space into a four-floor, wide apartment building with balconies
and a smaller upper floor.

### Reference B — ODA, 2222 Jackson

![2222 Jackson reference](references/2222-jackson.jpg)

Source: [ODA project page](https://oda-architecture.com/projects/2222-jackson/).
Photography credits listed by ODA: Imagen Subliminal and Pavel Bendov.
Reference image reproduced here solely for educational visual study; copyright
remains with its respective owner.

Preset B will use six narrower floors, offset and projecting volumes, repeated
glazed bays and metal railings. Visible support brackets are an intentional
industrial interpretation added to demonstrate Part 4 of the assignment.

### Planned procedural work

- Retain Lab 06's feedback stack, normal-based walls, Chain placement and ID-based
  Boolean window/door openings.
- Build original parameterized windows, doors and balconies with a dedicated
  Null control node for each type.
- Sweep border profiles around floor outlines and copy columns at floor corners.
- Detect actual floor overhangs against the previous structural floor; create
  supports only where an overhang exists and a lower-floor connection is valid.
- Add independent X/Z floor offsets as Part 5. Use the same HDA for both presets.
- Deliver an embedded HDA scene, renders, validation results and a parameter
  demonstration video.

---

## Project Overview
In this homework, you will continue creating procedural buildings based on the work you did in lab 06. The tutorial used for that lab and this homework can be found at [this URL](https://www.youtube.com/watch?v=uIe97023sDk&t=979s&ab_channel=SimonHoudini).

## Part 0: Setup and Planning 
### SideFX Labs 
If you didn't install SideFX Labs during lab 06, make sure you do so for this homework. You can do so at the “Labs/Packages” tab of the Houdini Launcher. Make sure that the version of Labs that you install is not newer than your overall Houdini install (e.g. if you have Houdini 21.544, don't install Labs 22.650). Use the Production version of Labs, not the Daily.

### Project Planning
Before implementing any Houdini nodes or VEX code, take some time to look at different architectural styles (realistic or fictional). Decide on two different buildings that use the architectural style you chose, and add to this README concept art or photographs of your chosen buildings, citing your sources. You will be using the techniques you practiced in Lab 06 to procedurally generate buildings modeled after the ones you selected. Your buildings should be stylistically similar enough that your tool can be used to create either one by modifying its parameters.

Do make sure that what you choose is manageable given your knowledge Houdini and what is taught in the tutorial. Of course, you’re welcome to adapt the setup to support additional logic/features to match your style, and particularly complex additions could merit extra credit :) On the other hand, if you’re newer to Houdini and want to stick relatively close to the tutorial, that’s okay too. Just be sure to think through what changes your chosen buildings will require (additional assets? different placement logic?) before diving into the project so you don’t bite off more than you can chew.  
Here are a few examples of possible building styles that could be a decent fit for inspiration:
CIS 5660 HW03 Procedural Building 1 
https://www.behance.net/gallery/23773965/ISOBuilding-concept-art 

https://www.artstation.com/artwork/m6xYy 

## Part 1: Box Stacking HDA
As you did in lab 06, follow the tutorial to make a simple HDA that stacks boxes on each other.  Important note about HDA creation:  
Creating an HDA saves a .hda file at the location you specify with the definition of your HDA. Be sure to submit this .hda file along with your .hip file so we can see the contents of your tool.  
Alternatively, when you save your HDA you can choose the “Embedded in HIP File” option (rather than specifying the path), and the hda definition will be automatically embedded in your hip file (and no additional files will be needed with submission).  

## Part 2: Add Details
Next, Simon adds details to the boxes to create floors by refining the shape and adding details like windows, doors, and balconies.  
Create your own models for windows, doors, and balconies based on your chosen style using Houdini. For each of the three types, create a Null “control” node with parameters that affect your window/door/balcony output (similar to how we made a control node for the jellyfish).  
You should have parameters to drive the width and height of the doors, windows, and balconies, as well as at least one other parameter of your choosing on each one (ex: double vs single doors, windows with and without shutters, and type of balcony railing). Apart from that, you can go as simple or complex as you like!  
Then follow Simon’s setup to integrate your windows, doors, and balconies into your buildings.  

## Part 3: Pillars and Border
Continue following the tutorial to add pillars and borders to each floor. Depending on your chosen style, your building may not make use of pillars. In this case, still use the technique shown to add horizontally-instanced elements of some kind to your building.

## Part 4: Supports
Continue following the tutorial to add supports to floors that overhang other floors.  

## Part 5: Feature of your choice
Throughout the tutorial, Simon mentions ways you could extend his project setup. Implement any of his suggestions: 
- More complex logic for creating supports (handle different length supports differently) Add more parameters to the user interface (for example, x and z offset options) UV and shade your models 
- Add a “manual node” where users can control detail placement manually 
- Add additional types of feature models (like fire escapes or chimneys). Note that, depending on what you choose, you might need to add new logic to integrate them into your building (ex: chimneys go on top instead of being chained on the side, fire escapes should be on one side of the building and go all the way down). We’ll award more extra credit accordingly.  
- Add some flair to your scene by dressing together multiple buildings or additional procedural props or background elements 

## Extra Credit
Take some time to make your building demo-reel worthy, and render it with materials, a background, and lighting!

## Submission
Update your README with 
A description of your project 
A video of your building tool in action 
Create a pull request to this repository 
Submit your Houdini file to Canvas along with a link to your pull request 
IMPORTANT NOTE: make sure your HDA is either embedded in the HIP file or included with your submission (see the instructions under “Part 1: Box Stacking HDA” for additional details).
