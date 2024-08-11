# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "Rotate around active and cursor",
    "author": "1COD",
    "version": (1, 2, 0),
    "blender": (2, 83, 0),
    "location": "View3D",
    "description": "activ object as new space referential. ctrl+. numpad", 
    "warning": "",
    "wiki_url": "",
    "category": "3D View"
}

import bpy
from mathutils import Matrix, Euler, Vector
from bpy.types import Operator, Panel
from bpy.props import FloatProperty, BoolProperty
from bpy_extras import view3d_utils

def remove_prop (self,context):  
    
    del bpy.types.Scene.rot_x       
    del bpy.types.Scene.rot_y       
    del bpy.types.Scene.rot_z       
    del bpy.types.Scene.loc_x       
    del bpy.types.Scene.loc_y
    del bpy.types.Scene.loc_z
    del bpy.types.Scene.cur_rot_x
    del bpy.types.Scene.cur_rot_y
    del bpy.types.Scene.cur_rot_z
    del bpy.types.Scene.cur_loc_x
    del bpy.types.Scene.cur_loc_y
    del bpy.types.Scene.cur_loc_z
    

Scn = bpy.types.Scene
Scn.whole_scene=BoolProperty(default=False)
Scn.around_cursor=BoolProperty(default=False)
ON=False
r=0

def loc_rot_props(self,context):
    
    Scn = bpy.types.Scene  
    context = bpy.context    
    scn = context.scene 
    cao=context.active_object

    Scn.rot_x=FloatProperty() #for active object
    Scn.rot_y=FloatProperty() 
    Scn.rot_z=FloatProperty() 
    Scn.loc_x=FloatProperty()   
    Scn.loc_y=FloatProperty()   
    Scn.loc_z=FloatProperty() 
    
    scn.rot_x = cao.rotation_euler.x
    scn.rot_y = cao.rotation_euler.y
    scn.rot_z = cao.rotation_euler.z   
    scn.loc_x = cao.location.x
    scn.loc_y = cao.location.y 
    scn.loc_z = cao.location.z   
    
    Scn.cur_rot_x=FloatProperty()  #for cursor
    Scn.cur_rot_y=FloatProperty()  
    Scn.cur_rot_z=FloatProperty()  
    Scn.cur_loc_x=FloatProperty()  
    Scn.cur_loc_y=FloatProperty()  
    Scn.cur_loc_z=FloatProperty()                

    scn.cur_rot_x = scn.cursor.rotation_euler.x
    scn.cur_rot_y = scn.cursor.rotation_euler.y
    scn.cur_rot_z = scn.cursor.rotation_euler.z   
    scn.cur_loc_x = scn.cursor.location.x
    scn.cur_loc_y = scn.cursor.location.y 
    scn.cur_loc_z = scn.cursor.location.z 

    
def call_props(self,context):
    
    context = bpy.context    
    scn = context.scene 
    cao=context.active_object
    
    rot_cur = context.scene.cursor.rotation_euler.copy()
    loc_cur = context.scene.cursor.location.copy()         
    rot = cao.rotation_euler.copy()
    loc = cao.location.copy()   

    self.rot = Euler((rot.x, rot.y, rot.z), 'XYZ')  
    self.loc = loc      

    rot_to_curs = Euler((
                        -rot_cur.x + rot.x,
                        -rot_cur.y + rot.y,
                        -rot_cur.z + rot.z
                        ), 'XYZ')
    
    if scn.around_cursor:                 
        self.rot = rot_to_curs
        self.loc_cur = loc_cur
        
def call_props_back(self,context):

    context = bpy.context    
    scn = context.scene 
            
    self.rot = Euler((
            scn.rot_x,
            scn.rot_y,
            scn.rot_z), 
            'XYZ')     
               
    self.loc = Vector((scn.loc_x, scn.loc_y, scn.loc_z))
    
    rot_curs = Euler((
                    -scn.cur_rot_x + scn.rot_x,
                    -scn.cur_rot_y + scn.rot_y,
                    -scn.cur_rot_z + scn.rot_z
                        ))

    loc_curs = Vector((
                        scn.cur_loc_x,
                        scn.cur_loc_y,
                        scn.cur_loc_z
                        ))

    if scn.around_cursor:                 
        self.rot = rot_curs
        self.loc_curs= loc_curs
        
