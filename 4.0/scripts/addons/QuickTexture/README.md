# QuickTexture

## Welcome to the QuickTexture Documentation!
With QuickTexture you can create extremely complicated multi-layer shaders blazingly fast without ever touching a single node. Control maps individually and blend between textures with a variety of masks.

## Workflow Overview
- Choose how you want your texture applied (UV Mode, Decal, etc) and then create the QuickTexture  
- Select the textures you want to use in the window that pops up
- While you are on the main map and the main layer, control the settings available to you in the UI via the displayed hotkeys  
- Switch to different maps to change settings, potentially previewing the final result as needed  
- Add masks and new layers and go back and forth changing settings until your final result has been reached  
- You can create extremely complicated multi layer materials with all kinds of masks in an unbelievably short amount of time, then add decals and paintovers on top and potentially bake the texture down to a single map for export if needed  
- If you have a QuickTexture on your object and you want to add a new QuickTexture to a specific face or faces, select them in edit mode then activate QuickTexture  
- When the object already has a material on it, be it from Megascans or anywhere else, running QuickTexture will take the maps and use them in a QuickTexture Material so you can instantly convert your materials and begin tweaking them and adding layers and masks
- Bake your Textures or add Mesh Decals and Paintover objects using the tools described below

## Preferences
**Viewport Drawing Border** will decrease the amount of available working area in the viewport. This might be useful if you have some gizmo you need to use without having to close down the tool  
**Text Size** controls the font size in the UI when running QuickTexture  
**Mouse Speed Multiplier** Most values in QuickTexture are determined by pressing a button, moving your mouse to increment a value, and then left clicking to confirm. This is the strength of that incrementation, you may have to adjust based on your monitor resolution or DPI  
**Colors** allow for UI theme customization  
**Image Editor Path** Select the .EXE file to use for Paintovers  
**UV Mode** Choose your default UV Mode when creating a QT  
- Triplanar  
- Procedural Box is a Procedural Triplanar. Unlike a Triplanar which is always generating based on object location, you can "Freeze" Procedural Box at any time by applying the modifier  
- UV will use the object's existing UV's or create a basic Smart UV unwrap if it doesn't detect any
- View will do a UV View Projection from the current view  
- If an object is not selected, then depending on which UV mode you have you will again receive a different result.  
- UV will create a Reference Plane which is a simple plane with the selected image texture and no modifiers  
- Procedural Box will create a Photomodeling Plane which unlocks interesting workflows such as using QuickShape with Modifiers From Active selected and drawing shapes with the texture of the photomodeling plane underneath. This is described in greater detail in the QuickShape docs  

**Multilayer** will create a QuickTexture with 3 layers from one set of selected images in one click. The second layer has added value and uses an Edgewear mask and the third layer has decreased value and uses a Dirt mask. Make sure you are in Cycles to see the effect of these masks  
**Decal Resolution** is a subdivision applied to the decal mesh  
**Decal Offset** is an offset off the surface of the mesh that the decal is projected onto  
**Paintover Resolution** is a multiplier of the viewport size  
**Paintover Resolution** is a subdivision applied to the paintover mesh  
**Paintover Offset** is an offset off the surface of the mesh that paintover is projected onto  
**Maps** QuickTexture places maps in slots based on what it finds in the filename. All the usual names are covered by default, but you can add any keywords you like here to any of the maps  

## Hotkeys
Most of the hotkeys in QuickTexture are not customizable, as generally the entire keyboard is in use and you do not need any Blender tools when inside QT. However, the main keys to launch QuickTexture, QuickDecal etc can be changed! Visit the Keymap Section of Blender Preferences and search for QuickTexture to find the customizable keys  
Consult the QuickTools Panel for a full list of all the hotkeys  

**Ctrl T** Open and Close QuickTexture (You can also close by pressing the Left Mouse button)  
**Ctrl D** QuickMenu containing helpful tools  
**Ctrl Shift D** Create QuickDecal at your mouse cursor  
**Shift Alt D** Create QuickPaintover at your mouse cursor  
**G** Move  
**S** Scale  
**R** Rotate  
**Shift S** Scale along X  
**Alt S** Scale along Y  
**Brackets** Rotate 90 Degrees  
**P** Reproject from View (Useful for View QuickTexture Layers and occassionaly Decals)  
**Tab** Preview Final Texture while keeping settings active from other maps or masks  
**K** Reset All Settings  

## Layers
QuickTexture supports a maximum of 5 Layers  
**Ctrl B** Procedural Box  
**Ctrl V** View  
**Ctrl T** Triplanar  
**Q** Previous Layer  
**W** Next Layer  
**Shift D** Duplicate Layer  
**Del** Delete Layer  
**Ctrl Num** Switch between all of the QuickTexture Materials on your object (only possible if you have created a QuickTexture, then gone into Edit Mode and selected a face and ran QuickTexture again)  

