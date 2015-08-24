#from OpenGL.GL import GL_ARRAY_BUFFER, GL_DYNAMIC_DRAW, glFlush
from OpenGL.GL import *
from OpenGL.GLU import *


import pyopencl as cl
import sys

import numpy
import timing

timings = timing.Timing()
class Part2(object):
    def __init__(self, num, dt, *args, **kwargs):
        self.clinit()
        self.loadProgram("part2_.cl")

        self.num = num
        self.dt = numpy.float32(dt)

        self.timings = timings



    def loadData(self, pos_vbo, col_vbo, vel):
        #import pyopencl as cl
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
        


    @timings
    def execute(self, sub_intervals):
        cl.enqueue_acquire_gl_objects(self.queue, self.gl_objects)
        mf=cl.mem_flags

        global_size = (self.num,)
        local_size = None#(2**9,)

        kernelargs = (self.pos_cl,
                      self.vel_cl,
                      #cl.LocalMemory(1024*3*4),
                      #cl.Buffer(self.ctx, mf.READ_ONLY, size=self.vel_cl.size),
                      self.dt)

        for i in xrange(0, sub_intervals):
            self.program.part2(self.queue, global_size, local_size, *(kernelargs))

        cl.enqueue_release_gl_objects(self.queue, self.gl_objects)
        self.queue.finish()
 

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
        glPointSize(2)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

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
     

