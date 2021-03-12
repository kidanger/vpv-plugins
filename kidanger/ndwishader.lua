return {init=function()
    SHADERS['ndwi'] = [[
        uniform vec3 scale;
        uniform vec3 bias;
        uniform sampler2D tex;
        in vec2 f_texcoord;
        out vec4 out_color;

        vec3 tonemap(vec3 p)
        {
            float i = p.x * scale.x;
            if (isnan(i))
                return vec3(0,0,0);
            if (i < 0.)
                return mix(vec3(1,1,1),vec3(0,1,0),-i);
            return mix(vec3(1,1,1),vec3(0,0,1),i);
        }
        void main()
        {
            vec3 q = texture(tex, f_texcoord.xy).xyz * scale * 1000.;
            vec3 a = tonemap(q);
            out_color = vec4(a, 1.);
        }
    ]]
end}

