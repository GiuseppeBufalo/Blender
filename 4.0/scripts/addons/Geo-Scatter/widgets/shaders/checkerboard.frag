// uniform vec4 color_a;
// uniform vec4 color_b;
// uniform int size;
//
// out vec4 fragColor;

void main()
{
    vec4 a = blender_srgb_to_framebuffer_space(color_a);
    vec4 b = blender_srgb_to_framebuffer_space(color_b);
    
    fragColor = b;
    
    vec2 p = floor(gl_FragCoord.xy / size);
    float m = mod(p.x + mod(p.y, 2.0), 2.0);
    
    if(m >= 0.5)
    {
        fragColor = a;
    }
}