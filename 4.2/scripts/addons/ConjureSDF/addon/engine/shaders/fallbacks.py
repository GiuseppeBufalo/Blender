from .main import BaseShader

from ..settings import GL_TESS_EVALUATION_SHADER, GL_TESS_CONTROL_SHADER

from bgl import *

VS_FALLBACK = '''
#version 330 core
uniform mat4 ModelViewProjectionMatrix;
uniform mat4 ModelMatrix;
in vec3 Position;
in vec3 Normal;
out VS_OUT {
    vec3 positionWS;
    vec3 normalWS;
} OUT;
void main()
{
    gl_Position = ModelViewProjectionMatrix * vec4(Position, 1.0);
    vec3 positionWS = (ModelMatrix * vec4(Position, 1.0)).xyz;
    vec3 normalWS = (ModelMatrix * vec4(Normal, 0)).xyz;
    OUT.positionWS = positionWS;
    OUT.normalWS = normalWS;
}
'''

FS_FALLBACK = '''
#version 330 core
uniform mat4 CameraMatrix;
layout (location = 0) out vec4 FragColor;
in VS_OUT {
    vec3 positionWS;
    vec3 normalWS;
} IN;
void main()
{
    vec3 cameraPositionWS = CameraMatrix[3].xyz;
    vec3 eye = cameraPositionWS - IN.positionWS;
    float ndl = clamp(dot(IN.normalWS, normalize(eye)), 0.0, 1.0);
    vec3 inner = vec3(0.61, 0.54, 0.52);
    vec3 outer = vec3(0.27, 0.19, 0.18);
    vec3 highlight = vec3(0.98, 0.95, 0.92);
    FragColor = vec4(mix(outer, mix(inner, highlight, ndl * 0.25), ndl * 0.75), 1);
}
'''


class FallbackShader(BaseShader):
    """Safe fallback shader in case the user shader fails to compile"""

    def __init__(self):
        super().__init__()
        self.sources[GL_VERTEX_SHADER] = VS_FALLBACK
        self.sources[GL_FRAGMENT_SHADER] = FS_FALLBACK