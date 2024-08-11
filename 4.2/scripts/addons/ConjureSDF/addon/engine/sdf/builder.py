import bpy

import os.path

from ConjureSDF.get_path import get_path
from ...util.object import get_csdf_prims

PRIMITIVE_NON_ROUNDED = ['Sphere', 'Link', 'Coin', 'Ellipsoid', 'BiCapsule', 'Capsule', 'Torus']

PRIMS = {
    "Box": "sdBox(pos, primitives[{index}].dimension.xyz);",
    "rBox": "sdRoundBox(pos, primitives[{index}].dimension.xyz, primitives[{index}].dimension.w);",

    "Sphere": "sdSphere(pos, primitives[{index}].dimension.x);",
    
    "Cylinder": "sdCylinder(pos, primitives[{index}].dimension.z, primitives[{index}].dimension.x);",
    "rCylinder": "sdRoundedCylinder(pos, primitives[{index}].dimension.x, primitives[{index}].dimension.w, primitives[{index}].dimension.z);",

    "Link": "sdLink(pos, primitives[{index}].dimension.y, primitives[{index}].dimension.x, primitives[{index}].dimension.z);",
    "Torus": "sdTorus(pos, primitives[{index}].dimension.x, primitives[{index}].dimension.z);",

    "HexPrism": "sdHexPrism(pos, primitives[{index}].dimension.xz);",
    "rHexPrism": "sdRoundHexPrism(pos, primitives[{index}].dimension.xz, primitives[{index}].dimension.w);",

    "Coin": "sdCoin(pos, primitives[{index}].dimension.xz);",

    "CapCone": "sdCappedCone(pos, primitives[{index}].dimension.z, primitives[{index}].dimension.x, primitives[{index}].dimension.y);",
    "rCapCone": "sdRoundCappedCone(pos, primitives[{index}].dimension.z, primitives[{index}].dimension.x, primitives[{index}].dimension.y, primitives[{index}].dimension.w);",

    "Ellipsoid": "sdEllipsoidimprovedV2(pos, primitives[{index}].dimension.xyz);",

    "LongCylinder": "sdElongatedCylinder(pos, primitives[{index}].dimension.xyz);",
    "rLongCylinder": "sdRoundElongatedCylinder(pos, primitives[{index}].dimension.xyz, primitives[{index}].dimension.w);",

    "BiCapsule": "sdBiCapsule(pos, primitives[{index}].dimension.x, primitives[{index}].dimension.y, primitives[{index}].dimension.z);",
    "Capsule": "sdCapsule(pos, primitives[{index}].dimension.z, primitives[{index}].dimension.x);"
}

OPS = {
    "nUnion": "opUnion",
    "nDiff": "opDifference",
    "nInters": "opIntersection",
    "nInset": "opInset",

    "sUnion": "opUnionSmooth",
    "sDiff": "opDifferenceSmooth",
    "sInters": "opIntersectionSmooth",
    "sInset": "opInsetSmooth",

    "cUnion": "OpUnionChamfer",
    "cDiff": "OpDifferenceChamfer",
    "cInters": "OpIntersectionChamfer",
    "cInset": "opInsetChamfer",

    "irUnion": "opUnionIRound",
    "irDiff": "opDifferenceIRound",
    "irInters": "opIntersectIRound",
    "irInset": "opInsetIRound"
}

MODS = {
    "solidify": "{prim} = opSolidifyIn( {prim}, primitives[{index}].parms.x );",
}

def get_prim_instruction(csdfData, prim_start, prim_name, idx):
    primtype = csdfData.primitive_type
    if csdfData.is_rounded:
        if primtype not in PRIMITIVE_NON_ROUNDED:
            primtype = "r" + primtype



    prim_string = PRIMS[primtype]

    prim_string = prim_start+prim_string

    # if primtype in'rBox':
    #     prim_string = prim_string.format(name=obj.name, index=idx)

    prim_string = prim_string.format(name=prim_name, index=idx)
    
    return prim_string



def generate_scene(depsgraph, meshing=False):

    # -- SCENE BUILDING
    scene = depsgraph.scene

    # get list of SDF objects
    root = scene.objects["CSDF Root"]
    root_data = root.csdfData
    sdf_objs = get_csdf_prims(scene)


    scene_string = """"""
 

    scene_bounds = """
// bounding volume optimization
    vec3 b_pos = p - u_bounds_pos;
    float dB = sdSphere( b_pos, u_bounds_radius);
    if( dB>1.0 ) return 1.0;
    """


    scene_start = """
float GetDist(vec3 p)
{
    //float planeDist = p.z;

    vec3 p_nomirror = p;

    vec3 pos = vec3(0,0,0);

    float result = 0.0;

    """

    scene_mirror_smooth = """

    {axis} = smooth_mirror({axis}, mirror_smoothing_strength, {flip});

"""
    scene_mirror_sharp = """

    {axis} = {flip}*abs({axis});
"""

    scene_end = """

    //float d = min(result,planeDist);

    return result;
}
    """

    if (len(sdf_objs) == 1) or meshing:
        scene_bounds = """"""

    scene_mirror = """"""

    if root_data.mirror_smooth:
        scene_mirror_axis = scene_mirror_smooth
    else:
        scene_mirror_axis = scene_mirror_sharp

    mirror_flip_dirs = ["1.0", "1.0", "1.0"]
    mirror_axis_dirs = ["p.x", "p.y", "p.z"]

    for idx, dir in enumerate(mirror_axis_dirs):
        if root_data.mirror_world[idx]:
            if root_data.mirror_flips[idx]:
                mirror_flip_dirs[idx] = "-1.0"
            scene_mirror += scene_mirror_axis.format(axis=dir, flip=mirror_flip_dirs[idx])



    scene_string = generate_scene_source(depsgraph, meshing=False)

    scene_string = scene_start + scene_mirror + scene_bounds + scene_string + scene_end

    

    

    return scene_string
    # return scene_distance


