
# ###############################################################################################################
# #  
# #   oooooooooo.            oooo
# #   `888'   `Y8b           `888
# #    888     888  .oooo.    888  oooo   .ooooo.
# #    888oooo888' `P  )88b   888 .8P'   d88' `88b
# #    888    `88b  .oP"888   888888.    888ooo888
# #    888    .88P d8(  888   888 `88b.  888    .o
# #   o888bood8P'  `Y888""8o o888o o888o `Y8bod8P'
# #  
# ###############################################################################################################


# import bpy, bmesh, time, datetime, uuid, os 

# import numpy as np
# from numpy.ctypeslib import ndpointer

# import ctypes 
# from ctypes import c_int, c_double, c_size_t



# from .. cpp import get_compiled_fct

# from .. resources.icons import cust_icon
# from .. resources.translate import translate

# from .. ui import ui_templates



# #   .oooooo.    .o8           o8o      ooooooooo.
# #  d8P'  `Y8b  "888           `"'      `888   `Y88.
# # 888      888  888oooo.     oooo       888   .d88' oooo d8b  .ooooo.  oo.ooooo.   .oooo.
# # 888      888  d88' `88b    `888       888ooo88P'  `888""8P d88' `88b  888' `88b `P  )88b
# # 888      888  888   888     888       888          888     888ooo888  888   888  .oP"888
# # `88b    d88'  888   888     888       888          888     888    .o  888   888 d8(  888
# #  `Y8bood8P'   `Y8bod8P'     888      o888o        d888b    `Y8bod8P'  888bod8P' `Y888""8o
# #                             888                                       888
# #                         .o. 88P                                      o888o
# #                         `Y888P


# def rasterize_obj(o, vg, img, mode="vg", margin=5, bench=True): 
#     """for each objects, preparate the mesh, get all the tris location and their vector weight, then rasterize all tris and return pixels array"""
    
#     # vg arg ->    [vg]       if mode == 'vg'     
#     #           or [vg,vg,vg] if mode == 'vg_rgb'                                                   
#     #           or vcol       if mode == 'vcol' 

#     if bench: 
#         _t = time.time()

#     #avoid empty vg

#     if mode == 'vg' or mode=='vg_rgb':
#         for vgroup in vg:
#             if vgroup:
#                 v_idx_array = np.indices((len(o.data.vertices), ))[0].tolist()
#                 vgroup.add(v_idx_array, 0.0, 'ADD', )

#     #evaluate modifiers

#     depsgraph = bpy.context.evaluated_depsgraph_get()
#     eo = o.evaluated_get(depsgraph)
#     ob = eo.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)

#     #make triangulated bmesh

#     bm = bmesh.new()
#     bm.from_mesh(ob)
#     bmesh.ops.triangulate(bm, faces=bm.faces, )

#     #put it in new mesh datablock

#     trime = bpy.data.meshes.new('tmp-{}'.format(uuid.uuid1()))
#     bm.to_mesh(trime)
#     bm.free()

#     #and to bmesh again.. may by skipped, if loop indices are somehow updated after triangulating..

#     bm = bmesh.new()
#     bm.from_mesh(trime)
#     bm.verts.ensure_lookup_table()
#     bm.faces.ensure_lookup_table()

#     deform_layer = bm.verts.layers.deform.active
#     tri_nbr      = len(bm.faces)

#     if bench: 
#         print(f"    -bmesh preparation done                  {datetime.timedelta(seconds=time.time()-_t)}")
#         _t = time.time()

#     #get all tris Pt 

#     tris = []
#     for face in bm.faces:
#         tri = []
#         for loop in face.loops:

#             #get uv coord 
#             u,v  = loop[bm.loops.layers.uv.active].uv 

#             #get pixel float coords from uv and res
#             x,y  = (u*res_x, v*res_y)

