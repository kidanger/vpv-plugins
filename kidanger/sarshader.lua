return {init=function()
    SHADERS['sar'] = [[
        uniform vec3 scale;
        uniform vec3 bias;
        uniform sampler2D tex;
        in vec2 f_texcoord;
        out vec4 out_color;

        vec3 hsvtorgb(vec3 colo)
        {
            vec4 outp;
            float r, g, b, h, s, v;
            r=g=b=h=s=v=0.0;
            h = colo.x; s = colo.y; v = colo.z;
            if (s == 0.0) { r = g = b = v; }
            else {
                float H = mod(floor(h/60.0) , 6.0);
                float p, q, t, f = h/60.0 - H;
                p = v * (1.0 - s);
                q = v * (1.0 - f*s);
                t = v * (1.0 - (1.0 - f)*s);
                if(H == 6.0 || H == 0.0) { r = v; g = t; b = p; }
                else if(H == -1.0 || H == 5.0) { r = v; g = p; b = q; }
                else if(H == 1.0) { r = q; g = v; b = p; }
                else if(H == 2.0) { r = p; g = v; b = t; }
                else if(H == 3.0) { r = p; g = q; b = v; }
                else if(H == 4.0) { r = t; g = p; b = v; }
            }
            return vec3(r, g, b);
        }
        vec3 tonemap(vec3 p)
        {
            float d = length(p);
            float h = pow((d / 100.), 1.4) * 30.;
            h = min(h, 300.);
            if (d < 300.) {
                h = d / 300. * 90.;
            } else if (d < 600.) {
                h = (d - 300.) / 300. * 100. + 90.;
            } else if (d < 900.) {
                h = (d - 600.) / 300. * 50. + 190.;
            } else {
                h = (d - 900.) / 900. * 30. + 240.;
            }
            h = min(h, 270.);
            h = mod(h + 280., 360.);
            float l = d;
            l = min(sqrt(l) / sqrt(2000.), 1.);
            return hsvtorgb(vec3(h, l, l));
        }

        void main()
        {
            vec3 q = texture(tex, f_texcoord.xy).xyz * scale * 1000.;
            vec3 a = tonemap(q);
            out_color = vec4(a, 1.);
        }
    ]]
    end
}


