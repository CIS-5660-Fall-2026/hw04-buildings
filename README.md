# CIS 5660 HW04 Procedural Buildings

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
