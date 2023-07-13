#pylint: disable=import-error, relative-beyond-top-level
import bpy

#credits to BD3D for inventing this way of showing information popups
class SMR_OT_INFO(bpy.types.Operator):

    bl_idname = "smr.info"
    bl_label = "info"
    bl_description = "Info about these options"
    bl_options = {"REGISTER", "UNDO"}

    info : bpy.props.StringProperty()

    def execute(self, context):
        info = self.info

        def draw(self, context):
            nonlocal info
            layout = self.layout
            eval(info+'(layout)')

        bpy.context.window_manager.popup_menu(draw, title = 'Info', icon = 'QUESTION')

        return {'FINISHED'}


txt_cancel = '''
You are in a separate 'SMR_Bake' scene to improve baking performance.
To cancel and get back to your old scene, click out of this window
(so not on the OK button) and in the top right corner of your window,
where it says 'SMR_Bake' press on the x button.

'''

def bake_cancel(layout):

    for i, line in enumerate(txt_cancel.splitlines()):
        layout.label(text=line)


txt_parallax = '''
DecalMachine decals look 3D because of their parallax effect, this gets
calculated for each decal when you turn the view. If you apply a full
Smudgr Pro setup to a set of decals, turning the view when really zoomed
in on a decal may be introduce lag because of more complex calculations.
If there is too much lag, you can bake the Smudgr Pro setup to a set of
textures to improve calculation time. Make sure to re-apply to the
decals after baking.
'''

def parallax(layout):

    for i, line in enumerate(txt_parallax.splitlines()):
        layout.label(text=line)


txt_fullbake = '''
This baking operator will bake all Smudgr effects on this material to
texture maps. A copy of your old material will be kept for you. Baking
the effects has major speed benefits, but you will lose detail (depending
on your resolution) and the ability to change the settings.
'''

def fullbake(layout):

    for i, line in enumerate(txt_fullbake.splitlines()):
        layout.label(text=line)


txt_decalmachine = '''
If you own the DecalMachine addon, this operator can be used to copy
your Smudgr material to your decals, achieving the same effects on them
as with your Smudgr material. You need to re-apply with this button if
you make changes on your Smudgr material and want those changes to appear
on the decals as well. This works with both Box Mapped and UV mapped setups,
also works with baked setups.

How does it work?
1) Select all decals you want to apply the Smudgr material to
2) Shift select your Smudgr object, making sure it is the active object
3) If you have multiple slots, select the material slot you want copied
4) Press the button below
5) Choose what parts of the Smudgr texture you want to be copied
6) Press OK 
'''

def decalmachine(layout):

    for i, line in enumerate(txt_decalmachine.splitlines()):
        layout.label(text=line)


txt_smudge = '''
Smudges are surface imperfections for your material. They change
the roughness of your material on the spots of the smudge textures.
You can choose what type of smudge you want in the menu below. Click
on the image preview to see all images, choose a category on
the right of it or cycle trough the options with the next and
previous buttons.

Below you can see what smudge is currently on your object, the
image preview does NOT show the active smudge if you clicked on
another object and then back to this one. The active smudge line
does always tell you what smudge is currently on your object.

The falloff and roughness sliders are your main ways of controlling
how strong the smudge effect is. The roughness slider evenly changes
how strong the effect is, while the falloff slider changes the 
levels/colorramp of the smudge image. The paint button allows you to
add an influence map to the roughness slider.

Advanced settings give you control over scale, location, mapping etc.

'''

def info_smudge(layout):

    for i, line in enumerate(txt_smudge.splitlines()):
        layout.label(text=line)




txt_scratch = '''
Scratches are height maps that change the normal map of your material.
You can choose what type of scratch you want in the menu below. Click
on the image preview to see all images or cycle trough the options with the next and
previous buttons.

Finetune the depth of the scratches using the intensity slider.

Advanced settings give you control over scale, location, mapping etc.

'''

def info_scratch(layout):

    for i, line in enumerate(txt_scratch.splitlines()):
        layout.label(text=line)





txt_lines = '''
Why am I seeing lines and/or stretching in the effects?

This is one of the major downsides of using Box Mapping. If you want to remove
the lines and/or stretching; 
-Make sure your object has UV-Coordinates/is UV unwrapped
-Go to the Smudgr menu of the effect that is stretching
-Go to advanced settings
-Switch the Texture mapping from Box to UV

'''

def info_lines(layout):

    for i, line in enumerate(txt_lines.splitlines()):
        layout.label(text=line)





