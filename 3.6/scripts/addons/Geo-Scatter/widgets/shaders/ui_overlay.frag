uniform float darken;
out vec4 fragColor;

void main()
{
    vec4 a = blender_srgb_to_framebuffer_space(vec4(0.0, 0.0, 0.0, 1.0));
    vec4 b = blender_srgb_to_framebuffer_space(vec4(0.0, 0.0, 0.0, darken));
    
    // pattern
    // 1 0 0
    // 0 0 1
    // 0 1 0
    
    float x = mod(floor(gl_FragCoord.x), 3);
    float y = mod(floor(gl_FragCoord.y), 3);
    
    fragColor = b;
    
    if(x == 0 && y == 2)
    {
        fragColor = a;
    }
    else if(x == 1 && y == 0)
    {
        fragColor = a;
    }
    else if(x == 2 && y == 1)
    {
        fragColor = a;
    }
}