#version 420 core
precision highp float; 

// uniform vec2 u_resolution;

out vec4 fragColor;

// total size is 32
struct testData
{
    // 16 - offset 0
    vec3 test3;

    float padding;

    // 4 - offset 16
    float test1;  

    // needed when used in a UBO?
    //https://community.khronos.org/t/sending-an-array-of-structs-to-shader-via-an-uniform-buffer-object/75092 
    // vec3 padding; 
};

// Uniform block, follows std140 alignment rules
layout (std140, binding = 0) uniform PrimitiveBlock {
  testData primitives [2];
};

void main()
{
    // vec2 uv = (gl_FragCoord.xy-.5*u_resolution.xy)/u_resolution.x;

    float test_result = primitives[0].test3.x;
    vec2 test_result2 = vec2(primitives[1].test3.x, primitives[1].test3.y);

    fragColor = vec4(test_result, test_result2, primitives[1].test1);
}
