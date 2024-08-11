// primitives
// from https://iquilezles.org/articles/distfunctions/ unless otherwise specified
// SDFs by João Desager are CC BY 4.0 (unless otherwise specified)

float sdSphere(vec3 p, float r)
{
    return length(p)-r;
}

float sdRoundBox( vec3 p, vec3 b, float r )
{
  vec3 q = abs(p) - (b-r);
  return length(max(q,0.0)) + min(max(q.x,max(q.y,q.z)),0.0) - r;
}

float sdBox( vec3 p, vec3 b )
{
  vec3 q = abs(p) - b;
  return length(max(q,0.0)) + min(max(q.x,max(q.y,q.z)),0.0);
}

float sdCylinder( vec3 p, float h, float r )
{
  vec2 d = vec2( length(p.xy)-r, abs(p.z) - h );
  return min(max(d.x,d.y),0.0) + length(max(d,0.0));
}

float sdRoundedCylinder( vec3 p, float ra, float rb, float h )
{
  return sdCylinder( p, h-rb, ra-rb )-rb;
}

float sdLink( vec3 p, float le, float r1, float r2 )
{
  vec3 q = vec3( p.x, max(abs(p.y)-le,0.0), p.z );
  return length(vec2(length(q.xy)-r1,q.z)) - r2;
}

float sdTorus( vec3 p, float R, float r )
{
  vec2 q = vec2(length(p.xy)-R,p.z);
  return length(q)-r;
}


float sdHexPrism( vec3 p, vec2 h )
{
  const vec3 k = vec3(-0.8660254, 0.5, 0.57735);
  p = abs(p);
  p.xy -= 2.0*min(dot(k.xy, p.xy), 0.0)*k.xy;
  vec2 d = vec2(
       length(p.xy-vec2(clamp(p.x,-k.z*h.x,k.z*h.x), h.x))*sign(p.y-h.x),
       p.z-h.y );
  return min(max(d.x,d.y),0.0) + length(max(d,0.0));
}

float sdRoundHexPrism( vec3 p, vec2 h, float r )
{
  h = h-r;
  return sdHexPrism(p, h) - r;
}

// By João Desager
float sdCoin( vec3 p, vec2 h)
{
  vec2 d = vec2(max(0.0, length(p.xy)-(h.x-h.y)), p.z);
  return length(d)-h.y;
}


float sdCappedCone( vec3 p, float h, float r1, float r2 )
{
  vec2 q = vec2( length(p.xy), p.z );
  vec2 k1 = vec2(r2,h);
  vec2 k2 = vec2(r2-r1,2.0*h);
  vec2 ca = vec2(q.x-min(q.x,(q.y<0.0)?r1:r2), abs(q.y)-h);
  vec2 cb = q - k1 + k2*clamp( dot(k1-q,k2)/dot2(k2), 0.0, 1.0 );
  float s = (cb.x<0.0 && ca.y<0.0) ? -1.0 : 1.0;
  return s*sqrt( min(dot2(ca),dot2(cb)) );
}

float sdRoundCappedCone( vec3 p, float h, float r1, float r2, float r)
{
  float tan_angle = tan( 1.0/2.0 * atan((h*2.0)/(r1-r2)) );
  float r1_corr = r/tan_angle;
  float r2_corr = r*tan_angle;

  h = h-r;
  r1 = r1-r1_corr;
  r2 = r2-r2_corr;
  return sdCappedCone(p, h, r1, r2 ) - r;
}


// from https://www.shadertoy.com/view/3tBcDR
float sdEllipsoidimprovedV2( vec3 p, vec3 r ) 
{
    float k0 = length(p/r);
    float k1 = length(p/(r*r));
    return (k0<1.0) ? (k0-1.0)*min(min(r.x,r.y),r.z) : k0*(k0-1.0)/k1;
}

// called Round Cone here https://iquilezles.org/articles/distfunctions/
// renamed to avoid confusion with round(capped)cone
float sdBiCapsule( vec3 p, float r1, float r2, float h )
{
  //JD additions
  if(r1>r2+h) return length(p)-r1;
  if(r2>r1+h) return length(vec3(p.x, p.y, p.z-h))-r2;
  // end additions

  // sampling independent computations (only depend on shape)
  float b = (r1-r2)/h;
  float a = sqrt(1.0-b*b);

  // sampling dependant computations
  vec2 q = vec2( length(p.xy), p.z );
  float k = dot(q,vec2(-b,a));
  if( k<0.0 ) return length(q) - r1;
  if( k>a*h ) return length(q-vec2(0.0,h)) - r2;

  return dot(q, vec2(a,b) ) - r1;
}


// adapted from https://www.shadertoy.com/view/Ml3fWj
// by Inigo Quilez
float sdElongatedCylinder( vec3 p, vec3 s )
{

  s.x = clamp (s.x-s.y, 0 , s.x);
  p.x = p.x-clamp(p.x, -s.x, s.x);

  vec2 d = vec2( length(p.xy)-s.y, abs(p.z) - s.z );
  return min(max(d.x,d.y),0.0) + length(max(d,0.0));
}


float sdRoundElongatedCylinder(vec3 p, vec3 s, float r){
    s = s-r;
    return sdElongatedCylinder(p, s) -r;
}


float sdCapsule( vec3 p, float h, float r )
{
  p.z -= clamp( p.z, 0.0, h*2.0 );
  return length( p ) - r;
}

