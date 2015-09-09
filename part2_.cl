float my_powr(float x,__global float* powers){
    return powers[(*(int *)&x)>>5];//veliko prepocasi!
}
__kernel void init_powers(__global float* powers){
    uint gid = get_global_id(0);
    uint n = get_global_size(0);
    uint y=(gid<<5)+16;
    float x=*(float*)&y;
    powers[gid]=powr(x,-1.5);
}

__kernel void part2(__global float4* pos, __global float4* vel, float dt)
{
    //get our index in the array
    uint gid = get_global_id(0);
    //uint lid = get_local_id(0);
    uint n = get_global_size(0);
    //uint nl = get_local_size(0);//work group size
    //uint wgs = n/nl;
    float G=1;
    float eps=1e-5;
    float3 v=vel[gid].xyz;
    float3 p=pos[gid].xyz;
    for(uint i=0;i<n;i+=1){
        float3 p2=pos[i].xyz;
        float3 d=p2-p;
        float m=vel[i].w;
        //float power=native_powr(dot(d,d)+eps,-1.5f);
        float power=native_rsqrt(dot(d,d)+eps);
        power=power*power*power;
        //float power=my_powr(dot(d,d)+eps,powers);
        v+=G*m*dt*power*d;//native_powr(dot(d,d)+eps,-1.5f)
    }
    pos[gid].xyz+=v*dt;
    vel[gid].xyz=v;
}