#             #get weight 'Vector', 3 mode possible 
#             if mode == 'vg':
#                 weight = loop.vert[deform_layer][vg[0].index]
#                 r = weight
#                 g = weight 
#                 b = weight
#             elif mode == 'vg_rgb':
#                 r,g,b = (0,0,0)
#                 if vg[0]: r = loop.vert[deform_layer][vg[0].index]
#                 if vg[1]: g = loop.vert[deform_layer][vg[1].index]
#                 if vg[2]: b = loop.vert[deform_layer][vg[2].index]
#             elif mode == 'vcol':
#                 r = loop[bm.loops.layers.color[vg.name]][0]
#                 g = loop[bm.loops.layers.color[vg.name]][1]
#                 b = loop[bm.loops.layers.color[vg.name]][2]

#             tri.append( [x, y, r, g, b] )
#         tris.append(tri)

#     #bmesh cleanup
#     bm.free()
#     bpy.data.meshes.remove(trime)

#     #TODO optimize above ????

#     if bench: 
#         print(f"    -getting all tris                        {datetime.timedelta(seconds=time.time()-_t)}")
#         _t = time.time()

#     ###############################################################################################################
#     ###############################################################################################################
#     #-> CPP
#     #use own compiled function on numpy array

#     # create numpy pixels array and tris array, cpp function will directly read and write in memory
#     pixels = np.zeros((res_x, res_y, 4), dtype=np.float,)
#     tris = np.array(tris)

#     # rasterization 
#     rasterize_tris = get_compiled_fct("rasterize_tris")
#     # convert args types
#     rasterize_tris.restype  = None
#     rasterize_tris.argtypes = [ ndpointer(c_double), ndpointer(c_double), c_size_t, c_int ]
#     # combile fct source -> "Scatter/cpp/_rasterize_tris.cpp"
#     rasterize_tris(tris, pixels, len(tris), len(pixels))

#     if bench: 
#         print(f"    -raster for {tri_nbr:,} tris @{res_x}x{res_y}       {datetime.timedelta(seconds=time.time()-_t)}")
#         _t = time.time()

#     if margin != 0:
#         # pixel margin
#         pixel_margin = get_compiled_fct("pixel_margin")
#         # convert args types
#         pixel_margin.restype  = None
#         pixel_margin.argtypes = [ ndpointer(c_double), c_int, c_int ]
#         # combile fct source -> "Scatter/cpp/_pixel_margin.cpp"
#         pixel_margin(pixels, len(pixels), margin)

#         if bench: 
#             print(f"    -margin for {margin:02d} px                      {datetime.timedelta(seconds=time.time()-_t)}")
#             _t = time.time()

#     ###############################################################################################################
#     ###############################################################################################################
    

#     return pixels 



# # oooooooooooo oooo                       ooooooooo.
# # `888'     `8 `888                       `888   `Y88.
# #  888          888   .ooooo.              888   .d88' oooo d8b  .ooooo.  oo.ooooo.   .oooo.
# #  888oooo8     888  d88' `88b             888ooo88P'  `888""8P d88' `88b  888' `88b `P  )88b
# #  888    "     888  888ooo888             888          888     888ooo888  888   888  .oP"888
# #  888       o  888  888    .o  888        888          888     888    .o  888   888 d8(  888
# # o888ooooood8 o888o `Y8bod8P'  888       o888o        d888b    `Y8bod8P'  888bod8P' `Y888""8o
# #                                                                          888
# #                                                                         o888o




# def rasterize_elements(o, vg_names, mode='vg', resolution=1024, path=None, rgb_name=None, rgb_vg_names=None, anim_name=False, margin=4, bench=True):
#     """for each elements, get the vertex groups arrayt=, rasterize_obj will get the pixel array , then create and export the image"""


#     def get_img(name,res_x,res_y):

#         img = bpy.data.images.get(name)
#         if (img is None) or ((img.size[0]!=res_x) or (img.size[1]!=res_y)):
#             if img is not None: 
#                 bpy.data.images.remove(img)
#             img = bpy.data.images.new(name, res_x, res_y)
#         return img 

#     def export_img(img,name,filepath_raw,file_format="PNG"):

