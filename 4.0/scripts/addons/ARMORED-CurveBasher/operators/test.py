import bpy


def curve_test(context):
    curve = bpy.data.curves.new("link", 'CURVE')
    spline = curve.splines.new('BEZIER')

    spline.bezier_points.add(2)
    
    p0 = spline.bezier_points[0]
    p1 = spline.bezier_points[1]
    p2 = spline.bezier_points[2]
    p0.co = (0, 0, 0)
    p1.co = (1, 1, 1)
    p2.co = (0, 2, 0)

    p0.handle_right_type = 'AUTO'
    p0.handle_left_type  = 'AUTO'

    p1.handle_right_type = 'AUTO'
    p1.handle_left_type  = 'AUTO'

    p2.handle_right_type = 'AUTO'
    p2.handle_left_type  = 'AUTO'

    obj = bpy.data.objects.new("link", curve)
    context.collection.objects.link(obj)
    context.view_layer.objects.active = obj

    return obj

class TEST_OT_black_curve(bpy.types.Operator):

    bl_idname = 'object.test_op'
    bl_label  = 'black curve test'
    bl_options = {'REGISTER', 'UNDO'}

    radius : bpy.props.FloatProperty(name='Radius', default=0.1)

    def execute(self, context):
        curve = curve_test(context)
        curve.data.bevel_depth = self.radius

        return {'FINISHED'}


def register():
    bpy.utils.register_class(TEST_OT_black_curve)
    

def unregister():
    bpy.utils.unregister_class(TEST_OT_black_curve)


if __name__ == "__main__":
    register()

    # test call
    bpy.ops.object.test_op()

