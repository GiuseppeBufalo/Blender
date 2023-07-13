


def get_loop_triangles(bm, faces=None):
    if faces:
        return [lt for lt in bm.calc_loop_triangles() if lt[0].face in faces]
    return bm.calc_loop_triangles()


def get_tri_coords_from_face(loop_triangles, f, mx=None):
    if mx:
        return [mx @ l.vert.co for lt in loop_triangles if lt[0].face == f for l in lt]
    else:
        return [l.vert.co for lt in loop_triangles if lt[0].face == f for l in lt]
