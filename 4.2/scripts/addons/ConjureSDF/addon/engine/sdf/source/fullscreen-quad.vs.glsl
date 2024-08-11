#version 420 core

uniform mat4 inverse_perspectiveMatrix;

out vec4 near_4;
out vec4 far_4;

out vec2 texcoords;

void main() {
        vec2 vertices[6]=vec2[6](vec2(-1,-1), vec2(1,-1), vec2(1, 1), vec2(-1,-1), vec2(1,1), vec2(-1, 1));
        gl_Position = vec4(vertices[gl_VertexID],0,1);
        texcoords = 0.5 * gl_Position.xy + vec2(0.5);

        //compute ray's start and end as inversion of these coordinates
        //in near and far clip planes
        near_4 = inverse_perspectiveMatrix * (vec4(gl_Position.xy, -1.0, 1.0));       
        far_4 = inverse_perspectiveMatrix * (vec4(gl_Position.xy, +1.0, 1.0));
}