def face_to_cursor(self,context):    
  
    ob=context.object
    scn = context.scene
    vert=ob.data.vertices

    if scn.geo: 
           
        global r  
        r=ob.matrix_world  @ (
        sum((i.co for i in  vert if i.select),Vector())/
        sum(int(i.select) for i in  vert)) 

        if scn.whole_scene:
            override = bpy.context.copy()
            override['selected_objects'] = list(bpy.context.scene.objects)
            bpy.ops.transform.translate(override, value=(
            scn.cursor.location.x-r.x, 
            scn.cursor.location.y-r.y, 
            scn.cursor.location.z-r.z))
            
        else:    
            bpy.ops.transform.translate(value=(
            scn.cursor.location.x-r.x, 
            scn.cursor.location.y-r.y, 
            scn.cursor.location.z-r.z)) 
    
    else:

        if scn.whole_scene:
            override = bpy.context.copy()
            override['selected_objects'] = list(bpy.context.scene.objects)
            bpy.ops.transform.translate(override, value=(
            -scn.cursor.location.x+r.x, 
            -scn.cursor.location.y+r.y, 
            -scn.cursor.location.z+r.z))
            
        else:    
            bpy.ops.transform.translate(value=(
            -scn.cursor.location.x+r.x, 
            -scn.cursor.location.y+r.y, 
            -scn.cursor.location.z+r.z)) 
               
Scn.geo=BoolProperty(default=False, update= face_to_cursor)        

class OBJ_OT_rot_loc (Operator):    
    bl_idname = "obj.rot_loc"
    bl_label = "matrice loc rot from active"
    bl_options = {"REGISTER", "UNDO"}
    
    @classmethod
    def poll (cls, context):
        return context.object and not ON and not context.object.parent   
    
    def execute(self, context): 
        
        global ON
        ON=True  
        
        context = bpy.context    
        scn = context.scene        
        loc_rot_props(self,context)
        call_props(self,context)
        
        rot=self.rot
        loc=self.loc
        
        to_qt = rot.to_quaternion()
        to_qt.invert()
        R = to_qt.to_matrix().to_4x4()
        T = Matrix.Translation(loc)
        M = T @ R @ T.inverted()
            
        if scn.whole_scene:
            obj = scn.objects
        else:
            obj = context.selected_objects
        
        for ob in obj:
            if ob.parent:
                continue
            ob.location = M @ ob.location -loc
            ob.rotation_euler.rotate(M)           
            
            if scn.around_cursor:
                ob.location +=  self.loc_cur
                    
            
        return {'FINISHED'}


class OBJ_OT_rot_loc_cancel (Operator):    
    bl_idname = "obj.rot_loc_cancel"
    bl_label = "cancel rot loc"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll (cls, context):
        return context.object and ON
    def execute(self, context):
        
        global ON
        ON=False  
        context = bpy.context    
        scn = context.scene   
        scn.geo=False     
        call_props_back(self,context)
        
        loc= self.loc
        rot= self.rot
        
        to_qt = rot.to_quaternion()
        to_qt.invert()

        R = to_qt.to_matrix().to_4x4()
        T = Matrix.Translation(loc)
        M = T @ R @ T.inverted()
        M = M.inverted() #rotation inverted

        if scn.whole_scene:
            obj = scn.objects
        else:
            obj = context.selected_objects
        
        for ob in obj:  
            if ob.parent:
                continue            
            
            if scn.around_cursor: 
                ob.location = M @ (ob.location + loc- self.loc_curs)               
                                   
            else:
                ob.location = M @ (ob.location + loc)
                
            ob.rotation_euler.rotate(M)
            
        if scn.geo:
            ob=bpy.context.object
            vert=ob.data.vertices
            r=ob.matrix_world  @ (
            sum((i.co for i in  vert if i.select),Vector())/
            sum(int(i.select) for i in  vert)) 
            bpy.ops.transform.translate(value=(
                                -scn.cursor.location.x + r.x,
                                -scn.cursor.location.y - r.y,
                                -scn.cursor.location.z - r.z))   
 
#        remove_prop(self,context)

            
        return {'FINISHED'}
    
 
class OBJ_OT_rot_loc_confirm (Operator):    
    bl_idname = "obj.rot_loc_confirm"
    bl_label = "matrice loc rot from active"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll (cls, context):
        return context.object and ON
        
    def execute(self, context):  
        
        global ON
        ON=False     

        remove_prop(self,context)      
        
        return {'FINISHED'}
    

