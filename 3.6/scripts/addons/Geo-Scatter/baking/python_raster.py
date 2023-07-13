

# # ooooooooo.                          .                           ooooooooo.                   .   oooo
# # `888   `Y88.                      .o8                           `888   `Y88.               .o8   `888
# #  888   .d88'  .oooo.    .oooo.o .o888oo  .ooooo.  oooo d8b       888   .d88' oooo    ooo .o888oo  888 .oo.    .ooooo.  ooo. .oo.
# #  888ooo88P'  `P  )88b  d88(  "8   888   d88' `88b `888""8P       888ooo88P'   `88.  .8'    888    888P"Y88b  d88' `88b `888P"Y88b
# #  888`88b.     .oP"888  `"Y88b.    888   888ooo888  888           888           `88..8'     888    888   888  888   888  888   888
# #  888  `88b.  d8(  888  o.  )88b   888 . 888    .o  888           888            `888'      888 .  888   888  888   888  888   888
# # o888o  o888o `Y888""8o 8""888P'   "888" `Y8bod8P' d888b         o888o            .8'       "888" o888o o888o `Y8bod8P' o888o o888o
# #                                                                              .o..P'
# #                                                                              `Y8P'


# # This is the Python version of the raster_tris compiled function 
# # This script is not used, this is just the rasterization algo but in python 
# # We did this during prototyping 

# from copy import deepcopy


# res_x=None
# res_y=None

    
# def draw_point(pixels,  y,x,  r,g,b):

#     pixels[y][x] = [r,g,b,1.0]

#     return 

# def raster_line(pixels,  y,  Lx,Lr,Lg,Lb,  Rx,Rr,Rg,Rb,):

#     #raster from left to right
#     #No line but a single point? draw point directly! 
#     #(only if point not out of bounds)

#     if Lx==Rx:
#         if Lx>=0 and Lx<res_x: 
#             draw_point(
#                 pixels, 
#                 int(y),int(Lx), 
#                 Lr,Lg,Lb
#                 ) 
#         return 
    
#     #for C++, will need const arg 

#     lr,lg,lb = Lr,Lg,Lb
#     rr,rg,rb = Rr,Rg,Rb

#     #always from left to right!
#     #may need to change direction? 
    
#     if Lx>Rx:
#         Lx,Rx = Rx,Lx
#         _r,_g,_b = lr,lg,lb
#         lr,lg,lb = rr,rg,rb
#         rr,rg,rb = _r,_g,_b
       
#     #prepare rgb points to increment and their deltas

#     r  = lr
#     g  = lg
#     b  = lb
#     dr = (rr - lr) / (Rx - Lx)
#     dg = (rg - lg) / (Rx - Lx)
#     db = (rb - lb) / (Rx - Lx)

#     #below = check if we are going out of pixel array bounds!

#     minx = int(0.5+Lx)
#     if (minx<0):
#         r-=minx*dr
#         g-=minx*dg
#         b-=minx*db
#         minx=0

#     maxx = int(0.5+Rx)
#     if (maxx>=res_x-1):
#         maxx=res_x-1

#     #draw each pixel on the line

#     for x in range(minx,maxx+1):

#         draw_point(
#             pixels, 
#             int(y),int(x), 
#             r,g,b
#             )

#         #increment rgb 

#         r += dr
#         g += dg
#         b += db

#     return 

# def rasterize_tris(pixels, tris):
        
#     #a point is an array of 5 values
#     #pt  = [x,y,r,g,b]
#     #       0 1 2 3 4 
#     #in this script l, m, h = low_point, medium_point, high_point in from Y axis

#     #a tri is an array of 3 pt
#     #tri = [[x,y,r,g,b], [x,y,r,g,b], [x,y,r,g,b]]

#     #tris array is an array of tri
#     #tris = [
#     #     [[x,y,r,g,b], [x,y,r,g,b], [x,y,r,g,b]],
#     #     [[x,y,r,g,b], [x,y,r,g,b], [x,y,r,g,b]],
#     #     [[x,y,r,g,b], [x,y,r,g,b], [x,y,r,g,b]],
#     #       ... 
#     #       ]

#     for tri in tris:

#         #sort points by y coords, from lower to higher
    
#         def sorter(array):
#             return (None, array[1])

#         l, m, h = sorted(tri, key=sorter)

#         #get Y distance from one point to another in px

