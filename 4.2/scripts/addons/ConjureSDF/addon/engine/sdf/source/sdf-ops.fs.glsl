// functions
// from https://iquilezles.org/articles/distfunctions/ unless otherwise specified
// functions by João Desager are CC BY 4.0 (unless otherwise specified)

// helper functions
// TODO : move these to their own glsl file
vec2 mirror2D(in vec2 p, in vec2 N)
{
    float proj = min(dot(p, N), 0.0);
    return p - 2.0*N*proj;
}


// modifiers
float opSolidify( float sdf, float thickness )
{
    return abs(sdf)-thickness;
}

float opSolidifyIn( float sdf, float thickness )
{
    return abs(sdf+thickness)-thickness;
}


// --- Sharp booleans

float opUnion( float d2, float d1, float k ) { return min(d1,d2); }

float opDifference( float d2, float d1, float k ) { return max(-d1,d2); }

float opIntersection( float d2, float d1, float k ) { return max(d1,d2); }

// By João Desager, based on Mercury's chamfer and carpenter groove ops
float opInset(float a, float b, float ra) {
	return max(a, min(a + ra, -b));
}


// --- Smooth booleans

float opUnionSmooth( float d2, float d1, float k ) {
    float h = clamp( 0.5 + 0.5*(d2-d1)/k, 0.0, 1.0 );
    return mix( d2, d1, h ) - k*h*(1.0-h); }

float opDifferenceSmooth( float d2, float d1, float k ) {
    float h = clamp( 0.5 - 0.5*(d2+d1)/k, 0.0, 1.0 );
    return mix( d2, -d1, h ) + k*h*(1.0-h); }

float opIntersectionSmooth( float d2, float d1, float k ) {
    float h = clamp( 0.5 - 0.5*(d2-d1)/k, 0.0, 1.0 );
    return mix( d2, d1, h ) + k*h*(1.0-h); }

// By João Desager, based on Mercury's chamfer and carpenter groove ops
float opInsetSmooth(float a, float b, float depth) {
    float r = depth;
	vec2 u = max(vec2(r + a,r - b), vec2(0));
	float subR = min(-r, max (a, -b)) + length(u);
    
    return min(a+depth, subR);
}


// --- Chamfer booleans

// by Mercury
// The "Chamfer" flavour makes a 45-degree chamfered edge (the diagonal of a square of size <r>):
float OpUnionChamfer(float a, float b, float r) {
	return min(min(a, b), (a - r + b)*sqrt(0.5));
}

// by Mercury
// Intersection has to deal with what is normally the inside of the resulting object
// when using union, which we normally don't care about too much. Thus, intersection
// implementations sometimes differ from union implementations.
float OpIntersectionChamfer(float a, float b, float r) {
	return max(max(a, b), (a + r + b)*sqrt(0.5));
}

// by Mercury
// Difference can be built from Intersection or Union:
float OpDifferenceChamfer(float a, float b, float r) {
	return OpIntersectionChamfer(a, -b, r);
}

// By João Desager, based on Mercury's chamfer and carpenter groove ops
float opInsetChamfer(in float a, in float b, in float r)
{
    float subCham = max(max(a, -b), (a + r - b)*sqrt(0.5));
    return min(a+r, subCham);
}


// --- Inverted Round booleans

// By João Desager
float opUnionIRound(in float a, in float b, in float r)
{
    // two lines with space for corner
    vec2 q = vec2(a,b);
    q = mirror2D(q, normalize(vec2(-1,1)) );
    q.y -= r;
    q.y = min(0.0, q.y);
    float ad = sign(q.x)*length(q);
    
    // inverted round corner
    vec2 s = vec2(max(a, 0.0), max(b, 0.0));
    float corn = length(s)-r ;
    
    return min(ad, corn);
}

// By João Desager
float opDifferenceIRound(in float a, in float b, in float r)
{
    // two lines with space for corner
    vec2 q = vec2(a, b);
    q = mirror2D(q, normalize(vec2(1,1)));
    q.y -= r;
    q.y = min(0.0, q.y);
    float ad = sign(q.x)*length(q);
    
    // inverted round corner
    vec2 s = vec2(min(a, 0.0), max(b, 0.0));
    float corn = -1.0*(length(s)-r) ;
    
    return max(ad, corn);    
}

// By João Desager
float opIntersectIRound(in float a, in float b, in float r)
{
    return opDifferenceIRound(a, -b, r);  
}

// By João Desager, based on Mercury's chamfer and carpenter groove ops
float opInsetIRound(in float a, in float b, in float r)
{
    float depth = r;
    // two lines with space for corner
    vec2 q = vec2(a, b);
    q = mirror2D(q, normalize(vec2(1,1)));
    q.y -= r;
    q.y = min(0.0, q.y);
    float ad = sign(q.x)*length(q);
    
    // inverted round corner
    vec2 s = vec2(min(a, 0.0), max(b, 0.0));
    float corn = -1.0*(length(s)-r) ;
    
    float subIR = max(ad, corn); 
    
    return min(a+depth, subIR); 
}


// --- transformations

vec3 transRot(vec3 p, vec3 loc, mat4 transrot)
{
    return (transrot * vec4(p-loc, 1.0)).xyz;
}


// --- space alterations


float smooth_mirror(float value, float k, float flip)
{

    // found via Inigo Quilez, from "Painting a Character with Maths" 
    // https://youtu.be/8--5LwHRhjk?t=194
    return flip*sqrt((value*value)+k);

    // TODO : add as option to smooth mirror
    // expensive, but not exponential
    // By João Desager
    // float absv = sqrt(value*value);

    // float r = k/sin(radians(45));
    // float h = r*cos(radians(45))+k;
    
    // float circy = -sqrt(r*r-value*value)+h;
    // return (absv<k) ? circy : absv; 
}


// --- extra funcs
float dot2( in vec2 v ) { return dot(v,v); }
float dot2( in vec3 v ) { return dot(v,v); }
float ndot( in vec2 a, in vec2 b ) { return a.x*b.x - a.y*b.y; }
