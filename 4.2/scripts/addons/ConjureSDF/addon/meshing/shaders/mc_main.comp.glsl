
// heavily based on https://github.com/Germanunkol/MarchingCubesComputeShader/tree/master


uint contIndex( uint x, uint y, uint z )
{
	return chunk_size2*z + chunk_size*y + x;
}

vec3 createVert( vec3 p0, vec3 p1, float d0, float d1 )
{
	float diff = d1-d0;
	if( abs(diff) > 1e-9 )
		return (p1-p0)*(0.0-d0)/diff + p0;
	else
		return (p0 + p1)*0.5;
}

void createVerts( vec3 voxel_index, inout vec3 pos[12], float vox_data[8]) {
	
	// All corner points of the current cube
	float x = voxel_index.x*voxel_size;
	float y = voxel_index.y*voxel_size;
	float z = voxel_index.z*voxel_size;
	vec3 c0 = vec3( x, y, z);
	vec3 c1 = vec3( x+voxel_size, y, z);
	vec3 c2 = vec3( x+voxel_size, y+voxel_size, z);
	vec3 c3 = vec3( x, y+voxel_size, z);
	vec3 c4 = vec3( x, y, z+voxel_size );
	vec3 c5 = vec3( x+voxel_size, y, z+voxel_size );
	vec3 c6 = vec3( x+voxel_size, y+voxel_size, z+voxel_size );
	vec3 c7 = vec3( x, y+voxel_size, z+voxel_size );

	// Find the 12 edge vertices by interpolating between the corner points,
	// depending on the values of the field at those corner points:
	pos[0] = createVert( c0, c1, vox_data[0], vox_data[1] );
	pos[1] = createVert( c1, c2, vox_data[1], vox_data[2] );
	pos[2] = createVert( c2, c3, vox_data[2], vox_data[3] );
	pos[3] = createVert( c3, c0, vox_data[3], vox_data[0] );

	pos[4] = createVert( c4, c5, vox_data[4], vox_data[5] );
	pos[5] = createVert( c5, c6, vox_data[5], vox_data[6] );
	pos[6] = createVert( c6, c7, vox_data[6], vox_data[7] );
	pos[7] = createVert( c7, c4, vox_data[7], vox_data[4] );
	
	pos[8] = createVert( c0, c4, vox_data[0], vox_data[4] );
	pos[9] = createVert( c1, c5, vox_data[1], vox_data[5] );
	pos[10] = createVert( c2, c6, vox_data[2], vox_data[6] );
	pos[11] = createVert( c3, c7, vox_data[3], vox_data[7] );

}
                   
void main() {

	// Make sure this is not a border cell (otherwise neighbor lookup in the next step would fail):
	if( gl_GlobalInvocationID.x >= chunk_size-1 ||
			gl_GlobalInvocationID.y >= chunk_size-1 ||
			gl_GlobalInvocationID.z >= chunk_size-1 )
			return;

	uvec3 index = gl_GlobalInvocationID;

	// Retrieve all necessary data from neighboring cells:
	float vox_data[8];
	vox_data[0] = data[ contIndex( index.x, index.y, index.z ) ];
	vox_data[1] = data[ contIndex( index.x+1, index.y, index.z ) ];
	vox_data[2] = data[ contIndex( index.x+1, index.y+1, index.z ) ];
	vox_data[3] = data[ contIndex( index.x, index.y+1, index.z ) ];

	vox_data[4] = data[ contIndex( index.x, index.y, index.z+1 ) ];
	vox_data[5] = data[ contIndex( index.x+1, index.y, index.z+1 ) ];
	vox_data[6] = data[ contIndex( index.x+1, index.y+1, index.z+1 ) ];
	vox_data[7] = data[ contIndex( index.x, index.y+1, index.z+1 ) ];



	// Turn this information into a triangle list index:
	int triangleTypeIndex = 0;
	for( int i = 0; i < 8; i++ )
		if( vox_data[i] > 0.0 )
			triangleTypeIndex |= 1 << i;


	// Set up all neighboring vertices:
	vec3 verts[12];
	for( int i = 0; i < 12; i++ ) {
		verts[i] = vec3(0,0,0);
	}
	// fills verts with position info
	createVerts(gl_GlobalInvocationID, verts, vox_data);


	int tri_vert_indices[15] = tConnectionTable[triangleTypeIndex];
	for( int i = 0; i < 15; i++ )
	{
		uvec3 index = gl_GlobalInvocationID;
		uint targetVertIndex = contIndex(index.x, index.y, index.z)*15 + i;
		if( tri_vert_indices[i] > -1 )
		{
			vertices[targetVertIndex].pos = verts[tri_vert_indices[i]];
			vertices[targetVertIndex].real = 1.0;
		} else {
			vertices[targetVertIndex].pos = vec3(0,0,0);
			vertices[targetVertIndex].real = 0.0;
		}
	}

}
