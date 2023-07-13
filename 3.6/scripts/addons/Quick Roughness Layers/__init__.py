bl_info = {
    "name": "Quick Roughness Layers",
    "author": "Amandeep",
    "description": "Add Roughness maps in one click",
    "blender": (2, 83, 0),
    "version": (1, 0, 0),
    "location": "N-Panel > Item > QRL",
    "warning": "",
    "category": "Object",
}
#region INFORMATION
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
import bpy
from bpy_extras.io_utils import ImportHelper
import os
import bpy.utils.previews
preview_collections = {}
preview_list = {}
def preferences():
    return bpy.context.preferences.addons[__package__].preferences
class QRPrefs(bpy.types.AddonPreferences):
    bl_idname = __package__
    roughness_maps_path:bpy.props.StringProperty(default="Choose Path",name="Roughness Maps Directory",subtype='DIR_PATH')
    use_anti_tile_node:bpy.props.BoolProperty(default=True,name="Use UnTile Node")
    def draw(self, context):
        layout=self.layout
        layout.prop(self,'roughness_maps_path')
        layout.prop(self,'use_anti_tile_node')
def enum_previews_from_directory_items_iad(self, context):
    enum_items = []
    name = self.name
    if name in preview_list.keys():
        list = preview_list[name]
        #print(name,list)
        if context is None:
            return enum_items
        pcoll = preview_collections[name]
        if len(pcoll.my_previews) > 0:
            return pcoll.my_previews
        
        for i, name in enumerate(list):
            if name.endswith(".png") or name.endswith(".jpg"):
                #print("loading:",name)
                thumb = pcoll.load(name, name, 'IMAGE')
                enum_items.append(
                    (name, os.path.basename(name.replace(".png", "").replace(".jpg","")), "", thumb.icon_id, i))
        pcoll.my_previews = enum_items
        return pcoll.my_previews
    return []
class QR_OT_Load_Previews(bpy.types.Operator):
    bl_idname = 'qr.refreshmaps'
    bl_label = 'Refresh'
    bl_description = "Refresh"
    bl_options = {'PRESET', 'UNDO'}
    def execute(self, context):
        bpy.context.scene.QRMaps.clear()
        for pcoll in preview_collections.values():
            bpy.utils.previews.remove(pcoll)
        preview_collections.clear()
        preview_list.clear()
        allfiles=[]
        alldirs=[]
        if os.path.isdir(preferences().roughness_maps_path):
            for path, dirs, files in os.walk(preferences().roughness_maps_path):
                    alldirs+= [os.path.join(path, dir) for dir in dirs]
            for a in alldirs+[os.path.dirname(preferences().roughness_maps_path),]:
                allfiles=[os.path.join(a,f) for f in os.listdir(a)]
                og_name=a
                i=1
                while os.path.basename(a) in bpy.context.scene.QRMaps.keys():
                    a=og_name+f"-{i}"
                    i=i+1
                temp = bpy.context.scene.QRMaps.add()
                temp.name = os.path.basename(a)
                preview_list[os.path.basename(a)] = allfiles
                pcoll = bpy.utils.previews.new()
                pcoll.my_previews = ()
                preview_collections[os.path.basename(a)] = pcoll
        return {'FINISHED'}
class QRMaps(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="name", default="Decals")
    preview: bpy.props.EnumProperty(
        items=enum_previews_from_directory_items_iad)
def QR_directories(self, context):
    if context.scene.QRMaps and [(a.name,a.name,a.name) for a in context.scene.QRMaps]:
        return [(a.name,a.name,a.name) for a in context.scene.QRMaps]
    else:
        return [("None","None","None")]
