return {init=function()
    SHADERS['angle'] = [[
        uniform vec3 scale;
        uniform vec3 bias;
        uniform sampler2D tex;
        in vec2 f_texcoord;
        out vec4 out_color;

        float M_PI = 3.1415926535897932;
        float M_PI_2 = 1.5707963267948966;
        float atan2(float x, float y)
        {
           if (x>0.0) { return atan(y/x); }
           else if(x<0.0 && y>0.0) { return atan(y/x) + M_PI; }
           else if(x<0.0 && y<=0.0 ) { return atan(y/x) - M_PI; }
           else if(x==0.0 && y>0.0 ) { return M_PI_2; }
           else if(x==0.0 && y<0.0 ) { return -M_PI_2; }
           return 0.0;
        }

        vec3 hsvtorgb(float a)
        {
            vec4 outp;
            float r, g, b, h, s, v;
            r=g=b=0.0;
            s = 1; v = 1;
            float px = cos(a);
            float py = sin(a);
            h = (180.0/M_PI)*(atan2(-px, py) + M_PI);
            if (isnan(a)) { r = g = b = 0.0; }
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
            float d = p.x;
            return hsvtorgb(d);
        }

        void main()
        {
            vec3 q = texture(tex, f_texcoord.xy).xyz;
            vec3 a = tonemap(q);
            out_color = vec4(a, 1.);
        }
    ]]
    end
}



