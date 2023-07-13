import bpy, os


HDR_FORMATS = ('.hdr', '.exr')
SDR_FORMATS = ('.jpg', '.jpeg', '.png', '.tga', '.tif', '.tiff')
IES_FORMATS = ('.ies',)

addon_name = 'photographer'

photographer_folder = os.path.dirname(os.path.realpath(__file__))
addon_folder = os.path.dirname(photographer_folder)
scripts_folder = os.path.dirname(addon_folder)
presets_folder = os.path.join(scripts_folder,'presets')
photographer_presets_folder = os.path.join(presets_folder,'photographer')
# print("Scripts Folder: " + scripts_folder)
# print("Presets Folder: " + presets_folder)
# print("Addon Folder: " + addon_folder)
# print("Photographer Presets Folder: " + photographer_presets_folder)
# print("Photographer Folder: " + photographer_folder)

# Compact UI panel size
panel_value_size = 0.88

# Default Exposure value
base_ev = 9.416 #Applying the 683 lm/W conversion (2^9.416 = 683)

# Color Temperature description
color_temp_desc = "Color Temperature (Kelvin)./n Physically based between 1000K and 12,000K then accelerated towards blue for artistic purposes"