def generate_scene_source(depsgraph, meshing=False):

    scene = depsgraph.scene
    root = scene.objects["CSDF Root"]

    # -- SCENE BUILDING

    scene_string = """"""

    transform_string = "pos = transRot({wpos}, primitives[{index}].loc.xyz, primitives[{index}].rotscale);"
    op_string = "{result} = {optype}({prevprim}, {prim}, primitives[{index}].loc.w);"

    global_sdf_list = get_csdf_prims(scene)

    csdf_scene_nodes = scene.CSDF_SceneNodes

    # if no sdf prims, just return a large distance as the result
    if len(csdf_scene_nodes) == 1:
        return """result=999999;"""

    root_node = csdf_scene_nodes[0]
    top_level_nodes = [csdf_scene_nodes[child.idx] for child in root_node.childIndices]
    top_level_nodes = [node for node in top_level_nodes if node.obj.csdfData.show_viewport]

    instruction_list, resultname = generate_scene_recursive(top_level_nodes, csdf_scene_nodes, global_sdf_list, transform_string, op_string, -1)
    instruction_list.append("result = "+resultname+";")

    scene_string = scene_string.join(instruction_list)

    return scene_string


def generate_scene_recursive(parent_nodes, csdf_scene_nodes, global_sdf_list, transform_string, op_string, parent_idx):

    instructions_list = []
    prev_local_leaf_index = -1
    prim_name = None

    for node in parent_nodes:
        sdf_obj = node.obj
        csdfData = sdf_obj.csdfData

        idx = global_sdf_list.index(sdf_obj)

        world_pos = "p"
        if csdfData.ignore_mirror:
            world_pos = "p_nomirror"
        
        instructions_list += transform_string.format(index=idx, wpos=world_pos)

        prim_start = "float {name} = "
        primprefix = "sdprim"
        prim_name = primprefix+str(idx)

        instructions_list += get_prim_instruction(csdfData, prim_start, prim_name, idx)

        if csdfData.solidify:
            solidify_string = MODS['solidify']
            instructions_list += solidify_string.format(prim=prim_name, index=idx)

        if node.childCount:
            child_nodes = [csdf_scene_nodes[childidx.idx] for childidx in node.childIndices]
            child_nodes = [node for node in child_nodes if node.obj.csdfData.show_viewport]

            instructions_children, _ = generate_scene_recursive(child_nodes, csdf_scene_nodes, global_sdf_list, transform_string, op_string, idx)
            instructions_list += instructions_children

        optype = OPS[csdfData.operation_blend+csdfData.operation_type]

        if parent_idx >= 0:
            instructions_list += op_string.format(optype=optype, prevprim=primprefix+str(parent_idx), prim=prim_name, result=primprefix+str(parent_idx), index=idx)
        elif prev_local_leaf_index >= 0:
            instructions_list += op_string.format(optype=optype, prevprim=primprefix+str(prev_local_leaf_index), prim=prim_name, result=prim_name, index=idx)

        prev_local_leaf_index = idx

    return instructions_list, prim_name



def build_shaders(scene):

    # get path to addon
    addon_relative_path = os.path.join('addon', 'engine', 'sdf', 'source')
    addon_path = get_path()

    # get path to shader source files
    src_folder = os.path.join(addon_path, addon_relative_path)


    # read source files
    template_src_files = (
        "fullscreen-quad.vs.glsl",
        "sdf-setup.fs.glsl",
        "sdf-ops.fs.glsl",
        "sdf-prims.fs.glsl",
        "sdf-main.fs.glsl",
        "ubo_test.fs.glsl"
    )

    sources = []

    for template in template_src_files:
        src_file = os.path.join(src_folder, template)
        with open(src_file) as f:
            sources.append(f.read())

    
    vs_shader = sources[0]

    # concatenate into string, using f"string" is the fastest
    fs_shader = f"{sources[1]}{sources[2]}{sources[3]}{scene}{sources[4]}"

    # fs_shader = sources[5]

    return vs_shader, fs_shader
