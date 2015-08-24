from OpenGL.GL import *
from numpy.ma import sin

import numpy

def spirala_np(num):
    velikost_centra = 50
    ostrina_meje_krakov = 1./500
    ukrivljenost_krakov = 1. / 70
    st_krakov = 5
    width=4

    pos = numpy.ndarray((num, width), dtype=numpy.float32)
    col = numpy.ndarray((num, 4), dtype=numpy.float32)
    vel = numpy.ndarray((num, width), dtype=numpy.float32)

    r = numpy.ndarray((num,), dtype=numpy.float32)
    a = numpy.ndarray((num,), dtype=numpy.float32)
    nfail=num
    idxfail=numpy.arange(num)
    while nfail:
        r[idxfail]=0.0001+numpy.random.random((nfail,))
        a[idxfail]=numpy.random.random((nfail,))*2*numpy.pi
        meja=numpy.random.random((nfail,))*10
        a2=a[idxfail]
        r2=r[idxfail]
        idxfail=numpy.where((numpy.sin(a2 * st_krakov - r2 * ukrivljenost_krakov) + 1 - r2*ostrina_meje_krakov + velikost_centra / r2)*0.5<meja)
        print idxfail[0].shape
        nfail=idxfail[0].shape[0]
        break

    pos[:,0]=r*numpy.cos(a)
    pos[:,1]=r*numpy.sin(a)
    print numpy.sum(pos,0)/num
    pos-= numpy.sum(pos,0)/num
    r[numpy.where(r<0.3)]=0.3
    pos[:,2]=(numpy.random.random_sample((num, ))-0.5)/r/10
    pos[:,3] =1.# numpy.random.random_sample((num, ))
    if 1:
        # c1=0.0095
        # c2=0.6
        c1=0.0095
        c2=0.65
    else:
        c1=0.004
        c2=0.8
    vel[:,0]=pos[:,1]/r**c2*num*c1
    vel[:,1]=-pos[:,0]/r**c2*num*c1
    vel[:,2]=0
    vel[:,3] = numpy.random.random_sample((num, ))*2

    col[:,0] = 1
    col[:,1] = 0.3
    col[:,2] = 0.1
    col[:,3] = 0.5
    return pos,col,vel


def fountain(num):
    """Initialize position, color and velocity arrays we also make Vertex
    Buffer Objects for the position and color arrays"""

    #pos, col, vel = fountain_loopy(num)
    #pos, col, vel = fountain_np(num)
    pos, col, vel = spirala_np(num)

    #create the Vertex Buffer Objects
    from OpenGL.arrays import vbo 
    pos_vbo = vbo.VBO(data=pos, usage=GL_DYNAMIC_DRAW, target=GL_ARRAY_BUFFER)
    pos_vbo.bind()
    col_vbo = vbo.VBO(data=col, usage=GL_DYNAMIC_DRAW, target=GL_ARRAY_BUFFER)
    col_vbo.bind()

    return (pos_vbo, col_vbo, vel)


