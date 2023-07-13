#pylint: disable=import-error, relative-beyond-top-level
import bpy
from . smr_common import ShowMessageBox
from . mat_functions import get_mat_data
from pathlib import Path
import os
from . pcoll import preview_collections

def update_image(categ_prev, categ_type):
    SMR_settings = bpy.context.scene.SMR
    mat, nodes, links = get_mat_data()
    categ_type_lower = categ_type.lower()
    
    sub_path= categ_prev
    image_namecheck = os.path.basename(sub_path)
    if SMR_settings.diagnostics:
        print('namecheck is {}'.format(image_namecheck))    
    
    filepath = SMR_settings.SMR_path +str(Path('/{}'.format(categ_type_lower))) + sub_path
    
    images = bpy.data.images
    try:
        images.load(filepath, check_existing=True)
    except RuntimeError:
        if SMR_settings.diagnostics:
            raise
        ShowMessageBox("Could not load image, please check file path", "What the smudge!", 'INFO')
        return
    except:
        raise
    if SMR_settings.diagnostics:
        print('loading {}'.format(filepath))
    block_image = images[image_namecheck]
    image_node =  nodes['SMR_{}_Texture'.format(categ_type)]
    image_node.image = block_image
    try:
        image_node_AT =  nodes['SMR_{}_Texture_AT'.format(categ_type)] 
        image_node_AT.image = block_image
    except:
        pass

class SMR_OT_NEXT(bpy.types.Operator):
    bl_idname = "smr.next"
    bl_label = "Next"
    bl_description = "Next image"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):        
        next_previous(True)                          
        return {'FINISHED'}

class SMR_OT_PREVIOUS(bpy.types.Operator):
    bl_idname = "smr.previous"
    bl_label = "Previous"
    bl_description = "Previous image"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        next_previous(False)                   
        return {'FINISHED'}


def find_smudge_categ(image_name):
    dir = bpy.context.scene.SMR.SMR_path + str(Path('/smudge'))

    assert os.path.isdir(dir)
    num_sep = dir.count(os.path.sep)
    image_paths = []
    for root, dirs, files in os.walk(dir):
        for fn in files:
            if fn == image_name:
                categ = os.path.basename(root)
                categ_dir = str(Path('/{}'.format(categ)))    

                return categ_dir
      

def change_scratch_res(self,context):
    res = context.scene.SMR.scratch_res
    change_res_general('Scratch', res)

def change_smudge_res(self, context):
    res = context.scene.SMR.smudge_res
    change_res_general('Smudge', res)

def change_res_general(categ, res):    
    SMR_settings = bpy.context.scene.SMR
    mat, nodes, links = get_mat_data()
    
    if categ == 'Scratch':
        image_namecheck = nodes['SMR_Scratch_Texture'].image.name
        file_folder = str(Path('/scratch/'))
    elif categ == 'Smudge':
        image_namecheck = nodes['SMR_Smudge_Texture'].image.name
        subcateg = find_smudge_categ(image_namecheck)
        if categ:
            file_folder = str(Path('/smudge/')) + subcateg
        else:
            file_folder = str(Path('/smudge/'))
            

    images = bpy.data.images

    filename, file_extension = os.path.splitext(image_namecheck)

    #finds the file with the same name, but other resolution
    new_filename= filename[:-2] + res
    filepath = SMR_settings.SMR_path + file_folder + str(Path('/{}'.format(new_filename))) + file_extension

    #load that image
    #try:
    bpy.data.images.load(filepath, check_existing=True)
    #except:
    #    ShowMessageBox("This texture does not have a variant in this resolution", "What the smudge!", 'INFO')

    #assign to node
    image_name = new_filename + file_extension
    block_image = images[image_name]
    image_node =  nodes['SMR_{}_Texture'.format(categ)]
    image_node.image = block_image
    try:
        AT_image_node =  nodes['SMR_{}_Texture_AT'.format(categ)]
        AT_image_node.image = block_image
    except:
        pass


def update_dust(self, context):
    SMR_settings = bpy.context.scene.SMR
    categ_prev = SMR_settings.prev_dust
    
    update_image(categ_prev, 'Dust')

def update_smudge(self, context):
    SMR_settings = bpy.context.scene.SMR
    categ_prev = SMR_settings.prev_smudge
    update_image(categ_prev, 'Smudge')  
    SMR_settings.active_smudge_ui = categ_prev
    SMR_settings.smudge_res = '1K'

def update_scratch(self, context):
    SMR_settings = bpy.context.scene.SMR
    categ_prev = SMR_settings.prev_scratch
    update_image(categ_prev, 'Scratch')
    SMR_settings.active_scratch_ui = categ_prev
    SMR_settings.scratch_res = '1K'

def update_droplets(self, context):
    SMR_settings = bpy.context.scene.SMR
    categ_prev = SMR_settings.prev_droplets
    
    update_image(categ_prev, 'Droplets')




        
def update_dir(self, context):
    """
    refreshes file path
    """ 

    if self.SMR_path.startswith('//'):
        self['SMR_path'] = bpy.path.abspath(self.SMR_path) 
    
    update_dir_type('smudge')
    update_dir_type('scratch')
    update_dir_type('dust')
    update_dir_type('droplets')

