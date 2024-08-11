#version 420 core
precision highp float; 
 
// Constants
#define PI 3.1415925359
#define TWO_PI 6.2831852

// obsolute normally
#define MAX_STEPS 100
#define MAX_DIST 500.
#define SURFACE_DIST .01

// maximum raymarching steps, maximum raymarching distance, and smallest surface distance to stop on
uniform vec4 steps_dist_surface_scale;

out vec4 fragColor;

// Matrices available to you by renderer.py
uniform mat4 u_viewMatrix;
uniform mat4 ProjectionMatrix;

uniform vec3 _AmbientColor;

uniform vec2 u_resolution;

// uniform vec3 u_lightPosition;

uniform vec3 u_bounds_pos;
uniform float u_bounds_radius;

in vec2 texcoords;

uniform sampler2D matcap;

// for depth calculation
uniform float depth_a;
uniform float depth_b;

in vec4 near_4;    //for computing rays in fragment shader
in vec4 far_4;

uniform vec3 ray_origin;

// for orthographic rendering

uniform int orthoview;
uniform vec3 viewpos;
uniform float orthoScale;

uniform vec3 camForward;
uniform vec3 camUp;

// for mirroring
uniform float mirror_smoothing_strength;



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


