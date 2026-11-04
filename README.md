# Procedural Building

**Procedural Controls Demo**

![Procedural controls demonstration](media/video/building_controls_demo.gif)

For this project, I wanted to recreate the architectural styles seen in China from the 1980s through the early 2000s. The design is inspired by Chinese dreamcore, an aesthetic used in games and visual art. It evokes the uncanny atmosphere of the Backrooms while drawing on nostalgic environments that many young people in China remember from childhood.

## Part 0: Setup and Planning

The project explores a dense residential building style with projecting balconies, protective window cages, exposed utilities, and vertical signs. A shared set of adjustable components supports different floor arrangements and facade proportions.

### Architectural References

| Dense Facades and Projecting Signs | Caged Balconies and Exterior Equipment |
| --- | --- |
| ![Dense facades and projecting signs](media/references/dense_facade_reference.jpeg) | ![Caged balconies and exterior equipment](media/references/caged_balconies_reference.webp) |
| The closely packed facade modules and projecting signs inform the building's dense layout and outward-facing billboards. | The enclosed balconies, repeated metal railings, and exterior air conditioners inform the balcony styles, window cages, and attached equipment. | Image source: [Aesthetics Wiki](https://aesthetics.fandom.com/wiki/File:CDream-1.png). |

## Part 1: Box Stacking HDA

Each floor has its own width, height, and depth. Its elevation follows the accumulated height of the floors below, allowing changes in footprint to create setbacks and overhangs. Floor count and per-floor dimensions control the overall silhouette.

![Complete building](media/overview/building.png)

### Building Variations

Changing the floor count and individual floor dimensions produces different building forms while retaining the same placement rules. The examples show how setbacks and wider overhangs affect the distribution of facade assets and supports.

| Original arrangement | Alternate arrangement |
| --- | --- |
| ![Original building](media/overview/building.png) | ![Alternate building](media/variants/building_variant_02.png) |

### Alternate Building Views

![Rear view](media/variants/building_variant_02_back.png)

![Side view](media/variants/building_variant_02_side.png)

![Opposite view](media/variants/building_variant_02_high.png)

### Node Screenshot

![Floor stack node network](media/nodes/floor_stack.png)

## Part 2: Add Details

### Windows

Window groups are generated within a minimum and maximum count range. Each group carries its actual width into the layout process, so increasing the number of windows also increases the space it occupies along the facade.

![Window variations](media/modules/windows.png)

#### Window Count

| Narrow window group | Medium window group | Wide window group |
| --- | --- | --- |
| ![Narrow window group](media/modules/windows_1.png) | ![Medium window group](media/modules/windows_2.png) | ![Wide window group](media/modules/windows_4.png) |

#### Node Screenshot

![Window node network](media/nodes/windows.png)

### Window Cages

The protective cage adapts to the window group's dimensions. A probability parameter determines whether a cage is included, with a floor-based random seed making the choice repeatable across that floor.

![Window cage](media/modules/window_cap.png)

#### Node Screenshot

![Window cage node network](media/nodes/window_cap.png)

### Sliding Doors

Door panels fit the balcony's opening, and their positions along the track depend on the enclosure parameter. Each balcony instance receives a randomized enclosure value, creating different opening amounts across the facade.

![Sliding doors](media/modules/sliding_doors.png)

#### Door Closure

| Closed doors | Partially open doors | Open doors |
| --- | --- | --- |
| ![Closed doors](media/modules/doors_000.png) | ![Partially open doors](media/modules/doors_050.png) | ![Open doors](media/modules/doors_100.png) |

#### Node Screenshot

![Sliding door node network](media/nodes/sliding_doors.png)

### Covered Balconies

Covered balconies adapt to the floor height while reserving clearance above. Their opening bounds define both the door's fitted size and the corresponding cutout in the building wall. The dense railings and corrugated cover distinguish this balcony style.

![Covered balcony](media/modules/balcony_1.png)

#### Node Screenshot

![Covered balcony node network](media/nodes/balcony_1.png)

### Open Balconies

Open balconies use a lighter railing arrangement. The balcony and its opening remain aligned as dimensions change, keeping the fitted doors and wall cutout consistent with the visible asset.

![Open balcony](media/modules/balcony_2.png)

#### Node Screenshot

![Open balcony node network](media/nodes/balcony_2.png)

### Facade Layout and Openings

The layout chooses between balcony styles and window groups using adjustable selection weights. It uses each asset's bounding width and the available wall length to arrange the selected pieces, with spacing and corner checks constraining placement. Window count variants share the overall window weight.

The visible asset and its opening bounds travel together through placement. The bounds then define the wall cutout, keeping the opening aligned with the chosen asset.

![Facade layout and openings](media/modules/layout_boolean.png)

#### Node Screenshot

![Facade layout node network](media/nodes/layout_boolean.png)

## Part 3: Pillars and Border

Floor borders follow each floor's footprint. Repeated posts and connecting rails form the rooftop perimeter; a final-floor condition enables this additional assembly only at the top.

![Roof and railings](media/modules/roof_railings.png)

### Node Screenshot

![Roof and railing node network](media/nodes/roof_railings.png)

## Part 4: Supports

Candidate positions beneath each floor are projected downward toward the lower floors or ground. The distance to the hit determines the support length, and segments below a minimum length are discarded. The support-width parameter controls both thickness and the inset beneath the floor.

![Overhang supports](media/modules/overhang_supports.png)

### Node Screenshot

![Support node network](media/nodes/overhang_supports.png)

## Part 5: Feature of Your Choice

### Water Pipes

The assembled floor boundaries provide a connected routing network. A shortest-path search connects selected upper and lower positions, while branches follow floor edges and outlet extensions turn away from the building. Overlapping paths are consolidated before becoming pipes.

Connection collars follow the local path direction. Pipe thickness and collar spacing control their appearance.

![Water pipes](media/modules/water_pipes.png)

#### Node Screenshot

![Water pipe node network](media/nodes/water_pipes.png)

## Extra Credit

### Electrical Wires

Attachment positions follow the floor perimeter. Corresponding points in a shared cross-section pattern connect into continuous wires, preserving their order around the building. Selected spans curve downward while their attachment points and corner sections remain fixed.

Wire thickness, count range, sagging percentage, sag depth, and variation control the result. A random seed changes the arrangement while keeping it reproducible.

![Electrical wires](media/modules/electrical_wires.png)

#### Wire Sagging

| Straight wires | Sagging wires |
| --- | --- |
| ![Straight wires](media/modules/wires_000.png) | ![Sagging wires](media/modules/wires_100.png) |

#### Node Screenshot

![Electrical wire node network](media/nodes/electrical_wires.png)

### Vertical Billboards

Vertical facade edges provide candidate locations and determine the billboard height. Orientation comes from the horizontal vector between the floor center and the placement position: an axis is selected, and its sign determines which way the billboard extends. The panel's facing direction is adjusted consistently with that outward direction.

![Vertical billboards](media/modules/billboards.png)

#### Node Screenshot

![Billboard node network](media/nodes/billboards.png)

### Air Conditioners

An imported air-conditioner model is positioned relative to each balcony, so it follows the balcony's placement as part of the assembled asset.

![Air conditioner](media/modules/air_conditioner.png)

#### Node Screenshot

![Air conditioner node network](media/nodes/air_conditioner.png)

### Rendered Presentation

The completed building and its components are presented with neutral shading, lighting, and a background. The rendered sequence shows the building variations, isolated features, and parameter changes.

[![Building demonstration](media/video/building_demo.gif)](media/video/building_demo.mp4)

[Watch the video](media/video/building_demo.mp4)