def update_dir_type(icon_type):
    SMR_Settings = bpy.context.scene.SMR
  
    enum_items = []
    if not 'previews_dir_{}'.format(icon_type) in SMR_Settings:
        SMR_Settings['previews_dir_{}'.format(icon_type)] = ''
    if not 'previews_list_{}'.format(icon_type) in SMR_Settings:
        SMR_Settings['previews_list_{}'.format(icon_type)] = []
            
    SMR_Settings['previews_list{}'.format(icon_type)] = []
    
    previews_list = []        
    if icon_type == 'smudge':
        if SMR_Settings.smudge_categ == 'All':
            category_path = ''
            recursion = 1        
        else:    
            category_path = str(Path('/{}'.format(SMR_Settings.smudge_categ)))
            recursion = 0
 
        
        previews_folder = bpy.path.abspath(SMR_Settings['SMR_path'])+ str(Path('/{}'.format(icon_type))) + category_path
    else:
        previews_folder = bpy.path.abspath(SMR_Settings['SMR_path'])+ str(Path('/{}'.format(icon_type)))
        recursion = 0
            
    pcoll = preview_collections["prev_{}".format(icon_type)]
    if os.path.exists(bpy.path.abspath(previews_folder)):

        image_paths = get_dir_images(previews_folder, recursion, icon_type)    
        for i, name in enumerate(image_paths):            
            if icon_type == 'smudge':
                previews_folder = previews_folder.replace(category_path, '')
            if icon_type == 'dust' or icon_type == 'droplets':
                filepath_thumb = previews_folder + str(name)
            else:
                filepath_thumb = previews_folder + str(name).replace('1K', '0K')
            if not pcoll.get(filepath_thumb):
                thumb = pcoll.load(filepath_thumb, filepath_thumb, 'IMAGE')
            else: thumb = pcoll[filepath_thumb]   
  
            enum_items.append((name, name, name, thumb.icon_id, i))
            previews_list.append(name)
        SMR_Settings['previews_list_{}'.format(icon_type)] = previews_list    
    
    if icon_type == 'smudge':
        pcoll.prev_smudge = enum_items
        pcoll.previews_dir_smudge = previews_folder
    elif icon_type == 'scratch':
        pcoll.prev_scratch = enum_items
        pcoll.previews_dir_scratch = previews_folder  
    elif icon_type == 'dust':
        pcoll.prev_dust = enum_items
        pcoll.previews_dir_dust = previews_folder 
    elif icon_type == 'droplets':
        pcoll.prev_droplets = enum_items
        pcoll.previews_dir_droplets = previews_folder              
        
    if len(previews_list) > 0:
        SMR_Settings['SMR_path_{}'.format(icon_type)] = previews_list[0]       
    return None  

def get_dir_images(dir, level = 1, icon_type = 'Smudge'):    
    """
    gets a list of jpg, jpeg and png images in folder
    """
    SMR_Settings = bpy.context.scene.SMR
    

    assert os.path.isdir(dir)
    num_sep = dir.count(os.path.sep)
    image_paths = []
    for root, dirs, files in os.walk(dir):
        for fn in files:
            #possible extensions
            extensions= ['jpeg','jpg','png','tif','tiff']
            for ext in extensions:
                if fn.lower().endswith("1k.{}".format(ext)):
                    if icon_type == 'smudge' and SMR_Settings.smudge_categ != 'All':
                        subcateg = str(Path('/{}'.format(SMR_Settings.smudge_categ)))
                        image_paths.append(subcateg + os.path.join(root, fn).replace(dir, '')) 
                    else:
                        image_paths.append(os.path.join(root, fn).replace(dir, ''))
                elif fn.lower().endswith(".{}".format(ext)) and icon_type == 'droplets':
                    image_paths.append(os.path.join(root, fn).replace(dir, ''))               
        num_sep_this = root.count(os.path.sep)
        if num_sep + level <= num_sep_this:
            del dirs[:]
    if SMR_Settings.diagnostics:
        print('getting images for {} in {}'.format(icon_type, dir))
        print('found images {}'.format(image_paths))
    return image_paths

def smudge_previews (self, context):
    """
    gets previews for the image icons in the panel
    """
    pcoll = preview_collections.get('prev_smudge')
    if not pcoll:
        return []
    return pcoll.prev_smudge

def scratch_previews (self, context):
    """
    gets previews for the image icons in the panel
    """
    pcoll = preview_collections.get('prev_scratch')
    if not pcoll:
        return []
    return pcoll.prev_scratch

def dust_previews (self, context):
    """
    gets previews for the image icons in the panel
    """
    pcoll = preview_collections.get('prev_dust')
    if not pcoll:
        return []
    return pcoll.prev_dust        

def droplets_previews (self, context):
    """
    gets previews for the image icons in the panel
    """
    pcoll = preview_collections.get('prev_droplets')
    if not pcoll:
        return []
    return pcoll.prev_droplets

def change_smudge_categ (self, context):
    update_dir_type('smudge')

def next_previous(next = True):
    SMR_settings = bpy.context.scene.SMR
    
    categ=SMR_settings.smr_ui_categ
    image_categ= categ.lower()
    
    list = SMR_settings["previews_list_{}".format(image_categ)]
    if image_categ == 'smudge':
        prev = SMR_settings.prev_smudge
    elif image_categ == 'dust':
        prev = SMR_settings.prev_dust
    elif image_categ == 'scratch':
        prev = SMR_settings.prev_scratch
    elif image_categ == 'droplets':
        prev = SMR_settings.prev_droplets    
    else:
        pass
    #elif image_categ == 'scratch':
    #    prev = SMR_settings.prev_dust            
    #OTHER CATEGORIES HERE
    
    count = len(list)
    
    if next:
        index = list.index(prev) + 1
        if index > count - 1:
            index = 0
    else:
        index = list.index(prev) - 1
        if index < 0:
            index = count-1
            
    image = list[index]     
    if image != prev:
        if image_categ == 'smudge':
            SMR_settings.prev_smudge = image
        elif image_categ == 'dust':
            SMR_settings.prev_dust = image
        elif image_categ == 'scratch':
            SMR_settings.prev_scratch = image   
        elif image_categ == 'droplets':
            SMR_settings.prev_droplets = image                  