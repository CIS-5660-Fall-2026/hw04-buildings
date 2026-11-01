# HW04 User Guide

## Open the project

Open `hw04.hipnc` in Houdini Apprentice 22.0 and select `/obj/TERRACE_WEAVE/BUILDING_GENERATOR`. The default scene is the four-storey timber variation.

The HDA definition, modeling logic and materials are embedded in the HIP. No external textures or plugins are needed to open the project.

## Controls

- **Building:** switch between the two presets; adjust each floor's width, depth, height and X/Z offsets; change the alternating recesses and setbacks.
- **Components:** adjust window, door and balcony dimensions, along with pane count, door configuration and railing spacing.
- **Details:** toggle terraces, balconies, overhang supports, floor borders, facade uprights and furniture.

Double-click the generator to inspect the Box, Copy to Points and component networks. `CTRL_WINDOW`, `CTRL_DOOR` and `CTRL_BALCONY` are the component Null controllers.

If the viewport clips the building when zoomed in, select the generator and press **Space + G** to frame it before orbiting.

## Files

- `hw04.hipnc`: Houdini project with the embedded HDA.
- `README.md`: project description, architectural references, renders and an inline tool demo.
- `images/`: main view, five-storey variation and terrace detail.
- `media/tool_demo.mp4`: parameter demonstration recorded in Houdini.
- `references/` and `REFERENCES.md`: reference images and source credits.
- `source/`: generator code and a standalone layout check. These scripts do not need to be run to open the HIP.
- `validation.json` and `build-report.json`: saved validation results.

The project was saved with Houdini Apprentice and uses the non-commercial `.hipnc` format.