class QR_PT_Roughness_Maps_Panel(bpy.types.Panel):
    bl_label = "QRL"
    bl_idname = "OBJECT_PT_QR"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Item"
    
    def draw(self, context):
        layout= self.layout
        #layout.operator("rtools.importasdecal")
        layout.operator("qr.refreshmaps",icon="FILE_REFRESH")
        layout.prop(context.scene,'QR_directories')
        if context.scene.QR_directories in context.scene.QRMaps.keys():
            layout.template_icon_view(
                        context.scene.QRMaps[context.scene.QR_directories], "preview", show_labels=True, scale=8, scale_popup=6)
            layout.operator("qr.addroughnessmap")
        
        if context.active_object and context.active_object.type in {'MESH','CURVE','FONT','SURFACE'} and context.active_object.data.materials:
            mat=context.active_object.data.materials[0]
            if "QR UnTile" in [a.name for a in mat.node_tree.nodes]:
                layout.label(text="UnTile Settings")
                layout.prop(mat.node_tree.nodes["QR UnTile"].inputs[1],'default_value',text="Scale")
                layout.prop(mat.node_tree.nodes["QR UnTile"].inputs[2],'default_value',text="Amount")
            for mat in context.active_object.data.materials:
                for n in mat.node_tree.nodes:
                    if "QR Roughness Map" in n.name and n.type=='TEX_IMAGE':
                        box=layout.box()
                        row=box.row()
                        row=row.split(factor=0.88)
                        row.label(text=n.name)
                        op=row.operator("qr.removelayer",text="",icon="PANEL_CLOSE")
                        op.node=n.name
                        op.mat=mat.name
                        box.prop(n,"image")
                        if n.outputs[0].is_linked and "QR Node Group" in n.outputs[0].links[0].to_node.name:
                            node=n.outputs[0].links[0].to_node
                            box.prop(node.inputs[1],'default_value',text="Brightness")
                            box.prop(node.inputs[2],'default_value',text="Contrast")
                            box.prop(node,'usezmask',text="Use Z Mask",toggle=True)
                            if node.inputs[3].default_value>0:
                                box.prop(node.inputs[4],'default_value',text="Reach")
                                box.prop(node.inputs[5],'default_value',text="Invert")
class QR_OT_Remove_Layer(bpy.types.Operator):
    bl_idname = 'qr.removelayer'
    bl_label = 'Remove Roughness Map'
    bl_description = "Remove this Roughness Map"
    bl_options = {'PRESET', 'UNDO'}
    node:bpy.props.StringProperty(options={'SKIP_SAVE'})
    mat:bpy.props.StringProperty(options={'SKIP_SAVE'})
    @classmethod
    def poll(self, context):
        return context.active_object
    
    def execute(self, context):
        mat=bpy.data.materials[self.mat]
        node=mat.node_tree.nodes[self.node]
        node_tree=mat.node_tree
        last_socket=None
        out_sockets=[]
        if node.outputs[0].is_linked and "QR Node Group" in node.outputs[0].links[0].to_node.name:
            
            for link in node.outputs[0].links[0].to_node.outputs[0].links:
                if link.to_node.type=='MIX_RGB':
                    for out_link in link.to_node.outputs[0].links:
                        out_sockets.append(out_link.to_socket)
                    for socket in link.to_node.inputs:
                        if socket.is_linked and socket.links[0].from_socket!=link.from_socket:
                            last_socket=socket.links[0].from_socket
                    node_tree.nodes.remove(link.to_node)
            node_tree.nodes.remove(node.outputs[0].links[0].to_node)
        node_tree.nodes.remove(node)
        if last_socket:
            for o in out_sockets:
                node_tree.links.new(last_socket,o)
        if not [a for a in node_tree.nodes if "QR Roughness Map" in a.name]:
            if "QR UnTile" in [a.name for a in node_tree.nodes]:
                node_tree.nodes.remove(node_tree.nodes["QR UnTile"])
            if "QR Texture Coordinates" in [a.name for a in node_tree.nodes]:
                node_tree.nodes.remove(node_tree.nodes["QR Texture Coordinates"])

        return {'FINISHED'}
