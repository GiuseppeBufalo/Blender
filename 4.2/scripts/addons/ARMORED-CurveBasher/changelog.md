# CURVEBASHER CHANGELOG

## v1.3 (LATEST)
*(12/Apr/21)*
- NEW Tool: Curvecast (*C*).
- NEW Tool: Mesh to Curvebash (*RMB* Context Menu).
- Wire Generator Random algorithm: Parallel.
- Wire Generator Pattern: Array.
- Wire Generator Property: Gravity.
- Wire Generator Property: Handle Alignment.
- Wire Generator Behaviour: Handles are now hooked to the volumes (only noticeable with *Aligned* handles).
- Wire Generator Behaviour: Massive performance boost with high curve counts.
- Curvebasher Property: Transform Slide.
- Curvebasher Property: *Array* types support caps.
- Curvebasher Property: can toggle the array type between *Fit Curve*. and *Fixed Count*
- Curvebasher Property: *Shift + Scroll* or *Ctrl + Shift + Scroll* increases *Profiles Types* edge count in different ways.
- Curvebasher Property: *Shift + Scroll* switches *Array* types to *Fixed Count* mode and changes the array count.
- Curvebasher Behaviour: links assets to the scene instead of appending.
- Curvebasher Behaviour: leaves no orphan data when browsing through presets.
- Curvebasher Behaviour: HUD remembers user settings between Blender sessions.
- Curvebasher Behaviour: when possible, discard invalid selections instead of raising exceptions.
- Curvebasher Behaviour: all transforms are persistent between type switching.
- Curvebasher Behaviour: all transforms are persistent between type switching.
- Curvebasher Behaviour: Deletes IDs when the reference geometry is missing.

- BUGFIX: where random curvebash scales would reset if the operator was cancelled (RMB) without any changes.
- BUGFIX: when using Array Mode that would crash the addon if you cancelled the operator before applying a scale trasformation.
- BUGFIX: Previous feature enable smart filtering for 'Profile' curves was accidently disabled but is now working again.

### Revision 1:
*(13/Apr/21)*
- Curvebasher Preferences: added *Adapt to HiDPI* - Scale the HUD based on your system scale.
- Curvebasher Preferences: added *HUD Scale* - Make the HUD bigger or smaller'.
- Curvebasher BUGFIX: added a cleanup function to remove the linked preset library to prevent *Missing Lib messages* (harmless errors).
- Wire Generator BUFGIX: When using objects with no dimensions such as Empties, 
  enabling *Gravity* placed the gravity volume in the wrong location or crashed the operator.

### Revision 2:
*(15/Apr/21)*
- Curvebasher BUGFIX: applying scale on a curve transfers that scale to its control points. Added 2 developer functions that counteract
  it in different ways. Best method is enabled by default *mk_inverse_scale_points*.

### Revision 3:
*(02/May/21)*
- Curvebasher Behaviour: Can now browse through presets and categories with the *Arrow Keys*
    (for users without mice or scroll wheels).
- Cursorcast BUGFIX: endpoint handles on new curves would not align properly if rotation_mode was changed by other addons.

### Revision 4:
*(29/Aug/21)*
- Curvebasher Behaviour: Can now browse switch preset categories with the number row even if you have *Emulate Numpad* enabled.
- Curvebasher BUGFIX: Custom materials would suddenly dissapear when applying any given kitbash preset to a curve (materials with texture inputs are still unsupported).

### Revision 5:
*(13/Sep/21)*
- Curvebasher BUGFIX: errors when scrolling through presets; basically bugfixed the bugfix (forgot to account for empty material slots listed by *obj.data.materials*)
- Curvebasher Behaviour: Incremental values such as *Array Count* can now be done with the *Arrow Keys* (for users without scroll wheels).

### Revision 6:
*(15/Mar/22)*
- Wire Generator BUGFIX: someone reported a crash in 3.1 caused by the randomized seed being a float instead of a int, I think I fixed it.
- Curvebasher Preferences: added *Show N Panel* - Shows or Hides the Curve Basher tab from Blender's N panel.

### Revision 7:
*(12/Nov/22)*
- Curvebasher BUGFIX: Moving the *CB Kitbash* or *CB Caps* collections would cause an error when the addon would look for those collections in the wrong place.

### Revision 8:
*(30/Jan/23)*
- Curvebasher BUGFIX: Presets would lose their textures after ending the modal operator with LEFTMOUSE. The data block was not local and the `utils.collections.cleanup()` was unlinking the required library. Temporarily disabled the `unlink_libraries` function (should be harmless) until a better solution is found.

### Revision 9:
*(17/Nov/23)*
- Curvebasher BUGFIX: the Kitbasher HUD was not being drawn because of a deprecated DPI parameter in the `<blf.size()>` command.


## v1.2
*(05/Nov/20)*
- Added the Wire Generator Tool (Shift+A>Curve>Wire Generator).
- Can now Randomize scale by holding ALT or ALT+SHIFT when scaling.
- 'Uniform Scale' on 'Array' types no longer requires ALT press and is now called 'Scale'.
- 'Array' types now support Scale Reset and new curves utilize the last scale applied in 'Array' mode.
- Mouse wraps around the screen when the border is reached.
- Added expandable HUD (F1, or H during the modal).
- Curve Profiles for 'Basic' types now appear selected. Based on context, the addon can ignore their 
 selection to prevent recursion (curve profiles being applied to curve profiles).

- 'Curve Kitbash' Collection is now deleted automatically when empty.
- Performance increase when creating 'Array' types.
- Improvements when resetting or canceling transforms.
- Fixed a scaling issue on the chain preset.
- Fixed a bug that increased the Uniform Scale speed depending on how many 'Array' types were selected.
- Fixed a bug that created internal selection duplicates. Using a Set instead of List to store the internal slection fixed the issue.
- Edge to curve conversion was broken in the previous release. The issue has been fixed.
- The active curve, along with its transforms and kitbash, will be used for the next virgin curve/s.

Revision 1:
-Removed stray print statements.
-Fixed crash from pressing TAB during the modal. TAB now selects the curve points correctly.


## v1.1
*(23/Sep/20)*
- Added the Draw Curve Tool (Shift+A>Curve>Draw Curve).
- Added a button in the N Panel that opens the 'Default Presets' Blend file.
- Fixed a bug that was creating extra mesh data for Array Types.