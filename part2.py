#from OpenGL.GL import GL_ARRAY_BUFFER, GL_DYNAMIC_DRAW, glFlush
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.raw.GL.VERSION.GL_1_5 import GL_DYNAMIC_DRAW, GL_ARRAY_BUFFER

import pyopencl as cl
import sys

import timing
tim=timing.Timing()

import numpy
class Part2(object):
    def __init__(self, num, dt, *args, **kwargs):
        self.clinit()
        self.loadProgram("part2_rk.cl")
        #self.init_powers()

        self.num = num
        self.dt = numpy.float32(dt)
        self.tim=tim

    def init_powers(self):
        mf = cl.mem_flags
        self.powers_buf = cl.Buffer(self.ctx, mf.WRITE_ONLY,2**30)
        self.program.init_powers(self.queue, (2 ** 26,), None, self.powers_buf)
        #cl.enqueue_copy(self.queue,self.powers,self.powers_buf)

    def loadData(self, pos_vbo, col_vbo, vel):
        mf = cl.mem_flags
        self.pos_vbo = pos_vbo
        self.col_vbo = col_vbo

        self.pos = pos_vbo.data
        self.col = col_vbo.data
        self.vel = vel

        #Setup vertex buffer objects and share them with OpenCL as GLBuffers
        self.pos_vbo.bind()
        self.pos_cl = cl.GLBuffer(self.ctx, mf.READ_WRITE, int(self.pos_vbo.buffers[0]))
        self.col_vbo.bind()
        self.col_cl = cl.GLBuffer(self.ctx, mf.READ_WRITE, int(self.col_vbo.buffers[0]))

        #pure OpenCL arrays
        self.vel_cl = cl.Buffer(self.ctx, mf.READ_WRITE | mf.COPY_HOST_PTR, hostbuf=vel)
        # self.pos_gen_cl = cl.Buffer(self.ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=self.pos)
        # self.vel_gen_cl = cl.Buffer(self.ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=self.vel)
        self.queue.finish()

        # set up the list of GL objects to share with opencl
        self.gl_objects = [self.pos_cl, self.col_cl]

    @tim
    def execute(self, sub_intervals):
        cl.enqueue_acquire_gl_objects(self.queue, self.gl_objects)
        mf=cl.mem_flags

        global_size = (self.num,)
        local_size = None#(2**9,)

        kernelargs = (self.pos_cl,self.vel_cl,
                      #cl.LocalMemory(1024*3*4),
                      #cl.Buffer(self.ctx, mf.READ_ONLY, size=self.vel_cl.size),
                      self.dt)

        for i in xrange(0, sub_intervals):
            self.program.part2(self.queue, global_size, local_size, *(kernelargs))

        cl.enqueue_release_gl_objects(self.queue, self.gl_objects)
        #self.queue.finish()
 

    def clinit(self):
        plats = cl.get_platforms()
        from pyopencl.tools import get_gl_sharing_context_properties
        import sys 
        if sys.platform == "darwin":
            self.ctx = cl.Context(properties=get_gl_sharing_context_properties(),
                             devices=[])
        else:
            self.ctx = cl.Context(properties=[
                (cl.context_properties.PLATFORM, plats[0])]
                + get_gl_sharing_context_properties(), devices=None)

        self.queue = cl.CommandQueue(self.ctx)

    def loadProgram(self, filename):
        #read in the OpenCL source file as a string
        f = open(filename, 'r')
        fstr = "".join(f.readlines())
        #print fstr
        #create the program
        self.program = cl.Program(self.ctx, fstr).build()


    def render(self):
        
        glEnable(GL_POINT_SMOOTH)
        glPointSize(3)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)

        #setup the VBOs
        self.col_vbo.bind()
        glColorPointer(4, GL_FLOAT, 0, None)#self.col_vbo)
        #
        self.pos_vbo.bind()
        glVertexPointer(4, GL_FLOAT, 0, None)#self.pos_vbo)

        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_COLOR_ARRAY)
        #draw the VBOs
        glDrawArrays(GL_POINTS, 0, self.num)

        glDisableClientState(GL_COLOR_ARRAY)
        glDisableClientState(GL_VERTEX_ARRAY)

        glDisable(GL_BLEND)

    @classmethod
    def init_np(self,num,collision=False):
        velikost_centra = 50
        ostrina_meje_krakov = 1./500
        ukrivljenost_krakov = 1. / 70
        st_krakov = 5
        width=4

        pos = numpy.ndarray((num, width), dtype=numpy.float32)
        col = numpy.ndarray((num, 4), dtype=numpy.float32)
        vel = numpy.ndarray((num, width), dtype=numpy.float32)

        r = numpy.ndarray((num,), dtype=numpy.float32) #radij
        a = numpy.ndarray((num,), dtype=numpy.float32) #kot
        nfail=num
        idxfail=numpy.arange(num)
        r[idxfail]=0.0001+numpy.random.random((nfail,))
        a[idxfail]=numpy.random.random((nfail,))*2*numpy.pi

        pos[:,0]=r*numpy.cos(a)
        pos[:,1]=r*numpy.sin(a)
        print numpy.sum(pos,0)/num
        pos-= numpy.sum(pos,0)/num
        r[numpy.where(r<0.3)]=0.3
        pos[:,2]=(numpy.random.random_sample((num, ))-0.5)/r/10
        pos[:,3] =1.# numpy.random.random_sample((num, ))
        if 0:
            # c1=0.0095
            # c2=0.6
            c1=0.008
            c2=0.65
        else:
            c1=0.005
            c2=0.8
        vel[:,0]=pos[:,1]/r**c2*num*c1
        vel[:,1]=-pos[:,0]/r**c2*num*c1
        vel[:,2]=0
        vel[:,3] = numpy.random.random_sample((num, ))*2

        col[:,0] = 0.3
        col[:,1] = 0.1
        col[:,2] = 0.03

        col[:,3] = 1
        if collision:
            pos[:num/2,0]+=3
        return pos,col,vel

    @classmethod
    def init_cl(self,num):
        width=4
        pos = numpy.ndarray((num, width), dtype=numpy.float32)
        col = numpy.ndarray((num, 4), dtype=numpy.float32)
        vel = numpy.ndarray((num, width), dtype=numpy.float32)
        ctx=cl.create_some_context()
        queue=cl.CommandQueue(ctx)
        prog=cl.Program(ctx,open("init.cl").read()).build()
        prog2=cl.Program(ctx,open("part2_.cl").read()).build()
        mf=cl.mem_flags
        pos_buf=cl.Buffer(ctx, mf.READ_WRITE | mf.COPY_HOST_PTR, hostbuf=pos)
        vel_buf=cl.Buffer(ctx, mf.READ_WRITE | mf.COPY_HOST_PTR, hostbuf=pos)

        # pos[:,0:2]=0

        # vel[:,0]=0
        # vel[:,1]=0
        # vel[:,2]=0
        vel[:,3] = numpy.random.random_sample((num, ))*2

        col[:,0] = 1
        col[:,1] = 0.3
        col[:,2] = 0.1
        col[:,3] = vel[:,3]/2

        prog.init(queue,(num,),None,pos_buf,vel_buf)
        cl.enqueue_copy(queue, pos, pos_buf)
        #prog2.part2(queue,(num,),None,pos_buf,vel_buf,numpy.float32(1./2000))
        cl.enqueue_copy(queue, vel, vel_buf)
        queue.finish()
        #vel[:,0:3]=numpy.cross(vel[:,0:3],[0,0,1])
        return pos,col,vel

    @classmethod
    def initial_pos(self,num):
        """Initialize position, color and velocity arrays we also make Vertex
        Buffer Objects for the position and color arrays"""

        pos, col, vel = self.init_np(num)
        print pos
        print vel

        #create the Vertex Buffer Objects
        from OpenGL.arrays import vbo
        pos_vbo = vbo.VBO(data=pos, usage=GL_DYNAMIC_DRAW, target=GL_ARRAY_BUFFER)
        pos_vbo.bind()
        col_vbo = vbo.VBO(data=col, usage=GL_DYNAMIC_DRAW, target=GL_ARRAY_BUFFER)
        col_vbo.bind()

        return (pos_vbo, col_vbo, vel)