class QR_OT_Add_Roughness_Map(bpy.types.Operator):
    bl_idname = 'qr.addroughnessmap'
    bl_label = 'Add Roughness'
    bl_description = "Add Roughness Map"
    bl_options = {'PRESET', 'UNDO'}
    @classmethod
    def poll(self, context):
        return context.active_object
    
    def execute(self, context):
        path=context.scene.QRMaps[context.scene.QR_directories].preview
        active=context.active_object
        #print(path,active)
        if bpy.data.node_groups.get('QR_Node_Group') is None:
            path2=os.path.join(os.path.join(os.path.dirname(os.path.abspath(__file__)),"Assets"),"Assets.blend","NodeTree")
        
    
            bpy.ops.wm.append(
                    directory=path2,
                    filename='QR_Node_Group', autoselect=False
                )
        if preferences().use_anti_tile_node and bpy.data.node_groups.get('QR UnTile') is None:
            path2=os.path.join(os.path.join(os.path.dirname(os.path.abspath(__file__)),"Assets"),"Assets.blend","NodeTree")
        
    
            bpy.ops.wm.append(
                    directory=path2,
                    filename='QR UnTile', autoselect=False
                )
        #print(active.data.materials,os.path.isfile(path))
        if active.data.materials and os.path.isfile(path):
            mat=active.data.materials[active.active_material_index]
            for  n in mat.node_tree.nodes:
                if "roughness" in [socket.name.lower() for socket in n.inputs]:
                    if n.inputs["Roughness"].is_linked:
                        bpy.ops.qr.mixwithnode('INVOKE_DEFAULT',node_to_mix=path,node=n.inputs["Roughness"].links[0].from_node.name,socket=n.inputs["Roughness"].links[0].from_socket.name,mat=mat.name)
                        return {'FINISHED'}
                    else:
                        node_to_mix=path
                        node_tree=mat.node_tree
                        if os.path.isfile(node_to_mix):
                            
                            
                            img=bpy.data.images.load(node_to_mix)
                            img.colorspace_settings.name='Non-Color'
                            img_node=node_tree.nodes.new(type='ShaderNodeTexImage')
                            img_node.hide=True
                            img_node.name="QR Roughness Map"
                            img_node.image=img
                            img_node.location=n.location[0]-450,n.location[1]
                            QRGroup=node_tree.nodes.new('ShaderNodeGroup')
                            QRGroup.location=n.location[0]-200,n.location[1]
                            QRGroup.name="QR Node Group"
                            QRGroup.node_tree = bpy.data.node_groups.get('QR_Node_Group')
                            if preferences().use_anti_tile_node: 
                                if "QR UnTile" not in [a.name for a in node_tree.nodes]:
                                    AntiTile=node_tree.nodes.new('ShaderNodeGroup')
                                    AntiTile.location=n.location[0]-700,n.location[1]
                                    AntiTile.name="QR UnTile"
                                    AntiTile.node_tree = bpy.data.node_groups.get('QR UnTile')
                                else:
                                    AntiTile=node_tree.nodes["QR UnTile"]
                                if "QR Texture Coordinates" not in [a.name for a in node_tree.nodes]:
                                    TexCoord=node_tree.nodes.new('ShaderNodeTexCoord')
                                    TexCoord.location=n.location[0]-900,n.location[1]
                                    TexCoord.name="QR Texture Coordinates"
                                else:
                                    TexCoord=node_tree.nodes["QR Texture Coordinates"]
                                node_tree.links.new(TexCoord.outputs[2],AntiTile.inputs[0])
                                node_tree.links.new(AntiTile.outputs[0],img_node.inputs[0])
                                
                            #contrast_node=node_tree.nodes.new(type='ShaderNodeBrightContrast')
                            #contrast_node.location=n.location[0]-200,n.location[1]
                            node_tree.links.new(img_node.outputs[0],QRGroup.inputs[0])
                            node_tree.links.new(QRGroup.outputs[0],n.inputs["Roughness"])
                            return {'FINISHED'}     
        else:
            self.report({'WARNING'},"No Materials Found!")
        return {'FINISHED'}
