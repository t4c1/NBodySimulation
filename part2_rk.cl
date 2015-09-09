__kernel void part2(__global float4* pos, __global float4* vel, float dt)
{
    uint gid = get_global_id(0);
    uint n = get_global_size(0);

    float G=1;
    float eps=1e-5;
    float3 v=vel[gid].xyz;
    float3 p_orig=pos[gid].xyz;
    float rkf[4]={1,2,2,1};
    float rkd[4]={0,0.5,0.5,1};
    float3 rkk[4]={v,v,v,v};
    for(uint j=0;j<4;j++){
        float3 p= p_orig+rkd[j]*rkk[j-1];
        for(uint i=0;i<n;i+=1){
            float3 p2=pos[i].xyz;
            float3 d=p2-p;
            float m=vel[i].w;
            float power=native_rsqrt(dot(d,d)+eps);
            power=power*power*power;
            rkk[j]+=G*m*power*d*dt;
        }
    }
    v=(rkk[0]*rkf[0]+rkk[1]*rkf[1]+rkk[2]*rkf[2]+rkk[3]*rkf[3])/6;
    //v=rkk[0];
    pos[gid].xyz+=v*dt;
    vel[gid].xyz=v.xyz;
}
