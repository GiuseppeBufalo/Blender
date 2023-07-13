
# ooooooooo.                       oooo                              o8o
# `888   `Y88.                     `888                              `"'
#  888   .d88'  .oooo.    .ooooo.   888  oooo   .oooo.    .oooooooo oooo  ooo. .oo.    .oooooooo
#  888ooo88P'  `P  )88b  d88' `"Y8  888 .8P'   `P  )88b  888' `88b  `888  `888P"Y88b  888' `88b
#  888          .oP"888  888        888888.     .oP"888  888   888   888   888   888  888   888
#  888         d8(  888  888   .o8  888 `88b.  d8(  888  `88bod8P'   888   888   888  `88bod8P'
# o888o        `Y888""8o `Y8bod8P' o888o o888o `Y888""8o `8oooooo.  o888o o888o o888o `8oooooo.
#                                                        d"     YD                    d"     YD
#                                                        "Y88888P'                    "Y88888P'
 

import bpy
import zipfile

from . import directories
from . translate import translate


# oooooooooooo               .
# `888'     `8             .o8
#  888          .ooooo.  .o888oo  .oooo.o
#  888oooo8    d88' `"Y8   888   d88(  "8
#  888    "    888         888   `"Y88b.
#  888         888   .o8   888 . o.  )88b
# o888o        `Y8bod8P'   "888" 8""888P'


def unzip_in_location(zip_path, unpack_path,):
    """unzip given zip file"""

    with zipfile.ZipFile(zip_path, 'r') as z:
        z.extractall(unpack_path)

    return None


def blend_in_zip(zip_path):
    """check if there are .blends in this zip"""

    with zipfile.ZipFile(zip_path, 'r') as z:
        for info in z.infolist():
            if (".blend" in info.filename):
                return True

    return False

#                                         .                                  oooo
#                                       .o8                                  `888
#         .oooo.o  .ooooo.   .oooo.   .o888oo oo.ooooo.   .oooo.    .ooooo.   888  oooo
#        d88(  "8 d88' `"Y8 `P  )88b    888    888' `88b `P  )88b  d88' `"Y8  888 .8P'
#        `"Y88b.  888        .oP"888    888    888   888  .oP"888  888        888888.
#  .o.   o.  )88b 888   .o8 d8(  888    888 .  888   888 d8(  888  888   .o8  888 `88b.
#  Y8P   8""888P' `Y8bod8P' `Y888""8o   "888"  888bod8P' `Y888""8o `Y8bod8P' o888o o888o
#                                              888
#                                             o888o



class SCATTER5_OT_install_package(bpy.types.Operator):

    bl_idname      = "scatter5.install_package"
    bl_label       = "install_package"
    bl_description = translate("Install a given .scatpack archive file in your scatter library")
    bl_options     = {'INTERNAL'}

    filepath : bpy.props.StringProperty(subtype="FILE_PATH",)
    popup_menu : bpy.props.BoolProperty(default=True, options={"SKIP_SAVE","HIDDEN"},)

    def execute(self, context):
            
        #check if file is .scatpack
        
        if (not self.filepath.endswith(".scatpack")):
            
            print("S5 WARNING : Scatpack File Incorrect!")

            if (self.popup_menu):

                bpy.ops.scatter5.popup_dialog(
                    'INVOKE_DEFAULT',
                    msg=translate("Selected File is not a '.scatpack' format"),
                    header_title=translate("Error!"),
                    header_icon="ERROR",
                    )

            return {'FINISHED'}    
            
        #check if creator of .scatpack is dummy and can't create the zipfile structure properly , or perhaps scatpack relying on external library

        with zipfile.ZipFile( self.filepath , 'r') as z:
            
            IsBlend = False
            IsCorrect = False

            for p in z.namelist():

                if ( p.startswith("_presets_") or p.startswith("_biomes_") or p.startswith("_bitmaps_") ):
                    IsCorrect = True 

                if ( p.endswith(".blend") ):
                    IsBlend = True

                continue
            
            if (IsCorrect==False):

                print("S5 WARNING : Unpacking Scatpack Failed!")

                if (self.popup_menu):

                    bpy.ops.scatter5.popup_dialog(
                        'INVOKE_DEFAULT',
                        msg=translate("your '.scatpack' structure is wrong, it doesn't contains a '_presets_' nor '_biomes_' folder on first level"),
                        header_title=translate("Error!"),
                        header_icon="ERROR",
                        )
                return {'FINISHED'} 

        #install .scatpack

        unzip_in_location(self.filepath , directories.lib_library)

        #reload all libs

        bpy.ops.scatter5.reload_biome_library()
        bpy.ops.scatter5.reload_preset_gallery()

        #Great Success!

        if (self.popup_menu):

            if (IsBlend==False):

                print("S5 WARNING : Environmental Path Required?")

                if (self.popup_menu):
                    bpy.ops.scatter5.popup_dialog(
                        'INVOKE_DEFAULT',
                        msg=translate("We did not find any .blend file in this scatpack. You may need to define new environment paths leading to this library so the Geo-Scatter plugin will be able to find your objects! This option is located in our plugin preferences.\n\nWe advise installing your assets as a blender asset-library, the plugin will search there by default."),
                        header_title=translate("Installation Successful"),
                        header_icon="CHECKMARK",
                        )
            else:
                bpy.ops.scatter5.popup_dialog(
                    'INVOKE_DEFAULT',
                    msg=translate("Everything was installed correctly\n"),
                    header_title=translate("Installation Successful"),
                    header_icon="CHECKMARK",
                    )

        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
 


classes = (

    SCATTER5_OT_install_package,

    )
