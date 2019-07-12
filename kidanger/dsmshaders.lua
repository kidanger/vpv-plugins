return {init=function()
    local scalemap = [[
        uniform vec3 scale;
        uniform vec3 bias;

        float scalemap(float p) {
            return clamp(p * scale.x + bias.x, 0.0, 1.0);
        }
        vec2 scalemap(vec2 p) {
            return clamp(p * scale.xy + bias.xy, 0.0, 1.0);
        }
        vec3 scalemap(vec3 p) {
            return clamp(p * scale.xyz + bias.xyz, 0.0, 1.0);
        }
    ]]
    SHADERS['dsmrender'] = scalemap .. [[
        uniform sampler2D src;

        void main (void)
        {
            //http://soliton.vm.bytemark.co.uk/pub/cpt-city/td/tn/DEM_poster.png.index.html
            float palI[8], palR[8], palG[8], palB[8];
            const int N = 8;
            palI[0]=0.00000; palR[0]=0.00000; palG[0]=0.38039; palB[0]=0.27843;
            palI[1]=0.01020; palR[1]=0.06275; palG[1]=0.47843; palB[1]=0.18431;
            palI[2]=0.10200; palR[2]=0.90980; palG[2]=0.84314; palB[2]=0.49020;
            palI[3]=0.24490; palR[3]=0.63137; palG[3]=0.26275; palB[3]=0.00000;
            palI[4]=0.34690; palR[4]=0.61961; palG[4]=0.00000; palB[4]=0.00000;
            palI[5]=0.57140; palR[5]=0.43137; palG[5]=0.43137; palB[5]=0.43137;
            palI[6]=0.81630; palR[6]=1.00000; palG[6]=1.00000; palB[6]=1.00000;
            palI[7]=1.00000; palR[7]=1.00000; palG[7]=1.00000; palB[7]=1.00000;

            // use texelFetchOffset to extract exact pixels (no interpolation or borders)
            ivec2 size = textureSize(src, 0);
            float pp = texelFetchOffset(src, ivec2(gl_TexCoord[0].xy*size), 0, ivec2(0, 0)).x;
            float px = texelFetchOffset(src, ivec2(gl_TexCoord[0].xy*size), 0, ivec2(1, 0)).x;
            float py = texelFetchOffset(src, ivec2(gl_TexCoord[0].xy*size), 0, ivec2(0, 1)).x;
            float dx = px - pp;
            float dy = py - pp;

	    float pi = 355.0/113;
            float t = pi/4;
            float z = cos(t) * dx + sin(t) * dy;
	    z = .5  + 30 * z * scale.x;

            vec3 q = scalemap(texture2D(src, gl_TexCoord[0].xy).xyz);
            vec3 p = q;
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

            p = p * z + 0.1;
            gl_FragColor = vec4(p, 1.);
        }
    ]]

    -- from pvflip by Gabriele Facciolo
    SHADERS['dem'] = scalemap .. [[
        uniform sampler2D src;

        void main (void)
        {
            //http://soliton.vm.bytemark.co.uk/pub/cpt-city/td/tn/DEM_screen.png.index.html
            //float palI[8], palR[8], palG[8], palB[8];
            //int N=6;
            //palI[0]=0.00000; palR[0]=0.00000; palG[0]=0.51765; palB[0]=0.20784;
            //palI[1]=0.12500; palR[1]=0.20000; palG[1]=0.80000; palB[1]=0.00000;
            //palI[2]=0.25000; palR[2]=0.95686; palG[2]=0.94118; palB[2]=0.44314;
            //palI[3]=0.50000; palR[3]=0.95686; palG[3]=0.74118; palB[3]=0.27059;
            //palI[4]=0.75000; palR[4]=0.60000; palG[4]=0.39216; palB[4]=0.16863;
            //palI[5]=1.00000; palR[5]=1.00000; palG[5]=1.00000; palB[5]=1.00000;

            ////http://soliton.vm.bytemark.co.uk/pub/cpt-city/td/DEM_print.gpf
            //float palI[8], palR[8], palG[8], palB[8];
            //int N=7;
            //palI[0]=0.00000; palR[0]=0.20000; palG[0]=0.40000; palB[0]=0.00000;
            //palI[1]=0.12500; palR[1]=0.50588; palG[1]=0.76471; palB[1]=0.12157;
            //palI[2]=0.25000; palR[2]=1.00000; palG[2]=1.00000; palB[2]=0.80000;
            //palI[3]=0.50000; palR[3]=0.95686; palG[3]=0.74118; palB[3]=0.27059;
            //palI[4]=0.62500; palR[4]=0.40000; palG[4]=0.20000; palB[4]=0.04706;
            //palI[5]=0.75000; palR[5]=0.40000; palG[5]=0.20000; palB[5]=0.00000;
            //palI[6]=1.00000; palR[6]=1.00000; palG[6]=1.00000; palB[6]=1.00000;

            //http://soliton.vm.bytemark.co.uk/pub/cpt-city/td/tn/DEM_poster.png.index.html
            float palI[8], palR[8], palG[8], palB[8];
            int N = 8;
            palI[0]=0.00000; palR[0]=0.00000; palG[0]=0.38039; palB[0]=0.27843;
            palI[1]=0.01020; palR[1]=0.06275; palG[1]=0.47843; palB[1]=0.18431;
            palI[2]=0.10200; palR[2]=0.90980; palG[2]=0.84314; palB[2]=0.49020;
            palI[3]=0.24490; palR[3]=0.63137; palG[3]=0.26275; palB[3]=0.00000;
            palI[4]=0.34690; palR[4]=0.61961; palG[4]=0.00000; palB[4]=0.00000;
            palI[5]=0.57140; palR[5]=0.43137; palG[5]=0.43137; palB[5]=0.43137;
            palI[6]=0.81630; palR[6]=1.00000; palG[6]=1.00000; palB[6]=1.00000;
            palI[7]=1.00000; palR[7]=1.00000; palG[7]=1.00000; palB[7]=1.00000;

            vec4 q = texture2D(src, gl_TexCoord[0].xy);

            vec4 p;
            p.w = 1.0;

            if (isnan(q.x)) {
                p.x = 0.0;
                p.y = 0.0;
                p.z = 0.0;
            } else {
                q.xyz = scalemap(q.xyz);
                p.x = palR[0];
                p.y = palG[0];
                p.z = palB[0];

                for(int i=1;i<N;i++) {
                    if(q.x >= palI[i-1] && q.x <= palI[i]){
                        float cc = (palI[i] - q.x) / (palI[i] -  palI[i-1]);
                        p.x = cc * palR[i-1] + (1.0 - cc)*palR[i];
                        p.y = cc * palG[i-1] + (1.0 - cc)*palG[i];
                        p.z = cc * palB[i-1] + (1.0 - cc)*palB[i];
                    }
                }

                if(q.x >= palI[N-1]){
                    p.x = palR[N-1];
                    p.y = palG[N-1];
                    p.z = palB[N-1];
                }
            }
            gl_FragColor = vec4(p.xyz, 1.);
        }
    ]]
    end
}