#         lh_y = h[1] - l[1]  #from y low to y high
#         lm_y = m[1] - l[1]  #from y low to y mid
#         mh_y = h[1] - m[1]  #from y mid to y high

#         # skip if tris is empty 

#         if (lh_y<=0):
#             return

#         #incremented variables + delta steps

#         Plh= deepcopy(l) #point that will move on the edge lh
#         _lhX = (h[0] - l[0]) /lh_y #delta x
#         _lhR = (h[2]-l[2]) /lh_y   #delta r
#         _lhG = (h[3]-l[3]) /lh_y   #delta g
#         _lhB = (h[4]-l[4]) /lh_y   #delta b

#         if (lm_y>0): #separate our triangle in two! is there's a lower triangle?

#             Plm= deepcopy(l) #point that will move on the edge lm
#             _lmX = (m[0] - l[0]) /lm_y #delta x
#             _lmR = (m[2]-l[2]) /lm_y   #delta r
#             _lmG = (m[3]-l[3]) /lm_y   #delta g
#             _lmB = (m[4]-l[4]) /lm_y   #delta b

#             #below = crop if out of pixels array bounds

#             miny=int(0.5 + l[1])
#             maxy=int(0.5 + m[1])

#             if miny<0:

#                 Plh[0] -= _lhX*miny
#                 Plh[2] -= _lhR*miny
#                 Plh[3] -= _lhG*miny
#                 Plh[4] -= _lhB*miny

#                 Plm[0] -= _lmX*miny
#                 Plm[2] -= _lmR*miny
#                 Plm[3] -= _lmG*miny
#                 Plm[4] -= _lmB*miny

#                 miny=0

#             if maxy>=res_y: 
#                 maxy=res_y-1

#             #rasterize lower triangle 

#             for y in range(miny, maxy):
                
#                 #rasterize line on y from Plh to Plm point, with interpolated rgb values 

#                 raster_line(
#                     pixels,   
#                     y,   
#                     Plh[0],Plh[2],Plh[3],Plh[4],   
#                     Plm[0],Plm[2],Plm[3],Plm[4],
#                     )

#                 #increment the two points x location and their rgb (also interpolated)

#                 Plh[0] += _lhX
#                 Plh[2] += _lhR
#                 Plh[3] += _lhG
#                 Plh[4] += _lhB

#                 Plm[0] += _lmX
#                 Plm[2] += _lmR
#                 Plm[3] += _lmG
#                 Plm[4] += _lmB

#         #rasterize from Ymid to Yhigh

#         if (mh_y>0): #separate our triangle in two! is there's a upper triangle?

#             Pmh= deepcopy(m) #point that will move on the edge mh
#             _mhX = (h[0] - m[0]) /mh_y #delta x
#             _mhR = (h[2]-m[2]) /mh_y   #delta r
#             _mhG = (h[3]-m[3]) /mh_y   #delta g
#             _mhB = (h[4]-m[4]) /mh_y   #delta b

#             #below = crop if out of pixels array bounds

#             miny=int(0.5+m[1])
#             maxy=int(0.5+h[1])

#             if miny<0:

#                 Plh[0] -= _lhX*miny
#                 Plh[2] -= _lhR*miny
#                 Plh[3] -= _lhG*miny
#                 Plh[4] -= _lhB*miny

#                 Pmh[0] -= _mhX*miny
#                 Pmh[2] -= _mhR*miny
#                 Pmh[3] -= _mhG*miny
#                 Pmh[4] -= _mhB*miny

#                 miny=0

#             if maxy>=res_y:
#                 maxy=res_y-1

#             #rasterize upper triangle

#             for y in range(miny, maxy):

#                 #rasterize line on y from Plh to Pmh point, with interpolated rgb values 

#                 raster_line(
#                     pixels,   
#                     y,   
#                     Plh[0],Plh[2],Plh[3],Plh[4],   
#                     Pmh[0],Pmh[2],Pmh[3],Pmh[4],
#                     )

#                 #increment the two points x location and their rgb (also interpolated)

#                 Plh[0] += _lhX
#                 Plh[2] += _lhR
#                 Plh[3] += _lhG
#                 Plh[4] += _lhB

#                 Pmh[0] += _mhX 
#                 Pmh[2] += _mhR
#                 Pmh[3] += _mhG
#                 Pmh[4] += _mhB

#     return 