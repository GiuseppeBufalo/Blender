
def loop_index_update(bm, debug=False):

    lidx = 0
    for f in bm.faces:
        if debug:
            print(f)
        for l in f.loops:
            l.index = lidx
            lidx += 1
            if debug:
                print(" •", l)
