uniform mat4 transform;
uniform mat4 projection;

uniform float size;

in vec3 vert;


void main() {
    gl_Position = projection * transform * vec4(vert, 1.0);
}
