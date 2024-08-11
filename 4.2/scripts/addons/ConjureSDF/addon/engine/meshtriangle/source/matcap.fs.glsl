#version 330 core

// Matrices available to you by micro.py
uniform mat4 u_viewMatrix;
uniform mat4 ViewMatrix;
uniform mat4 ProjectionMatrix;
uniform mat4 CameraMatrix; // Inverted ViewMatrix

uniform mat4 ModelMatrix;
uniform mat4 ModelViewMatrix;
uniform mat4 ModelViewProjectionMatrix;

// Lighting information provided by micro.py
uniform vec4 _MainLightDirection;

uniform sampler2D matcap;

layout (location = 0) out vec4 FragColor;

in VS_OUT {
    vec3 positionWS;
    vec3 normalWS;
} IN;

void main()
{
    vec2 snor = (inverse(u_viewMatrix) * vec4(normalize(IN.normalWS), 0.0)).xy;
    snor = (0.5*snor)+0.5;
    float darken = 0.4;
    FragColor = vec4(darken,darken,darken, 1.0) * texture(matcap, snor);
}