## Maps
Settings are applied per map, so if you are in the combined map it will adjust all of the maps, if you are in ie: roughness it will only adjust the roughness map  
**1** View Combined Texture Maps of the current Layer  
**2** View Roughness Map  
**3** View Bump Map  
**4** View Texture Mask  
**5** View Alpha  
**6** View UV mask  
**7** View Variation Mask  
**8** View Randomization Per Object  
**9** View Metal Map  
**0** View Displacement Map  
**Ctrl R** Replace current Active Map or ALL maps if you are on Combined Texture Map. This also works for replacing Masks that use an Image Texture  
**Ctrl I** Invert Texture on Active Map or ALL maps if you are on Combined Texture Map  
Additional hotkeys displayed in the UI to control specific settings of the material or the combined map are self explanatory. All the settings and controls you will ever need are available  

## Masks
Masks are one of the most important aspects of QuickTexture, with masks you can easily blend between all of the layers you have created  
Masks require a minimum 2 of layers to blend between unless explicitely stated  
Upon creation of Masks you preview that Mask and have a series of settings to manipulate, remember from the maps section above that you can always go to a different map, different layer, or return to the mask at any time by pressing the correct key  

**Ctrl M** Texture Mask  
**Ctrl C** Edge Mask (Cycles Only)  
**Ctrl A** Dirt Mask (Cycles Only)  
**Ctrl H** Height Mask will create a gradient from the bottom-top of your object  
**Ctrl N** Mask By Normal Direction  
**Alt H ** Depth Mask  
**Alt V** Variation Mask does not require a second layer as it will make a copy of your diffuse map and let you adjust the hue, saturation and value of the texture. The mask you select will be used as the blend map between the original and the edited map, to create variation  
**Shift V* Vertex Mask using your active Vertex Color Attribute  
**Ctrl O* Randomize Per Object does not require a second layer and will just add some hue saturation and value multipliers randomly for each object that your QuickTexture is applied to  
**Shift U** De-tiling does not require a second layer and breaks up repetitive patterns seen when tiling  
**Shift A** Smudge UV's does not require a second layer and will just offset your UV's by the texture map you choose, creating interesting effects  
**Backspace** Deletes Mask on the current layer  

## Managing Materials
QuickTexture comes with tools to easily manage materials instead of using Blender's regular ways of copying or deleting etc  
**Make Material Unique** will create a copy of the material that is not linked to any other objects  
**Copy Material** will copy materials over to objects including the procedural modifier setup  
**Unlink Material After Copy** will create a unique material for the object after you have copied it  
**Reset Material** Fully delete QuickTexture and any QuickTexture related attributes on the object  

## Baking
You can bake your textures and automatically have them imported into a new material for you, all with one click. keep in mind if you press ctrl t on this material, QuickTexture will launch and auto convert that material into a QuickTexture so you can continue this process over and over
**Preview Dirt and Edges** is a special feature that will take you into a preview mode to set up Dirt and Edgewear masks that you can then bake out and either use them in another application or as a Texture Mask  

## Decal
QuickDecals are extremely versatile and are Mesh Objects, so please remember that you can edit them at any time  
Border settings will enable a procedural blending that goes all around the decals outline so you can easily blend it into the surroundings  
QuickDecals are still QuickTextures, so you can edit these just as you would any QuickTexture by pressing Ctrl T and make layers and masks and so on  

## Paintover
QuickPaintover allows you to paint textures using your favorite image editor  
Set the full Image Editor .EXE file location in the preferences  
Make sure you collapse everything down to a single layer in your image editor before saving, and then use the Apply Paintover tool to update the texture  

## Tips 
Press the hotkey and then release to begin changing the setting, confirm by pressing the left mouse button  
Hold Ctrl/Alt/Shift to adjust values slower or faster while changing a setting
If you want to Photomodel you can launch QuickTexture or QuickDecal without an object selected, and based on the UV mode you will get a reference plane with different kinds of properties. Experiment with what works for your workflow    
Apply the QuickTexture modifier if you want to "Freeze" the texture  
Use Cycles when you are creating Edge/Dirt masks  
If you want to change the mask of the active layer to a different type, just delete it first and then make the new one

## Known Errors
Switching Workspaces is not supported so close the tool first and relaunch once you have switched  
Multiple Scenes and Multiple Viewlayers are not supported  
Full Screen Hotkey is not supported  
Non English Languages are NOT supported! Set language to EN_US  