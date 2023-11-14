import bpy
from . registration import get_addon


decalmachine = None

def get_last_node(mat):
    if mat.use_nodes:
        tree = mat.node_tree
        output = tree.nodes.get("Material Output")
        if output:
            surf = output.inputs.get("Surface")
            if surf:
                if surf.links:
                    return surf.links[0].from_node


def lighten_color(color, amount):
    def remap(value, new_low):
        old_range = (1 - 0)
        new_range = (1 - new_low)
        return (((value - 0) * new_range) / old_range) + new_low

    return tuple(remap(c, amount) for c in color)


def adjust_bevel_shader(context, debug=False):

    debug = True
    debug = False

    m3 = context.scene.M3

    if debug:
        print("\nadjusting bevel shader")
        print("use bevel:", m3.use_bevel_shader)

    visible_objs = [obj for obj in context.visible_objects if obj.data and getattr(obj.data, 'materials', False) is not False and not any([obj.type == 'GPENCIL', obj.display_type in ['WIRE', 'BOUNDS'], obj.hide_render])]

    white_bevel = bpy.data.materials.get('white bevel')
    white_bevel_objs = []

    visible_mats = {white_bevel} if white_bevel else set()

    if debug:
        print("white bevel mat:", white_bevel)

    if debug:
        print("\nvisible objects")

    for obj in visible_objs:
        mats = [mat for mat in obj.data.materials if mat]

        if obj.data.materials and not mats:
            obj.data.materials.clear()

        if debug:
            print(obj.name, [mat.name for mat in mats])

        if m3.use_bevel_shader and not mats:
            if not white_bevel:
                if debug:
                    print(" creating new white bevel material")

                white_bevel = bpy.data.materials.new('white bevel')
                white_bevel.use_nodes = True

            if debug:
                print(" assigning white bevel material")

            obj.data.materials.append(white_bevel)
            mats.append(white_bevel)

        if obj.data.materials[0] == white_bevel:
            white_bevel_objs.append(obj)
        
        visible_mats.update(mats)


    if debug:
        print("\nvisible materials")

    for mat in visible_mats:
        if debug:
            print(mat.name)

        tree = mat.node_tree

        bevel = tree.nodes.get('Bevel')
        math = tree.nodes.get('Bevel Shader Radius Math')
        global_radius = tree.nodes.get('Bevel Shader Global Radius')
        obj_modulation = tree.nodes.get('Bevel Shader Object Radius Modulation')

        if debug:
            print(" bevel:", bevel)
            print(" math:", math)
            print(" global_radius:", global_radius)
            print(" obj_modulation:", obj_modulation)

        if not bevel:
            if debug:
                print("\n no bevel node found")

            last_node = get_last_node(mat)

            if last_node:
                if debug:
                    print("  found last node", last_node.name)

                normal_input = last_node.inputs.get('Normal')

                if normal_input and not normal_input.links:
                    if debug:
                        print("   has a normal input without links, creating bevel node")

                    bevel = tree.nodes.new('ShaderNodeBevel')
                    bevel.location.x = last_node.location.x - 250

                    y_dim = last_node.dimensions.y
                    if y_dim == 0:
                        y_dim = 660

                    bevel.location.y = last_node.location.y - y_dim + bevel.height

                    if not math:
                        if debug:
                            print("   creating multiply node")

                        math = tree.nodes.new('ShaderNodeMath')
                        math.name = "Bevel Shader Radius Math"
                        math.operation = 'MULTIPLY'

                        math.location = bevel.location
                        math.location.x = bevel.location.x - 200

                        tree.links.new(math.outputs[0], bevel.inputs[0])

                    if not global_radius:
                        if debug:
                            print("   creating global radius node")

                        global_radius = tree.nodes.new('ShaderNodeValue')
                        global_radius.name = "Bevel Shader Global Radius"
                        global_radius.label = "Global Radius"

                        global_radius.location = math.location
                        global_radius.location.x = math.location.x - 200
                        global_radius.location.y = math.location.y

                        tree.links.new(global_radius.outputs[0], math.inputs[0])

                    if not obj_modulation:
                        if debug:
                            print("   creating obj modulation node")

                        obj_modulation = tree.nodes.new('ShaderNodeAttribute')
                        obj_modulation.name = "Bevel Shader Object Radius Modulation"
                        obj_modulation.label = "Obj Radius Modulation"

                        obj_modulation.attribute_type = 'OBJECT'
                        obj_modulation.attribute_name = 'M3.bevel_shader_radius_mod'

                        obj_modulation.location = global_radius.location
                        obj_modulation.location.y = global_radius.location.y - 100

                        tree.links.new(obj_modulation.outputs[2], math.inputs[1])

                    tree.links.new(bevel.outputs[0], normal_input)

                else:
                    continue

            else:
                continue

        if m3.use_bevel_shader:
            samples = bevel.samples
            radius = global_radius.outputs[0].default_value

            if samples != m3.bevel_shader_samples:
                if debug:
                    print(" setting bevel samples to:", m3.bevel_shader_samples)

                bevel.samples = m3.bevel_shader_samples

            if radius != m3.bevel_shader_radius:
                if debug:
                    print(" setting bevel radius to:", m3.bevel_shader_radius)
                
                bevel.inputs[0].default_value = m3.bevel_shader_radius

                global_radius.outputs[0].default_value = m3.bevel_shader_radius


        else:
            if mat == white_bevel:
                if debug:
                    print(" removing white bevel material")

                bpy.data.materials.remove(mat, do_unlink=True)
                
                for obj in white_bevel_objs:
                    obj.data.materials.clear()
                    print("  clearing material slots on", obj.name)

            else:
                if bevel:
                    if debug:
                        print(" removing bevel node")

                    tree.nodes.remove(bevel)

                if math:
                    if debug:
                        print(" removing math node")

                    tree.nodes.remove(math)

                if global_radius:
                    if debug:
                        print(" removing global radius node")

                    tree.nodes.remove(global_radius)

                if obj_modulation:
                    if debug:
                        print(" removing obj modulation node")

                    tree.nodes.remove(obj_modulation)
