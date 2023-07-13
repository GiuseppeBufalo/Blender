

#This script is meant to roughly converting Scatter4 biomes into Scatter5 files or batch change values in whole library 
#It's not used by the plugin i run it directly and change it on the fly

import enum
import os, json, shutil


#OLD  = "C:/Users/doria/AppData/Roaming/Blender Foundation/Blender/2.90/scripts/addons/Scatter Library/__biomes__/__presets__"
F  = "C:/Users/doria/AppData/Roaming/Blender Foundation/Blender/data/scatter library/_biomes_/Scatter Pro/"

def find_path(folder, file_name):
    for f in  [os.path.join(r,file) for r,d,f in os.walk(folder) for file in f]:
        if f.endswith(file_name):
            return f

def create_biome_for_all_s4_layer(old_layers_directory, new_directory):
    """pass over all your single layer file and convert them, will try to find the preset automatically"""

    #note that Scatter4 biomes use a special Layering system, so this file is made for this layer structure
    #Script won't work straight out the box if the biomes are NOT using this layer system

    for f in os.listdir(old_layers_directory):
        if f.startswith("l_") and f.endswith(".py"):

            filepath = os.path.join(old_layers_directory,f)
            file = open(filepath, "r")
            old = [l.replace("\n","").split("=") for l in file if (l.startswith("objects") or l.startswith("preset") or l.startswith("blend") or l.startswith("namee"))]
            old = {k.replace(" ",""):eval(",".join(v.split(',')[:-1])) for k,v in old}
            file.close()

            future_biome_basename = f[2:].replace(".py","")
            if (future_biome_basename[0]=="."):
                future_biome_basename = future_biome_basename[1:]
            future_biome_path = os.path.join(new_directory,future_biome_basename+".biome")
            future_preset_basename = future_biome_basename+".layer00"
            future_preset_path = os.path.join(new_directory,future_preset_basename+".preset")

            #need to get jpeg name to get keywords back
            jpeg_name =  [n for n in os.listdir(old_layers_directory) if n.startswith(f.replace(".py","")+"#") ]
            if jpeg_name:
                  jpeg_name = jpeg_name[0]
            else: jpeg_name = ""

            old_preset_path = os.path.join(old_layers_directory,"__presets__",old["preset"])
            if not os.path.exists(old_preset_path):
                raise Exception(f"Couldn't find {old_preset_path}")
            p = s4_preset_to_dict(old_preset_path)

            d = {}
            d["info"] = {}
            d["info"]["name"] = old["namee"]
            d["info"]["type"] = "Biome"
            d["info"]["keywords"] = ",".join(jpeg_name.split("@")[0].split("#")[1:]).title()
            d["info"]["author"] = "BD3D"
            d["info"]["website"] = "https://twitter.com/geoscatter"
            d["info"]["description"] = "Biome Layer from the official builtin Scatter Library"
            d["info"]["layercount"] = 1
            d["info"]["estimated_density"] = -1 #NO EASY SUPPORT, NEEED OVERWRITE

            d["00"] = {}
            d["00"]["name"] = d["info"]["name"]
            d["00"]["color"] = p["s_color"]
            d["00"]["preset"] = "BASENAME.layer00.preset"
            d["00"]["instances"] = old["objects"].split(",")
            d["00"]["asset_file"] = "scatter_builtin_library"
            #d["00"]["display"] = "" #NO EASY SUPPORT, NEEED OVERWRITE


            #write .biome file
            with open(future_biome_path, 'w') as f:
                json.dump(d, f, indent=4)
            #write .preset file
            with open(future_preset_path, 'w') as f:
                json.dump(p, f, indent=4)

            continue
    
    return None 

def batch_replace_dict_value_in_json():
    """in this function i batch change/add values in json dict"""
    
    for p in [os.path.join(r,file) for r,d,f in os.walk(NEW) for file in f] :
        
        if not p.endswith(".biome"):
            continue

        with open(p) as f:
            d = json.load(f)

        for k,v in d.items():
            if k.isdigit():
                d[k]["asset_file"] = "scatter_free_library"
    
        with open(p, 'w') as f:
            json.dump(d, f, indent=4)

        continue

