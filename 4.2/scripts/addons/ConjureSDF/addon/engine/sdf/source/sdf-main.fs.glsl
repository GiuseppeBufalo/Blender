
float RayMarch(vec3 ro, vec3 rd) 
{
    float dO = 0.; //Distane Origin
    float ds = 0;
    for(int i=0;i<steps_dist_surface_scale.x;i++)
    {
        vec3 p = ro + rd * dO;
        ds = GetDist(p); // ds is Distance Scene
        dO += ds*steps_dist_surface_scale.w;
        if(dO > steps_dist_surface_scale.y || ds < steps_dist_surface_scale.z) break;
    }
    if (ds > 0.5) discard;
    return dO;
}

vec3 GetNormal(vec3 p)
{ 
    float d = GetDist(p); // Distance
    vec2 e = vec2(.01,0); // Epsilon

    if (steps_dist_surface_scale.z < e.x)
    {
        e.x = steps_dist_surface_scale.z;
    }

    vec3 n = d - vec3(
    GetDist(p-e.xyy),  
    GetDist(p-e.yxy),
    GetDist(p-e.yyx));
   
    return normalize(n);
}

float GetLight(vec3 p, vec3 l)
{ 
    // Light (directional diffuse)
    //vec3 l = normalize(lig-p); // Light Vector
    vec3 n = GetNormal(p); // Normal Vector
   
    float dif = dot(n,l); // Diffuse light
    dif = clamp(dif,0.,1.); // Clamp so it doesnt go below 0

    // Shadows
    //float d = RayMarch(p+n*SURFACE_DIST*2., l);

    //if(d<length(lightPos-p)) dif *= .1;
 
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
    // ro = ray origin, rd = ray direction
    vec3 ro = viewpos;
    vec3 rd = vec3(0,0,-1);

    if (orthoview == 0)
    {
        // based on https://encreative.blogspot.com/2019/05/computing-ray-origin-and-direction-from.html
        ro = near_4.xyz/near_4.w;  //ray's origin
        vec3 far3 = far_4.xyz/far_4.w;
        rd = far3-ro;
        rd = normalize(rd); //ray's direction
    }
    else
    {
        // based on https://www.shadertoy.com/view/flXXWn by Envy24
        // and https://twitter.com/IY0YI 's Ernst Renderer
        vec2 uv = texcoords;
        
        vec3 f = camForward;  // forward
        vec3 u = camUp; // up

        vec3 r = cross(f, u); // right

        float aspectRatio = u_resolution.x / u_resolution.y;
        float orthographicScale = orthoScale*1.5;
        float vpWidth = orthographicScale;
        float vpHeight = vpWidth / aspectRatio;
    
        uv.x = (uv.x * vpWidth) - vpWidth * 0.5;
        uv.y = (uv.y * vpHeight) - vpHeight * 0.5;
            
        ro = ro + uv.x * r + uv.y * u;
        // push ray origin back a bit
        ro -= f*5;
        rd = f;    
    }


    float d = RayMarch(ro,rd); // Distance

    vec3 p = ro + rd * d;

    vec3 nor = GetNormal(p);
    //vec3 lig = normalize(u_lightPosition-p);
    //vec3 lig = normalize(vec3(1,1,1));
    //vec3 lig = -rd;

    //float dif = clamp( dot( nor, lig ), 0.0, 1.0 ) * calcSoftshadow( p, lig, 0.1, 100.0);
    //float dif = GetLight(p, lig);

    // .4 .7 .5 is a nice matcap color
    // vec3 color = mix(vec3(0,0,0), _AmbientColor, dif);
    // color = mix(color, vec3(1,1,1), pow(dif, 32));
   
    // depth only version, comment out normal/lighting calculations
    // d = 1-(d/100);
    // gl_FragColor = vec4(color,1.0);

    // Set the output color
    // gl_FragColor = vec4(color,1.0);



    vec2 snor = (inverse(u_viewMatrix) * vec4(nor, 0.0)).xy;
    snor = (0.5*snor)+0.5;
    fragColor = texture(matcap, snor);

    // max tracing distance has been reached
    if (d >= steps_dist_surface_scale.y)
    {
        gl_FragDepth = 1.0;
    }
    else
    {
        // depth correction for proper sorting
        d = d * dot(normalize(camForward), rd);

        float depth = depth_a + depth_b/(-d);
        depth = 0.5 + (depth * 0.5);

        gl_FragDepth = depth;
    }

}
