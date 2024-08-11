# ///////////////////////////////////////////////////////////////
#
# Blender Dome Light
# by: WANDERSON M. PIMENTA
# version: 3.0.0
#
# ///////////////////////////////////////////////////////////////

import os 

# Previews Collections
preview_collections = {}

# Version
version = '3.0.0 Alpha'

# File path for saving favorites
# Getting the current directory of the script
current_directory = os.path.dirname(__file__)
# Getting the directory one level up
parent_directory = os.path.abspath(os.path.join(current_directory, ".."))
# Matching the directory with the file name
favorites_file = os.path.join(parent_directory, "settings", "favorites.json")

# Loading status
actual_file_status = ""

# Addon Keymaps
addon_keymaps = []

# Load Icons
# Call the function to load the icons
icons_info = [
    ("logo_icon", os.path.join(os.path.dirname(__file__), "..", "icons", "logo.svg"), 'IMAGE'),
    # Add more tuples here to load other icons
]