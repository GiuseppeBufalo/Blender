

void main() {

    uvec3 index = gl_GlobalInvocationID;
    float distance = GetDist((index*voxel_size)+origin);
    data[contIndex( index.x, index.y, index.z )] = distance;

}
