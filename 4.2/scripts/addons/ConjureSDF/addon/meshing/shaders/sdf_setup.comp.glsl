#version 430

layout (local_size_x = 1, local_size_y = 1, local_size_z = 1) in;


// total memory for one struct = 112
struct PrimitiveData
{
    // 16 - offset 0
    vec4 loc;
    // w is op_strength

    // 16 - offset 16
    vec4 dimension;
    // w is radius

    // 64 - offset 32
    mat4 rotscale;

    // 16 - offset 96
    vec4 parms;
    // various extra parameters
};

// Uniform block named InstanceBlock, follows std140 alignment rules
layout (std140, binding = 0) uniform PrimitiveBlock {
  PrimitiveData primitives [500];
};

uniform vec3 origin;

const uint chunk_size = 100;
const uint chunk_size2 = chunk_size*chunk_size;

layout(std430,binding=1) writeonly buffer InputField 
{
  float data[chunk_size*chunk_size*chunk_size];
};

uniform float chunk_length;
float voxel_size = chunk_length/(chunk_size-1);

uint contIndex( uint x, uint y, uint z )
{
	return chunk_size2*z + chunk_size*y + x;
}

