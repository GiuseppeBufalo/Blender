
#####################################################################################################
#
# ooooooooo.
# `888   `Y88.
#  888   .d88'  .ooooo.  ooo. .oo.    .oooo.   ooo. .oo.  .oo.    .ooooo.
#  888ooo88P'  d88' `88b `888P"Y88b  `P  )88b  `888P"Y88bP"Y88b  d88' `88b
#  888`88b.    888ooo888  888   888   .oP"888   888   888   888  888ooo888
#  888  `88b.  888    .o  888   888  d8(  888   888   888   888  888    .o
# o888o  o888o `Y8bod8P' o888o o888o `Y888""8o o888o o888o o888o `Y8bod8P'
#
#####################################################################################################


import bpy
from .. utils.extra_utils import dprint
from .. resources.translate import translate


def rename_particle(self,context):

    scat_scene = bpy.context.scene.scatter5
    emitter = self.id_data

    #deny update if no changes detected 
    if (self.name==self.name_bis):
        return None 
    
    #deny update if empty name 
    elif ( (self.name=="") or self.name.startswith(" ") ):
        self.name = self.name_bis
        bpy.ops.scatter5.popup_menu(msgs=translate("Name cannot be None, Please choose another name"),title=translate("Renaming Impossible"),icon="ERROR")
        return None
    
    #deny update if name already taken by another scatter_obj 
    elif (f"scatter_obj : {self.name}" in bpy.data.objects):
        if (self.name_bis!=""): #No update on creation
            self.name = self.name_bis
            bpy.ops.scatter5.popup_menu(msgs=translate("This name is taken, Please choose another name"),title=translate("Renaming Impossible"),icon="ERROR")
            return None

    dprint(f"PROP_FCT: updating name : {self.name_bis}->{self.name}")

    #change the geonode_coll names
    if ( (self.scatter_obj is not None) and (self.name_bis!="") ):

        #change geonode collection name
        geonode_coll = bpy.data.collections.get(f"psy : {self.name_bis}")
        if (geonode_coll is not None):
            geonode_coll.name = geonode_coll.name.replace(self.name_bis,self.name,)
       
        #change scatter obj name
        self.scatter_obj.name = self.scatter_obj.name.replace(self.name_bis,self.name,)

    #rename default instance_coll
    if (self.scatter_obj is not None):

        coll = self.s_instances_coll_ptr
        if ( (coll is not None) and coll.name.startswith("ins_col") ):
            coll.name = coll.name.replace(self.name_bis,self.name,)

    #change sync channels members names

    #loop channels
    for ch in scat_scene.sync_channels:

        #change channels name
        if (ch.name==self.name_bis):
            ch.name = self.name

        #change channel members
        if ( (len(ch.members)!=0) and ch.psy_in_channel(self.name_bis) ):

            for m in ch.members:
                if (m.psy_name==self.name_bis):
                    m.psy_name = self.name
                continue

        continue

    #change ecosystem relation names? 
    for ps in emitter.scatter5.particle_systems:
        for i in (1,2,3):
            
            #affinity
            name = getattr(ps,f"s_ecosystem_affinity_{i:02}_ptr")
            if ( (name!="") and (name==self.name_bis) ):
                setattr(ps,f"s_ecosystem_affinity_{i:02}_ptr", self.name)
            
            #repulsion
            name = getattr(ps,f"s_ecosystem_repulsion_{i:02}_ptr")
            if ( (name!="") and (name==self.name_bis) ):
                setattr(ps,f"s_ecosystem_repulsion_{i:02}_ptr", self.name)

    #change name_bis name
    self.name_bis = self.name 

    return None
