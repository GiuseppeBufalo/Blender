from mathutils import Vector, Matrix


def vector_sum(vectors):
    return sum(vectors, Vector())


def flatten_matrix(mx):
    dimension = len(mx)
    return [mx[j][i] for i in range(dimension) for j in range(dimension)]


def get_sca_matrix(vector):
    scale_mx = Matrix()
    for i in range(3):
        scale_mx[i][i] = vector[i]
    return scale_mx


def get_rot_matrix(quaternion):
    return quaternion.to_matrix().to_4x4()


def get_loc_matrix(vector):
    return Matrix.Translation(vector)


def coords_to_center(coordinates):
    center = sum((Vector(b) for b in coordinates), Vector())
    center /= len(coordinates)
    return center


def coords_to_center_2d(coordinates):
    center = sum((Vector(b) for b in coordinates), Vector((0,0)))
    center /= len(coordinates)
    return center


def coords_to_bounds(coordinates):
    x =[c[0] for c in coordinates] 
    y =[c[1] for c in coordinates]  
    z =[c[2] for c in coordinates] 
    
    x_min = min(x)
    x_max = max(x)
    y_min = min(y)
    y_max = max(y)
    z_min = min(z)
    z_max = max(z)

    # array of bounding box vectors.
    # should match object.bound_box order
    return [
    Vector((x_min,y_min,z_min)),
    Vector((x_min,y_min,z_max)),
    Vector((x_min,y_max,z_max)),        
    Vector((x_min,y_max,z_min)),

    Vector((x_max,y_min,z_min)),
    Vector((x_max,y_min,z_max)),
    Vector((x_max,y_max,z_max)),
    Vector((x_max,y_max,z_min))]


def uniform_boundary_box(coordinates):
    x =[c[0] for c in coordinates] 
    y =[c[1] for c in coordinates]  
    z =[c[2] for c in coordinates] 
    
    x_min = min(x)
    x_max = max(x)
    y_min = min(y)
    y_max = max(y)
    z_min = min(z)
    z_max = max(z)

    w = abs(x_max - x_min)
    l = abs(y_max - y_min)
    h = abs(z_max - z_min)
    c = coords_to_center(coordinates)
    d = max([w, l, h]) * .5

    return [
    Vector((-d, -d, -d)),
    Vector((-d, -d,  d)),
    Vector((-d,  d,  d)),        
    Vector((-d,  d, -d)),

    Vector((d, -d, -d)),
    Vector((d, -d,  d)),
    Vector((d,  d,  d)),
    Vector((d,  d, -d))]


def dimensions(coordinates):
    x =[c[0] for c in coordinates] 
    y =[c[1] for c in coordinates]  
    z =[c[2] for c in coordinates] 
    
    x_min = min(x)
    x_max = max(x)
    y_min = min(y)
    y_max = max(y)
    z_min = min(z)
    z_max = max(z)
    
    minimum = Vector((x_min, y_min, z_min))
    maximum = Vector((x_max, y_max, z_max))
    dimensions = maximum - minimum
    
    return dimensions


def dimensions_2d(coordinates):
    x =[c[0] for c in coordinates]
    y =[c[1] for c in coordinates]
    
    x_min = min(x)
    x_max = max(x)
    y_min = min(y)
    y_max = max(y)
    
    minimum = Vector((x_min, y_min))
    maximum = Vector((x_max, y_max))
    dimensions = maximum - minimum
    
    return dimensions
