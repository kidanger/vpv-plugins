return {init=function()
    SHADERS['diff'] = [[
        uniform sampler2D tex;
        in vec2 f_texcoord;
        uniform vec3 scale;

        void main (void)
        {
            float palI[3], palR[3], palG[3], palB[3];
            int N = 3;
            palI[0]=-1.00000;palR[0]=0.00000; palG[0]=0.00000; palB[0]=1.00000;
            palI[1]=0.00000; palR[1]=1.00000; palG[1]=1.00000; palB[1]=1.00000;
            palI[2]=1.00000; palR[2]=1.00000; palG[2]=0.00000; palB[2]=0.00000;

            vec3 q = scale * texture(tex, f_texcoord.xy).xyz;
            vec3 p = vec3(palR[0], palG[0], palB[0]);
            for (int i = 1; i < N; i++) {
                if (q.x >= palI[i-1] && q.x <= palI[i]) {
                    float cc = (palI[i] - q.x) / (palI[i] -  palI[i-1]);
                    p.x = cc * palR[i-1] + (1.0 - cc)*palR[i];
                    p.y = cc * palG[i-1] + (1.0 - cc)*palG[i];
                    p.z = cc * palB[i-1] + (1.0 - cc)*palB[i];
                }
            }
            if (q.x >= palI[N-1]) {
                p.x = palR[N-1];
                p.y = palG[N-1];
                p.z = palB[N-1];
            }
            if (isnan(q.x)) {
                p = vec3(0, 0, 0);
            }
            gl_FragColor = vec4(p, 1.);
        }
    ]]
    end
}