txt_bug = '''
How to report a bug?

I'm sorry to hear you found a bug in the addon, please send the things mentioned below
to me via BlenderMarket to help me fix this for you:

-When did the bug occur? What button did you press?
-Was there an error message? If so:
-A screenshot of the error log, found under Window>Toggle System Console
-What operating system are you using?
-If there was no error log: what version of SMUDGR are you using? (The name of the .py file)
-If you try the same thing you were doing before again, does the bug occur again?

'''

def info_bug(layout):

    for i, line in enumerate(txt_bug.splitlines()):
        layout.label(text=line)





txt_files = '''
How to add my own textures/files?

In summary:

For smudges and scratches = Save a thumbnail, a 1K, 2K and 4K version of the texture in one 
of the category folders. Make sure all the file names are the exact same, except the 
_0K (thumbnail), _1K, _2K and _4K suffix at the end of the filename (The K should be a 
captital). Supported formats are jpeg, jpg and png. 

For dust influence maps: Save a jpeg, jpg or png image in the dust folder inside SMR_Files.
Make sure to include the _1K suffix. I recommend using 1K files for this that are a bit blurred,
this gives the best effect.

For droplets: Save a jpeg, jpg of png version of the image in the droplets folder inside
SMR_Files. No suffix required. The file should be a black and white height map file.

IMPORTANT: User the Reload Images button in the preferences to update the image list.
'''

def info_files(layout):

    for i, line in enumerate(txt_files.splitlines()):
        layout.label(text=line)





txt_dust = '''
Dust adds a dust texture on the sides of your object facing upwards. This effect also includes
a brighter color when looking at low angles, to get a realistic dust effect. Smudgr uses influence
maps to create a realistic dust distribution, you can choose what influence map you want below.

Change the multiplier value to make the effect stronger or weaker, or use an influence map with
the paint button next to this slider. If you also want dust on the sides of your object, use 
the Side Dust slider.

The influence map slider increases or decreases the strenght of the influence map. Making this
0 will give a uniform dust pattern all across your object. Making it 1 is usually not the most
realistic, I recommend 0.6 to 0.8.

Change the dust color with the color picker.

In the advanced settings you can change scale, location, mapping etc.. The scale for
the influence map is seperate from the scale for the underlaying dust texture.
'''

def info_dust(layout):

    for i, line in enumerate(txt_dust.splitlines()):
        layout.label(text=line)





txt_bcm = '''
Base color mixing (BCM) adds color to your smudges/scratches. The
falloff slider determines the levels/colorramp of the effect, making 
it sharper or smoother. The color below is the color that the BCM
will be. Adding an influence map to the BCM intensity is a great
way of adding color only in selected places to get a realistic effect.
'''

def info_bcm(layout):

    for i, line in enumerate(txt_bcm.splitlines()):
        layout.label(text=line)





txt_inf = '''
Influence maps give you finer control over the effects of Smudgr.
By previewing the influence maps you see what controls the effects.
Light areas have strong effects and dark areas have little effects.

The sliders do the following:
Boost Blacks = Makes dark tones even darker
Boost White = Makes light tones even lighter
Multiplier = The influence map stays the same, but the effect gets
evenly stronger/weaker by moving this slider.
Influence = An example of this would be an influence map where some 
parts are pure white and others pure black. By setting the influence
to .5 the pure black areas will now only be 50 percent gray. This is
useful if you want the effect everywhere, but just a bit stronger in
the white areas.

You can choose one of the following influence maps:

Noise = Uses a noise texture to distribute your effects on your object.
Using the contrast or Hotspots presets works really well with this influence
map. The distortion slider also can add a realistic effect.

Cavity = Calculates where crevices and cavities are, making this white

Texture paint = Paint where you want the effect. Be careful about the sliders,
since they change the way your painting looks. If you want to see the effect
right away, not just paint on a black background, press Stop Previewing. If
you are stuck in paint mode and can't select your objects, this means you are 
in paint mode, you should go back to object mode in the top left corner of your
3D view. Texture paints will have to be packed in order to save them.

Geometry = Currently geometry will put the effect only on the parts of your
object that are facing upwards.

Gradient = Adds a black to white gradient. Using the move and rotate sliders,
you can place the gradient where you want it. Using the regular sliders you
can make the effect sharper or smoother. If the influence map is pure black, 
first try to reset your regular sliders, then move the Move slider untill you 
see the effect.

'''

def info_inf(layout):

    for i, line in enumerate(txt_inf.splitlines()):
        layout.label(text=line)





