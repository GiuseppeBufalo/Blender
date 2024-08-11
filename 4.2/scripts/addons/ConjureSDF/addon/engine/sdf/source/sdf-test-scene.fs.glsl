float GetDist(vec3 p)
{
    float planeDist = p.z;

    float sphere1 = sdSphere(p, 1, u_sdprim01);
    float sphere2 = sdSphere(p, 1, u_sdprim02);
    float result = opSmoothUnion(sphere1, sphere2, .3);

    vec3 cubepoint = transRot(p, u_sdprim03, u_obj_mat);
    float box1 = sdRoundBox(cubepoint, u_sdprim03_dim, .05);

    result = OpDifferenceChamfer(result, box1, .1);

    float d = min(result,planeDist);
 
    return d;
}