def batch_replace_estimated_density_in_all_presets():

    new_values = {'Autumn Bush Dead': 10.9827, 'Autumn Bush Fall': 5.2823, 'Autumn Bush Full': 2.2286, 'Autumn Leaves A': 7.889, 'Autumn Leaves B': 4.0505, 'Autumn Leaves C': 66.6755, 'Autumn Plant A': 7.7458, 'Autumn Plant B': 2.0052, 'Bushes Coniferous A': 0.1833, 'Bushes Deciduous A': 0.2865, 'Bushes Pine Small A': 0.2865, 'Bushes Rosemary': 0.888, 'Forest Branches': 9.2525, 'Forest Clover': 20.8254, 'Forest Dead Leaves': 50.0324, 'Forest Dead Leaves Cluster': 17.2619, 'Forest Ferns A': 1.9708, 'Forest Ferns B': 4.5718, 'Forest Moss': 52.5017, 'Forest Mossy Rock': 1.1745, 'Forest Seedlings': 13.515, 'Forest Young A': 1.7187, 'Forest Young B': 0.6245, 'Clover': 25.3743, 'Clover Pink': 5.4369, 'Daisies': 10.3754, 'Dandelion': 4.2968, 'Striped Grass Tiny': 150.2921, 'Striped Grass Clump': 9.4645, 'Grass Clump': 3.5406, 'Grass Dry': 4.7666, 'Grass Pattern': 31.642, 'Grass Small': 103.8633, 'Grass Wild': 2.3661, 'Grass Wild Dry': 9.6249, 'Leaves': 68.9615, 'Leaves L': 88.7842, 'Nettle': 24.0795, 'Paperwhite': 12.2374, 'Red Poppy': 10.3296, 'Weed': 5.3739, 'A Border': 202.0719, 'A Clump': 7.7515, 'A Dead': 95.9227, 'A Pattern': 10.1405, 'A Small': 73.0521, 'A Weed': 40.6195, 'B Optimized Extra Large': 8.0036, 'B Optimized Large': 24.5894, 'B Optimized Small': 128.0287, 'C Dead': 64.911, 'C Medium Full': 64.9454, 'C Medium Half': 14.5863, 'C Weed': 13.4405, 'D Dead': 50.9319, 'D Medium': 13.177, 'D Plant 01': 4.8297, 'D Plant 02': 7.2588, 'D Weed': 32.8565, 'E Border': 307.0008, 'E Clover': 15.3025, 'E Clump Big': 9.0692, 'E Clump Tiny': 19.8514, 'E Dark': 7.6598, 'E Dead': 40.946, 'E Small': 13.6468, 'F Clover': 16.6947, 'F Clover Flower': 6.6343, 'F Clump': 4.1651, 'F Leaves': 16.7863, 'F Medium': 214.9281, 'F Tiny': 64.5329, 'Rockplain Clover Creeper': 46.8814, 'Rockplain Creeper': 29.9862, 'Rockplain Dry Plant': 4.8869, 'Rockplain Fuchsia': 3.6953, 'Rockplain Gravel': 63.662, 'Rockplain Moss Medium': 55.9163, 'Rockplain Moss Small': 29.0925, 'Rockplain Rocks': 3.151, 'Rockplain Thorns': 64.1261, 'Rockplain Wildflowers': 7.5338, 'Wasteland Branches': 11.8077, 'Wasteland Clump Bush': 1.8333, 'Wasteland Clump High': 4.0906, 'Wasteland Clump Low': 18.9405, 'Wasteland Dead': 73.1896, 'Wasteland Field': 3.5349, 'Wasteland Field Full': 15.1192, 'Wasteland Grass Medium': 11.7619, 'Wasteland Grass Small': 19.8743, 'Wasteland Gravel': 12.3978, 'Wasteland Gravel Full': 45.9476, 'Wasteland Meadow': 16.1504, 'Wasteland Meadow Flower': 85.5702, 'Wasteland Thin': 26.8409, 'Winter Branches': 3.8901, 'Winter Clumps': 14.9072, 'Winter Coniferous Bush': 0.2979, 'Winter Coniferous Pine Small': 0.2292, 'Winter Frozen Grass': 40.7856, 'Winter Frozen Grass Clump': 0.8708, 'Winter Frozen Leaves': 36.8325, 'Winter Fuchsia': 1.0141, 'Winter Grass': 32.3008, 'Winter Grass Clump': 4.0849, 'Winter Grass Wild': 7.5109, 'Winter Leaves': 31.556, 'Winter Nettle': 9.6421, 'Winter Plant': 2.9562, 'Winter Rocks': 9.7567, 'Winter Snowpile Large': 0.9625, 'Winter Snowpile Small': 7.2932}
    
    #search for all preset files
    for f in  [os.path.join(r,file) for r,d,f in os.walk(NEW) for file in f]:
        if f.endswith(".preset") and "grass_12" not in f:

            prepath = f

            biopath = f.replace(".layer00.preset",".biome")
            with open(biopath) as f:
                bi = json.load(f)

            estimated_density = new_values.get(bi["00"]["name"])
            assert estimated_density
            estimated_density *=1.01
            
            with open(prepath) as f:
                d = json.load(f)

            d["estimated_density"] = estimated_density
            with open(prepath, 'w') as f:
                json.dump(d, f, indent=4)

            bi["info"]["estimated_density"] = estimated_density
            with open(biopath, 'w') as f:
                json.dump(bi, f, indent=4)

            continue 

def batch_replace_estimated_density_in_multi_biome():

    for f in  [os.path.join(r,file) for r,d,f in os.walk(NEW) for file in f]:
        if f.endswith(".biome") and not os.path.exists(f.replace(".biome",".layer00.preset")):

            biopath = f

            with open(biopath) as f:
                bi = json.load(f)

            #gather all density from all sub layers 
            estimated_density = 0
            for k,v in bi.items():
                if k.startswith("layerlink"):
                    link = find_path(NEW, v)
                    with open(link) as f:
                        lk = json.load(f)
                        estimated_density +=lk["info"]["estimated_density"]

            bi["info"]["estimated_density"] = round(estimated_density,4)
            with open(biopath, 'w') as f:
                json.dump(bi, f, indent=4)

            continue


#Run Here
if __name__ == "__main__":
    pass