txt_wear = '''
SMUDGR includes two types of wear; cavity and edge wear. Both
change the color of your material based on calculated data.
Cavity changes the color in the crevices and cavities of your
object. Edge changes the color on, well, the edges...

You have to choose between Bake Mode and Live Mode:

Bake Mode = After you specified your resolution and samples,
Blender will render/bake a texture with the calculated cavity
data. This is great for Eevee and viewport, but can take some time
to bake. You also have to REBAKE every time you make changes to 
your object. After baking Smudgr will ask you to pack the baked image.
Note: Bake mode makes your material single user (only one object)

Live Mode = The calculations will be done when you render your final
image. This has some big advantages; no waiting for baked images, no
need to make the material single user (multiple objects can keep using
the same material) and the calculations will always be high detail.
The main disadvantages are that it cannot be used in Eevee and that
the effect is not visible in material mode, you have to check your
changes in the rendered viewport.

'''

def info_wear(layout):

    for i, line in enumerate(txt_wear.splitlines()):
        layout.label(text=line)





txt_mapping = '''
Box mapping projects the image from the 6 sides of an invisible box around 
your object. This means you don't need a UV map and the scale of the
effects are the same everywhere. This also makes the edges of the textures
almost invisble. The main downside is that there might be some stretching,
sometimes resulting in straight lines across your object.

The alternative is UV mapping, this uses your UV coordinates to place the 
textures. This is recommended if you have good UV-mapping on your object, 
or if the stretching effects are too noticable.

'''

def info_mapping(layout):

    for i, line in enumerate(txt_mapping.splitlines()):
        layout.label(text=line)





txt_at = '''
Anti tiling is great if you need large surfaces with the Smudgr textures.
Usually this results in a noticable repeating/tiling effect which looks
very unrealistic. Anti tiling creates a 2nd copy of the texture and scales,
rotates and moves this copy a bit. Then, a noise texture determines where
the original is visible, and where the copy.

You can preview the noise texture with the preview button.

The AT scale slider scales the copy of the texture. So if your orignal scale
is 10, an AT scale of 1.2 will make the copy have a scale of 12. I recommend
an AT_scale between 0 and 0.3.

The AT rotation slider is a factor of how much the copy is rotated, this is
a multiplier not a value in degrees. If your texture has a very noticable
direction, it might be better to keep this value at 0.

The AT noise scale influences the scale of the noise map that determines
where the copy is visible. It's best to go into preview mode to see this
scale changing.

'''

def info_at(layout):

    for i, line in enumerate(txt_at.splitlines()):
        layout.label(text=line)





txt_cavity_choice = '''
Cavity will be added in Live mode, this means it's only 
visible in Cycles Rendered mode. You can manually bake
the cavity map in the cavity settings if you want the 
effect to be visible at all times.

'''

def info_cavity_choice(layout):

    for i, line in enumerate(txt_cavity_choice.splitlines()):
        layout.label(text=line)





txt_droplets = '''
Droplets are height maps of water droplets on a surface. These are
mainly included in this addon to be used on glass surfaces. This is
because they use a height map that influences the normal map.

'''

def info_droplets(layout):

    for i, line in enumerate(txt_droplets.splitlines()):
        layout.label(text=line)





txt_nocavity = '''
I've added wear to an object, but it's not visible?

First, this could mean you are in Live mode and are looking at your
object in material mode. Live mode is only visible in the rendered
viewport in Cycles and in Cycles final renders. Switch to baked if you
want to use it in Eevee or want to see it in the viewport. See the 
info box in the Wear menu for more information about this.

If this is not the issue, increase the multiplier and/or use the
"preview influence map" button to check your effect.

'''

def info_nocavity(layout):

    for i, line in enumerate(txt_nocavity.splitlines()):
        layout.label(text=line)




txt_review = '''
Where can I post a review about the addon?

If you really like the addon, it would be awesome if you left a review
over on the BlenderMarket :-)

If you are having problems with the addon, or are not satisfied you can
of course also leave a review over there. I however would greatly appreciate it
if you told me about your problems first, I will do everything to help you!

Regards,
Oliver

'''

def info_review(layout):

    for i, line in enumerate(txt_review.splitlines()):
        layout.label(text=line)




txt_tut = '''
Are there tutorials?

Yes, tutorials will be released shortly after the release of the addon.
You can find them on my YouTube channel, it's called Oliver J Post

'''

def info_tut(layout):

    for i, line in enumerate(txt_tut.splitlines()):
        layout.label(text=line)        
