
#extension of the os.path module i guess? 

import bpy
import os
import json
import glob

def dict_to_json(d, path="", file_name="", extension=".json", ):
    """ dict > .json, will write json to disk"""

    json_path = os.path.join( path, f"{file_name}{extension}" ) #filename = w o extension!!!
    with open(json_path, 'w') as f:
        json.dump(d, f, indent=4)

    return None

def json_to_dict(path="", file_name=""):
    """.json -> dict"""

    json_path = os.path.join( path, file_name )

    if (not os.path.exists(json_path)):
        print(f"path_utils.json_to_dict() -> it seems that the json file do not exists? [{json_path}]")
        return {}

    with open(json_path) as f:
        d = json.load(f)

    return d

def get_direct_folder_paths(main):
    """get all directories paths within given path"""
    for _, dirnames, _ in os.walk(main):
        return [os.path.join(main,d) for d in dirnames]

def get_direct_files_paths(main):
    """get all files paths within given path"""
    for _, _, files in os.walk(main):
        return [os.path.join(main,d) for d in files]

def get_subpaths(folder, file_type="", excluded_files=[], excluded_folders=[".git","__pycache__",],):
    """get all existing files paths within the given folder"""
    r = []
    for main,dirs,files in os.walk(folder, topdown=True):
        dirs[:] = [d for d in dirs if d not in excluded_folders]
        if (excluded_files!=[]):
            files = [f for f in files if f not in excluded_files]
        for file in files:
            if ( (file_type!="") and (not file.endswith(file_type)) ):
                continue
            r.append(os.path.join(main,file))
            continue
    return r

def get_parentfolder(folder="", depth=1,):
    """get parent folder from given depth"""

    for _ in range(depth):
        folder = os.path.dirname(folder)

    return folder

def glob_subfolders(folder="", depth="all",):
    """get list of folders at given depths"""

    if (depth=="all"):
        
        arg = os.path.join(folder,"**/")

        return glob.glob(arg, recursive=True,)

    elif (depth>=0):

        lvl = "*/"*(depth+1)
        arg = os.path.join(folder,lvl)

        return glob.glob(arg, recursive=True,)
    
    elif (depth<0):

        depth = abs(depth)
        folder = get_parentfolder(folder, depth=depth)
        arg = os.path.join(folder,"*/")

        return glob.glob(arg, recursive=True,)

    raise Exception("glob_subfolders() -> bad depth arg")  

def folder_match_search(folder="C:/", folderdepth=0, file="file.txt",):
    """search by overviewing all folders and checking if file exists at these locations, faster method?"""

    if (folderdepth==0):
        filepath = os.path.join(folder,file)
        if (os.path.exists(filepath)):
            return filepath

    for f in glob_subfolders(folder=folder, depth=folderdepth,):
        f = os.path.normpath(f)
        filepath = os.path.join(f,file)
        if (os.path.exists(filepath)):
            return filepath
        continue

    return "" 

def search_for_path(keyword="", search_first=None, search_folder=None, search_others=[], file_type="",):
    """search everywhere for a file, if found, return it's path else return None, the search order is the following:
       1) "search_first" check if exists in level 0 & 1
       2) "search_first" check if exists in level -1
       3) "search_folder" check if exists in all subfolders
       4) "search_others" check if exists in level 0 & 1
       5) "search_others" check if exists in level 2
       6) "search_others" check if exists in level 3
    """

    #TODO could improve this function, used consistently in biome loading!

    if (not os.path.exists(search_folder)):
        raise Exception("The path you gave doesn't exists")

    if (file_type):
        if (not keyword.endswith(file_type)):
            keyword += file_type

    #first try to search in priority folder
    if (search_first is not None):

        if (not os.path.exists(search_first)):
            raise Exception("The path you gave doesn't exists (search_first)")

        #file exists in +1 level or level 0?
        p = folder_match_search(folder=search_first, folderdepth=0, file=keyword,)
        if (p!=""):
            return p

        #in parent folder? lelvel -1?
        p = os.path.join(os.path.dirname(search_first),keyword)
        if (os.path.exists(p)):
            return p

    #else search everywhere in main library
    p = folder_match_search(folder=search_folder, folderdepth="all", file=keyword,)
    if (p!=""):
        return p

    #else search in collection of other paths given
    if (len(search_others)!=0):
        search_others = [pt for pt in search_others if (os.path.exists(pt)) ]

        #exists in level 0 or level 1 ?
        for pt in search_others:
            p = folder_match_search(folder=pt, folderdepth=0, file=keyword,)
            if (p!=""):
                return p

        #lelvel 2 ?
        for pt in search_others:
            p = folder_match_search(folder=pt, folderdepth=1, file=keyword,)
            if (p!=""):
                return p

        #level 3 ?
        for pt in search_others:
            p = folder_match_search(folder=pt, folderdepth=2, file=keyword,)
            if (p!=""):
                return p

    return "" #nothing found 


# def search_for_paths(search_paths, keywords,):
#     """https://stackoverflow.com/questions/74113035/fastest-way-to-search-many-files-in-many-directories/74113561#74113561"""

#     for p in search_paths:
#         if (not os.path.exists(p)):
#             raise Exception(f"following path do not exists: {p}")

#     def process_directory(directory):
#         output = []
#         for root, _, files in os.walk(directory):
#             for file in files:
#                 if (file in keywords):
#                     output.append(os.path.join(root, file))
#                     keywords.remove(file)
#         return output

#     paths = []

#     from concurrent.futures import ThreadPoolExecutor

#     with ThreadPoolExecutor() as executor:
#         for rv in executor.map(process_directory, search_paths):
#             paths.extend(rv)

#     return keywords, paths



#   .oooooo.   oooo
#  d8P'  `Y8b  `888
# 888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
# 888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
# 888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
# `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#  `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'


class SCATTER5_OT_open_directory(bpy.types.Operator):

    bl_idname      = "scatter5.open_directory"
    bl_label       = ""
    bl_description = ""

    folder : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)

    def execute(self, context):

        import subprocess
        import shlex
        import platform

        if (not os.path.exists(self.folder)):
            from .. resources.translate import translate
            bpy.ops.scatter5.popup_menu(msgs=translate("The folder you are trying to open does not exists")+f"\n{self.folder}",title=translate("Error!"),icon="ERROR")
            return {'FINISHED'}             

        if (platform.system()=="Windows"):
            os.startfile(self.folder)

        elif (platform.system()=="Linux"):
            subprocess.call(['xdg-open', self.folder])

        elif (platform.system()=="Darwin"):
            os.system('open {}'.format(shlex.quote(self.folder)))

        return {'FINISHED'} 


classes = (

    SCATTER5_OT_open_directory,

    )