#         if os.path.exists(filepath_raw):
#             file_name = name.replace(".","_").replace(" ","_").replace(":","").replace("/","")
#             img.filepath_raw = os.path.join(filepath_raw,f"{file_name}.{file_format.lower()}")
#             img.file_format = file_format
#             img.save()
#             return True
#         return False 


#     _tot = time.time()  
#     if bench:
#         print("")
#         print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
#         print(f">>> Launching Calculations for frame {bpy.context.scene.frame_current}...")

#     #bake each elements

#     for i,name in enumerate(vg_names):

#             if mode=="vg_rgb":
#                 name=rgb_name

#             if bench:
#                 print("")
#                 print(f"> Calculating element {i} [{name}]")
#                 _e = time.time()  
#                 _f = time.time()  

#             #get img data

#             img_name = name 
#             if anim_name:
#                 img_name += f"_{bpy.context.scene.frame_current:03d}"

#             global res_x,res_y 
#             res_x   = int(resolution)
#             res_y   = int(resolution)
#             img = get_img(img_name,res_x,res_y)

#             if bench:
#                 print(f"  -launching rasterization :")

#             #rasterize obj

#             if mode=="vg":
#                 vg = [ o.vertex_groups[name] ]
#                 pixels = rasterize_obj( o ,vg, img, mode=mode, margin=margin, bench=bench)
#                 #
#             elif mode=="vcol":
#                 vg = o.data.vertex_colors[name]
#                 pixels = rasterize_obj( o ,vg, img, mode= mode, margin=margin, bench=bench)
#                 #
#             elif mode=="vg_rgb":
#                 r = o.vertex_groups[rgb_vg_names[0]] if rgb_vg_names[0] else 0 
#                 g = o.vertex_groups[rgb_vg_names[1]] if rgb_vg_names[1] else 0 
#                 b = o.vertex_groups[rgb_vg_names[2]] if rgb_vg_names[2] else 0 
#                 vg = [r,g,b]
#                 pixels = rasterize_obj( o ,vg, img, mode=mode, margin=margin, bench=bench)

#             if bench:
#                 print(f"  -rasterization done !                    {datetime.timedelta(seconds=time.time()-_e)}")
#                 _e = time.time()  

#             #write pixels to img #-> https://devtalk.blender.org/t/bpy-data-images-perf-issues/6459

#             pixels.shape = (res_x*res_y*4, )
#             img.pixels.foreach_set(pixels.tolist()) #->https://developer.blender.org/D7053, not that fast? still 9sec for 8k texture. why?
#             img.update()

#             if bench:
#                 print(f"  -pixels array to image data              {datetime.timedelta(seconds=time.time()-_e)}")
#                 _e = time.time()  

#             #write img to disk 

#             if path: 
#                 success = export_img(img, img_name, path)
#                 if bench and success:
#                     print(f"  -exported the image to disk              {datetime.timedelta(seconds=time.time()-_e)}")

#             if bench:
#                 print(f"> Element {i} Done!                          {datetime.timedelta(seconds=time.time()-_f)}")

#             if mode=="vg_rgb":
#                 break 

#             continue 

#     seconds = datetime.timedelta(seconds=time.time()-_tot)
#     if bench:
#         print("")
#         print(f">>> Baking {len(vg_names)} elements for frame {bpy.context.scene.frame_current} Done!   {seconds}")
#         print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
#         print("")

#     return



# ###############################################################################################################
# #
# # oooooooooo.    o8o            oooo                            oooooooooo.
# # `888'   `Y8b   `"'            `888                            `888'   `Y8b
# #  888      888 oooo   .oooo.    888   .ooooo.   .oooooooo       888     888  .ooooo.  oooo    ooo
# #  888      888 `888  `P  )88b   888  d88' `88b 888' `88b        888oooo888' d88' `88b  `88b..8P'
# #  888      888  888   .oP"888   888  888   888 888   888        888    `88b 888   888    Y888'
# #  888     d88'  888  d8(  888   888  888   888 `88bod8P'        888    .88P 888   888  .o8"'88b
# # o888bood8P'   o888o `Y888""8o o888o `Y8bod8P' `8oooooo.       o888bood8P'  `Y8bod8P' o88'   888o
# #                                               d"     YD
# #                                               "Y88888P'
# ###############################################################################################################