class QR_OT_Mix_To_Node(bpy.types.Operator):
    bl_idname = "qr.mixwithnode"
    bl_label = "Mix With Node"
    bl_description = ""
    bl_options = {"REGISTER","UNDO"}
    node_to_mix:bpy.props.StringProperty(default="")
    node: bpy.props.StringProperty(default="",options={'SKIP_SAVE'})
    socket: bpy.props.StringProperty(default="",options={'SKIP_SAVE'})
    mat: bpy.props.StringProperty(default="")
    
    def execute(self, context):
        if self.node!="":
            n1=bpy.data.materials[self.mat].node_tree.nodes[self.node]
        socket=0
        if self.socket!="":
            socket=self.socket
        output_sockets=[]
        node_tree=bpy.data.materials[self.mat].node_tree
        node_to_mix=self.node_to_mix
        if node_to_mix!="":
            if os.path.isfile(node_to_mix):
                for out in n1.outputs:
                    if out.is_linked:
                        output_sockets=[a.to_socket for a in out.links]
                img=bpy.data.images.load(node_to_mix)
                img.colorspace_settings.name='Non-Color'
                img_node=node_tree.nodes.new(type='ShaderNodeTexImage')
                img_node.hide=True
                img_node.name="QR Roughness Map"
                img_node.image=img
                img_node.location=n1.location[0]-250,n1.location[1]+n1.height+200
                QRGroup=node_tree.nodes.new('ShaderNodeGroup')
                QRGroup.location=n1.location[0],n1.location[1]+n1.height+200
                QRGroup.name="QR Node Group"
                QRGroup.node_tree = bpy.data.node_groups.get('QR_Node_Group')
                #contrast_node=node_tree.nodes.new(type='ShaderNodeBrightContrast')
                #contrast_node.location=n1.location[0],n1.location[1]+n1.height+200
                node_tree.links.new(img_node.outputs[0],QRGroup.inputs[0])
                mix_node=node_tree.nodes.new(type='ShaderNodeMixRGB')
                mix_node.blend_type='SCREEN'
                mix_node.inputs[0].default_value =1
                mix_node.hide=True
                mix_node.use_clamp=True
                node_tree.links.new(QRGroup.outputs[0],mix_node.inputs[1])
                node_tree.links.new(n1.outputs[socket],mix_node.inputs[2])
                mix_node.location=n1.location[0]+n1.width+50,n1.location[1]+100
                if preferences().use_anti_tile_node: 
                                if "QR UnTile" not in [a.name for a in node_tree.nodes]:
                                    AntiTile=node_tree.nodes.new('ShaderNodeGroup')
                                    AntiTile.location=n1.location[0]-700,n1.location[1]
                                    AntiTile.name="QR UnTile"
                                    AntiTile.node_tree = bpy.data.node_groups.get('QR UnTile')
                                else:
                                    AntiTile=node_tree.nodes["QR UnTile"]
                                if "QR Texture Coordinates" not in [a.name for a in node_tree.nodes]:
                                    TexCoord=node_tree.nodes.new('ShaderNodeTexCoord')
                                    TexCoord.location=n1.location[0]-900,n1.location[1]
                                    TexCoord.name="QR Texture Coordinates"
                                else:
                                    TexCoord=node_tree.nodes["QR Texture Coordinates"]
                                node_tree.links.new(TexCoord.outputs[2],AntiTile.inputs[0])
                                node_tree.links.new(AntiTile.outputs[0],img_node.inputs[0])
                for o in output_sockets:
                        node_tree.links.new(mix_node.outputs[0],o)
        return {'FINISHED'}
def update_z_mask(self, context):
    if "QR Node Group" in self.name:
        if self.usezmask:
            self.inputs[3].default_value=1
        else:
            self.inputs[3].default_value=0
classes = (QR_OT_Add_Roughness_Map,QR_OT_Load_Previews,QRMaps,QRPrefs,QR_PT_Roughness_Maps_Panel,QR_OT_Mix_To_Node,QR_OT_Remove_Layer
)

icon_collection={}
addon_keymaps = []

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    kmaps = [
    ]

    km = kc.keymaps.new(name="3D View", space_type="VIEW_3D")
    if kc:
        for (op, k, sp) in kmaps:

            kmi = km.keymap_items.new(
                op,
                type=k,
                value="PRESS",
                alt="alt" in sp,
                shift="shift" in sp,
                ctrl="ctrl" in sp,
            )
            addon_keymaps.append((km, kmi))
    bpy.types.Scene.QR_directories= bpy.props.EnumProperty(items=QR_directories,name="Folder")
    bpy.types.Scene.QRMaps = bpy.props.CollectionProperty(type=QRMaps)
    bpy.types.Node.usezmask= bpy.props.BoolProperty(default=False,update=update_z_mask)

def unregister():

    from bpy.utils import unregister_class

    for cls in reversed(classes):
        unregister_class(cls)
    for (km, kmi) in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()
    preview_list.clear()
if __name__ == "__main__":
    register()

