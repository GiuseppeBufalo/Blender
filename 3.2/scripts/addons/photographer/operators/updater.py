import re
import requests
import bpy

from ..constants import addon_name

update_url = 'https://api.github.com/repos/michelchafouin/photographer_updater/releases'
version_regex = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+")
changelog = []
latest_msg = "You are running the latest version of the add-on."

class PHOTOGRAPHER_OT_CheckForUpdate(bpy.types.Operator):
    bl_idname = "photographer.check_for_update"
    bl_label = "Check for Updates"
    bl_description = "Verify if you are running the latest version of the add-on"

    def execute(self,context):
        prefs = bpy.context.preferences.addons[addon_name].preferences
        prefs.needs_update = ""

        try:
            response = requests.get(update_url)
            if response.status_code == 200:
                resp_json = response.json()
                versions = list()
                for rel in resp_json:
                    v_info = [rel['tag_name'],rel['body']]          
                    if version_regex.match(v_info[0]):
                        versions.append(v_info)
                versions = sorted(versions, reverse=True)

                # addon_version is set at registration in __init__
                current_version_str = '.'.join(map(str, list(addon_version)))
                latest_version_str = versions[0][0]
                if str(current_version_str) < str(latest_version_str):
                    needs_update = f"Photographer {latest_version_str} is available!"
                    changelog.clear()
                    for v in versions:
                        if v[0] > current_version_str:
                            changelog.append(v)
                    prefs.needs_update = needs_update
                else:
                    prefs.needs_update = latest_msg

        except:
            prefs.needs_update = 'Update Check: Connection Failed.'
            
        return{'FINISHED'}