# class SCATTER5_OT_bake_vertex_groups(bpy.types.Operator):

#     bl_idname = "scatter5.bake_vertex_groups"
#     bl_label = translate("Scatter Mask(s) to Bitmap(s) Baking Tool")
#     bl_description = ""
#     bl_options = {'INTERNAL'}


#     mode : bpy.props.EnumProperty(
#         default    = "vg",
#         items      = [("vg"    ,translate("Vertex Group")              ,"","WPAINT_HLT",1 ),
#                       ("vg_rgb",translate("Vertex Group (Combine RGB)"),"","WPAINT_HLT",2 ),
#                       ("vcol"  ,translate("Vertex Color")              ,"","VPAINT_HLT",3 ),
#                       ],) 

#     resolution : bpy.props.EnumProperty(
#         default    = "1024",
#         items      = [("256"    ,"256x256" ,"" ,4  ),
#                       ("512"    ,"512x512" ,"" ,5  ),
#                       ("1024"   ,"1k"      ,"" ,6  ),
#                       ("2048"   ,"2k"      ,"" ,7  ),
#                       ("4096"   ,"4k"      ,"" ,8  ),
#                       ("8192"   ,"8k"      ,"" ,9  ),
#                       ("custom" ,"Custom"  ,"" ,10 ),
#                       ],) 

#     margin : bpy.props.IntProperty(
#         default=0, 
#         min=0,
#         soft_max=10, 
#         max=500, 
#         subtype="PIXEL",
#         )

#     custom_resolution : bpy.props.IntProperty(
#         default=1500,
#         min=16,
#         max=8192,
#         subtype="PIXEL",
#         )

#     bake_animation : bpy.props.BoolProperty()

#     nbr : bpy.props.IntProperty(
#         default=1,
#         min=1,
#         max=10,
#         )

#     vg01 : bpy.props.StringProperty(name="01")
#     vg02 : bpy.props.StringProperty(name="02")
#     vg03 : bpy.props.StringProperty(name="03")
#     vg04 : bpy.props.StringProperty(name="04")
#     vg05 : bpy.props.StringProperty(name="05")
#     vg06 : bpy.props.StringProperty(name="06")
#     vg07 : bpy.props.StringProperty(name="07")
#     vg08 : bpy.props.StringProperty(name="08")
#     vg09 : bpy.props.StringProperty(name="09")
#     vg10 : bpy.props.StringProperty(name="10")

#     path : bpy.props.StringProperty(default=os.path.normpath(os.path.expanduser("~/Desktop")))

#     rgb_name : bpy.props.StringProperty(default="MASK_RGB")

#     pop_msg : bpy.props.BoolProperty(default=True)



#     def invoke(self, context, event):
#         return context.window_manager.invoke_props_dialog(self)


#     def draw(self, context):

#         layout  = self.layout
#         emitter = bpy.context.scene.scatter5.emitter


#         box, is_open = ui_templates.box_panel(self, layout, 
#             prop_str = "baking_boxpanel", 
#             icon = "RENDER_STILL", 
#             name = translate("Settings"),
#             )
#         if is_open:

#                 box.prop(self,"mode",text=translate("Mode"))
#                 box.prop(self,"resolution",text=translate("Resolution"))
#                 if self.resolution=="custom":
#                     prp = box.row()
#                     lbl = prp.row()
#                     lbl.scale_x = 0.55
#                     lbl.label(text=" ")
#                     prp.prop(self,"custom_resolution",text=translate("Custom Square Resolution"))

#                 prp = box.row()
#                 lbl = prp.row()
#                 lbl.scale_x = 0.55
#                 lbl.label(text=translate("Margin:"))
#                 prp.prop(self,"margin",text=translate("Pixel Margin"))