class OBJ_PT_loc_rot_menu(Panel):
    bl_label = "Global rotation"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "0data"  # not valid name to hide it
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        
        scn = context.scene
        layout = self.layout

        row = layout.row(align=True)
        row.alignment = 'LEFT'   
        row.prop(scn,'whole_scene',text='Scene')
        row = layout.row(align=True)
        row.alignment = 'LEFT'  
        row.prop(scn,'around_cursor',text='Cursor')  
        if ON and scn.around_cursor:      
            row.prop(scn,'geo',text='From selected Geo')
        row=layout.row()
        label='Cursor'if scn.around_cursor else 'W Center'
        row.operator("obj.rot_loc",text=label)    
        row.operator("obj.rot_loc_confirm", text='Confirm')
        row.operator("obj.rot_loc_cancel", text='Cancel')
        layout.separator_spacer
        layout.operator("view3d.face_center",text="snap Cursor 2 face center")

#-----------------------------snap to face center


def main(context, event):
    
    scene = context.scene
    region = context.region
    rv3d = context.region_data
    coord = event.mouse_region_x, event.mouse_region_y
    viewlayer = context.view_layer
    depsgraph = context.evaluated_depsgraph_get()

    # get the ray from the viewport and mouse
    view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
    ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)
    
    result, location, normal, index, object, matrix = scene.ray_cast(viewlayer, ray_origin, view_vector)  

    if object:
        wmtx = object.matrix_world    
        object_eval = object.evaluated_get(depsgraph)    
        
        if context.mode=='OBJECT':            
                        
            face=object_eval.data.polygons[index]  
            loc = wmtx @ face.center   
            
        else:  
            mesh_from_eval = bpy.data.meshes.new_from_object(object_eval)
            
            face=mesh_from_eval.polygons[index]
            loc = wmtx @ face.center 
        
        bpy.context.scene.cursor.location=loc    

    return {'FINISHED'}

class FACE_OT_center(bpy.types.Operator):
    bl_idname = "view3d.face_center"
    bl_label = "snap cursor 2 face center-sfc"     
    
    @classmethod
    def poll(cls, context):
        return context.mode in {'OBJECT','EDIT_MESH'}

    def modal(self, context, event):        
        
        bpy.ops.view3d.cursor3d('INVOKE_DEFAULT',use_depth=False, orientation='GEOM')
        main(context, event)
 
        if event.type == 'LEFTMOUSE':
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            bpy.context.scene.cursor.location=self.cursor_loc
            bpy.context.scene.cursor.rotation_euler=self.cursor_rot
            return {'FINISHED'}
        
        elif event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE','TAB'}:
            # allow navigation
            return {'PASS_THROUGH'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):    
    
        self.cursor_loc=bpy.context.scene.cursor.location.copy()
        self.cursor_rot=bpy.context.scene.cursor.rotation_euler.copy()
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}        






#------------------------------        

addon_keymaps = []

def register():
    bpy.utils.register_class(OBJ_OT_rot_loc)
    bpy.utils.register_class(OBJ_OT_rot_loc_cancel)
    bpy.utils.register_class(OBJ_PT_loc_rot_menu)
    bpy.utils.register_class(OBJ_OT_rot_loc_confirm)
    bpy.utils.register_class(FACE_OT_center)
    
    wm = bpy.context.window_manager

    if wm.keyconfigs.addon:

        km = wm.keyconfigs.addon.keymaps.new(name = '3D View Generic', space_type = 'VIEW_3D')
        kmi = km.keymap_items.new(idname='wm.call_panel', type='NUMPAD_PERIOD', value='PRESS',shift=True)
        kmi.properties.name = "OBJ_PT_loc_rot_menu"
        addon_keymaps.append((km, kmi))  

def unregister():
    bpy.utils.unregister_class(OBJ_OT_rot_loc)
    bpy.utils.unregister_class(OBJ_OT_rot_loc_cancel)
    bpy.utils.unregister_class(OBJ_PT_loc_rot_menu)
    bpy.utils.unregister_class(OBJ_OT_rot_loc_confirm)
    bpy.utils.unregister_class(FACE_OT_center)

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        for km, kmi in addon_keymaps:
            km.keymap_items.remove(kmi)
    addon_keymaps.clear()  

if __name__ == "__main__":
    register()
    

