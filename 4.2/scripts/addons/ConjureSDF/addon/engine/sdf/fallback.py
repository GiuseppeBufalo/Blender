

SDF_VERTEX_SHADER = """
#version 330 core

varying vec2 texcoords; // texcoords are in the normalized [0,1] range for the viewport-filling quad part of the triangle
void main() {
        vec2 vertices[3]=vec2[3](vec2(-1,-1), vec2(3,-1), vec2(-1, 3));
        gl_Position = vec4(vertices[gl_VertexID],0,1);
        texcoords = 0.5 * gl_Position.xy + vec2(0.5);
}

"""

SDF_FRAGMENT_SHADER = """
#version 330 core
precision highp float; 
 
// Constants
#define PI 3.1415925359
#define TWO_PI 6.2831852
#define MAX_STEPS 128
#define MAX_DIST 100.
#define SURFACE_DIST .01

// Matrices available to you by renderer.py
uniform mat4 u_viewMatrix;
uniform vec3 u_cameraPosition;

uniform vec2 u_resolution;

uniform vec3 u_lightPosition;


uniform vec3 u_sdprim01;
uniform vec3 u_sdprim02;
uniform vec3 u_sdprim03;
uniform vec3 u_sdprim03_dim;

uniform mat4 u_obj_mat;



// operations
float opUnion( float d2, float d1 ) { return min(d1,d2); }

float opDifference( float d2, float d1 ) { return max(-d1,d2); }

float opIntersection( float d2, float d1 ) { return max(d1,d2); }


float opSmoothUnion( float d2, float d1, float k ) {
    float h = clamp( 0.5 + 0.5*(d2-d1)/k, 0.0, 1.0 );
    return mix( d2, d1, h ) - k*h*(1.0-h); }

float opSmoothDifference( float d2, float d1, float k ) {
    float h = clamp( 0.5 - 0.5*(d2+d1)/k, 0.0, 1.0 );
    return mix( d2, -d1, h ) + k*h*(1.0-h); }

float opSmoothIntersection( float d2, float d1, float k ) {
    float h = clamp( 0.5 - 0.5*(d2-d1)/k, 0.0, 1.0 );
    return mix( d2, d1, h ) + k*h*(1.0-h); }


// The "Chamfer" flavour makes a 45-degree chamfered edge (the diagonal of a square of size <r>):
float OpUnionChamfer(float a, float b, float r) {
	return min(min(a, b), (a - r + b)*sqrt(0.5));
}

// Intersection has to deal with what is normally the inside of the resulting object
// when using union, which we normally don't care about too much. Thus, intersection
// implementations sometimes differ from union implementations.
float OpIntersectionChamfer(float a, float b, float r) {
	return max(max(a, b), (a + r + b)*sqrt(0.5));
}

// Difference can be built from Intersection or Union:
float OpDifferenceChamfer (float a, float b, float r) {
	return OpIntersectionChamfer(a, -b, r);
}


vec3 transRot(vec3 p, vec3 loc, mat4 transrot)
{
    return (transrot * vec4(p-loc, 1.0)).xyz;
}


float sdSphere(vec3 p, float r, vec3 center)
{
    return length(p-center)-r;
}

float sdRoundBox( vec3 p, vec3 b, float r )
{
  vec3 q = abs(p) - (b-r);
  return length(max(q,0.0)) + min(max(q.x,max(q.y,q.z)),0.0) - r;
}

float GetDist(vec3 p)
{
    float planeDist = p.z;

    float sphere1 = sdSphere(p, 1, u_sdprim01);
    float sphere2 = sdSphere(p, 1, u_sdprim02);
    float result = opSmoothUnion(sphere1, sphere2, .3);

    vec3 cubepoint = transRot(p, u_sdprim03, u_obj_mat);
    float box1 = sdRoundBox(cubepoint, u_sdprim03_dim, .05);

    result = OpDifferenceChamfer(result, box1, .1);

    float d = min(result,planeDist);
 
    return d;
}

float RayMarch(vec3 ro, vec3 rd) 
{
    float dO = 0.; //Distane Origin
    for(int i=0;i<MAX_STEPS;i++)
    {
        vec3 p = ro + rd * dO;
        float ds = GetDist(p); // ds is Distance Scene
        dO += ds;
        if(dO > MAX_DIST || ds < SURFACE_DIST) break;
    }
    return dO;
}

vec3 GetNormal(vec3 p)
{ 
    float d = GetDist(p); // Distance
    vec2 e = vec2(.01,0); // Epsilon
    vec3 n = d - vec3(
    GetDist(p-e.xyy),  
    GetDist(p-e.yxy),
    GetDist(p-e.yyx));
   
    return normalize(n);
}

float GetLight(vec3 p)
{ 
    // Light (directional diffuse)
    vec3 lightPos = u_lightPosition; // Light Position
    vec3 l = normalize(lightPos-p); // Light Vector
    vec3 n = GetNormal(p); // Normal Vector
   
    float dif = dot(n,l); // Diffuse light
    dif = clamp(dif,0.,1.); // Clamp so it doesnt go below 0

    // Shadows
    float d = RayMarch(p+n*SURFACE_DIST*2., l);

    if(d<length(lightPos-p)) dif *= .1;
 
    return dif;
}

// modified from https://www.shadertoy.com/view/lsKcDD
// which is based on Sebastian Aaltonen's soft shadow improvement.
// more info here https://iquilezles.org/articles/rmshadows/
float calcSoftshadow( in vec3 ro, in vec3 rd, in float mint, in float tmax)
{
	float res = 1.0;
    float t = mint;
    float ph = 1e10; // big, such that y = 0 on the first iteration
    
    for( int i=0; i<128; i++ )
    {
		float h = GetDist(ro + rd*t );

        // use this if you are getting artifact on the first iteration, or unroll the
        // first iteration out of the loop
        //float y = (i==0) ? 0.0 : h*h/(2.0*ph); 

        float y = h*h/(2.0*ph);
        float d = sqrt(h*h-y*y);
        res = min( res, 10.0*d/max(0.0,t-y) );
        ph = h;

        
        t += h;
        
        if( res<0.0001 || t>tmax ) break;
        
    }
    res = clamp( res, 0.0, 1.0 );
    return res*res*(3.0-2.0*res);
}

 
void main()
{
    vec2 uv = (gl_FragCoord.xy-.5*u_resolution.xy)/u_resolution.y;
    vec3 ro = u_cameraPosition;
    vec3 rd = normalize(vec3(uv.x,uv.y,-1));
    rd = (u_viewMatrix * vec4(rd, 0.0)).xyz;
    float d = RayMarch(ro,rd); // Distance

    vec3 p = ro + rd * d;

    vec3 nor = GetNormal(p);
    vec3 lig = normalize(u_lightPosition-p);

    float dif = clamp( dot( nor, lig ), 0.0, 1.0 ) * calcSoftshadow( p, lig, 0.1, 100.0);
    //float dif = GetLight(p);


    vec3 color = vec3(dif);
   
    // Set the output color
    gl_FragColor = vec4(color,1.0);
}

"""