#                 if self.mode=="vg_rgb":
#                     box.prop(self,"rgb_name",text=translate("File Name"))
#                 p = box.row()
#                 p.alert = not os.path.exists(self.path)
#                 p.prop(self,"path",text=translate("Folder"))

#                 row = box.row()
#                 lbl = row.row()
#                 lbl.label(text=translate("Animation:"))
#                 lbl.scale_x  = 0.29
#                 row.prop(self,"bake_animation",text=translate("Enable Timeline Baking"),icon="CAMERA_DATA")
#                 if self.bake_animation:
#                     prp = box.row()
#                     lbl = prp.row()
#                     lbl.scale_x = 0.55
#                     lbl.label(text="")
#                     prp.prop(bpy.context.scene,"frame_start")

#                     prp = box.row()
#                     lbl = prp.row()
#                     lbl.scale_x = 0.55
#                     lbl.label(text="")
#                     prp.prop(bpy.context.scene,"frame_end")


#                 box.separator()


#         box, is_open = ui_templates.box_panel(self, layout, 
#             prop_str = "baking_sub2", 
#             icon = "GROUP_VERTEX", 
#             name = translate("Element(s)"),
#             )
#         if is_open:

#                 box.label(text=translate("Bake the element(s) below"))
                
#                 if not self.mode=="vg_rgb":

#                     row = box.row(align=True)
#                     row.label(text=translate("Number of Elements to Bake :"))
#                     app=row.row()
#                     app.scale_x = 0.6
#                     app.prop(self,"nbr",text="")
                    
#                     for i in range(1,self.nbr+1):
#                         if self.mode=="vg":
#                               box.prop_search(self, f"vg{i:02d}", emitter, "vertex_groups",)
#                         else: box.prop_search(self, f"vg{i:02d}", emitter.data, "vertex_colors",)
#                 else: 
#                     box.prop_search(self, f"vg01", emitter, "vertex_groups",text="R")
#                     box.prop_search(self, f"vg02", emitter, "vertex_groups",text="G")
#                     box.prop_search(self, f"vg03", emitter, "vertex_groups",text="B")

#                 box.separator()


#         box, is_open = ui_templates.box_panel(self, layout, 
#             prop_str = "baking_sub3", 
#             icon = "INFO", 
#             name = translate("Information"),
#             )
#         if is_open:

#                 resolution = int(self.resolution) if  self.resolution!="custom" else self.custom_resolution
#                 elements = self.nbr if self.mode != "vg_rgb" else 1
#                 frames = (bpy.context.scene.frame_end - bpy.context.scene.frame_start) if self.bake_animation else 1
#                 tris = len(emitter.data.vertices) *2

#                 #estimate one element
#                 estimation = 0

#                 #estimate time of raster+write img
#                 if   resolution<1000: estimation+= 1
#                 elif resolution<2100: estimation+= 2
#                 elif resolution<4100: estimation+= 5
#                 elif resolution<8200: estimation+= 20
#                 else:                 estimation+= 75

#                 #estimate bmesh prep and getting all tris
#                 if   tris<200_000   : estimation+= 1
#                 elif tris<450_000   : estimation+= 2
#                 elif tris<1_000_000 : estimation+= 10
#                 elif tris<2_000_000 : estimation+= 24
#                 elif tris<4_000_000 : estimation+= 48
#                 elif tris<8_000_000 : estimation+= 120
#                 else:                 estimation+= 400

#                 estimation = estimation * frames * elements
#                 minutes, seconds = divmod(estimation, 60)

#                 #first label, statistic
#                 text=box.column()
#                 text.scale_y = 0.8
#                 v= text.row()
#                 v.alert = len(emitter.data.vertices)>2_000_000
#                 v.label(text=translate("Emitter verts-count: ")+ "         "+ f"{len(emitter.data.vertices):,}"  )
#                 text.label(text=translate("Elements to bake:")+ "              "+ str(elements if self.mode != "vg_rgb" else 3) )
#                 text.label(text=translate("Chosen Resolution: ")+ "           "+ str(resolution)+"x"+str(resolution)+" px" )
#                 if self.bake_animation:
#                     text.label(text=translate("Number of Frames: ")+ "           "+ str(frames) )

#                 t = text.row()
#                 t.alert = estimation>540
#                 t.label(text=translate("Estimated baking time: ")+ "    "+ f"{minutes:02d}m {seconds:02d}s" )

#                 #second label, general information

#                 #TODO Dorian, once you rework the baking module, use word_wrap function instead of this shit 

#                 # text=box.column()
#                 # text.scale_y = 0.8
#                 # r = text.row()
#                 # r.alignment="CENTER"
#                 # r.label(text=translate("The mesh will be triangulated in Calculations"))
#                 # r = text.row()
#                 # r.alignment="CENTER"
#                 # r.label(text=translate("The result will be available in blender image-data"))
#                 # r = text.row()
#                 # r.alignment="CENTER"
#                 # r.label(text=translate("Open the console to see your advancements"))
#                 # r = text.row()
#                 # r.alignment="CENTER"
#                 # r.label(text=translate("click 'OK' or press 'ENTER' to start baking"))

#                 box.separator()


#         return 


#     def execute(self, context):    

#         _p = time.time()  

#         emitter = bpy.context.scene.scatter5.emitter

#         #get all elements 
#         vg_names = []
#         max_range = self.nbr if not self.mode=="vg_rgb" else 3
#         for i in range (1,11):
#             if i>max_range:
#                 break
#             name = eval(f"self.vg{i:02d}")
#             if name :
#                 if name not in vg_names:
#                     vg_names.append(name)

#         #bake animation support frame range 
#         if self.bake_animation:
#               frames = bpy.context.scene.frame_end+1 - bpy.context.scene.frame_start
#         else: frames = 1

#         #loop over frames
#         for i in range(frames):

#             if self.bake_animation:
#                 bpy.context.scene.frame_current = i
#                 handler_update_graph_remap()
#                 refresh_selected()

#             # rasterize_elements -> rasterize_obj -> rasterize_tris
#             rasterize_elements(emitter, vg_names, 
#                 mode         = self.mode, 
#                 resolution   = self.resolution if self.resolution!="custom" else self.custom_resolution, 
#                 path         = self.path, 
#                 rgb_name     = self.rgb_name, 
#                 rgb_vg_names = [self.vg01, self.vg02, self.vg03 ],
#                 anim_name    = self.bake_animation,
#                 margin     = self.margin,
#                 bench        = True,
#                 )

#         seconds = datetime.timedelta(seconds=time.time()- _p)
#         if self.pop_msg:
#             pass
#             #animation support add for x frames
#             #Dorian, You will need to use the proper popup_dialog operator instead of this function
#             # f'Baking {len(vg_names)} element(s) for {frames} frame(s) took "{seconds}" The File(s) are available in blender image-data' ,"", "",

#         return {'FINISHED'}




# # ooooooooo.                         o8o               .
# # `888   `Y88.                       `"'             .o8
# #  888   .d88'  .ooooo.   .oooooooo oooo   .oooo.o .o888oo  .ooooo.  oooo d8b
# #  888ooo88P'  d88' `88b 888' `88b  `888  d88(  "8   888   d88' `88b `888""8P
# #  888`88b.    888ooo888 888   888   888  `"Y88b.    888   888ooo888  888
# #  888  `88b.  888    .o `88bod8P'   888  o.  )88b   888 . 888    .o  888
# # o888o  o888o `Y8bod8P' `8oooooo.  o888o 8""888P'   "888" `Y8bod8P' d888b
# #                        d"     YD
# #                        "Y88888P'




# classes = (
    
#     SCATTER5_OT_bake_vertex_groups,

#     )


# def register():
#     for cls in classes:
#         bpy.utils.register_class(cls)
#     return 



# def unregister():
#     for cls in reversed(classes):
#         bpy.utils.unregister_class(cls)
#     return 


# # if __name__ == "__main__":
