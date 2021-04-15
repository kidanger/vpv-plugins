--[[
in vpvrc:
    plugins.load('gencatshader', 'kidanger/gencatshader')
    plugins.gencatshader.gen('testcat', {
        [0]={250,0,0,'pixel=0'},
        [1]={0,0,20, 'black'},
        [2]={000,200,100,'2 (=green)'},
    })

then,
$ olambda lena.png 'mod(x(:,:,1),3)' | vpv - shader:testcat
]]
local svgs = {}

local function gen(name, cats)
    -- generate shader in glsl
    local glsl = {}
    for v, c in pairs(cats) do
        local str =  ('} else if (cat == %d) {\n'):format(v)
        str = str .. ('  return vec3(%f,%f,%f);\n'):format(c[1]/255,c[2]/255,c[3]/255)
        table.insert(glsl, str)
    end
    local get_color = [[
        vec3 get_color(int cat) {
            if (false) {
            ]] .. table.concat(glsl) .. [[
            }
            return vec3(0., 0., 0.);
        }
    ]]
    SHADERS[name] = get_color .. [[
        uniform sampler2D tex;
        in vec2 f_texcoord;
        out vec4 out_color;

        void main()
        {
             int cat = int(texture(tex, f_texcoord.xy).x);
            vec3 q = get_color(cat);
            out_color = vec4(q, 1.);
        }
    ]]

    -- generate legend in svg
    local y = 0
    svg = '<svg width="1" height="1">'
    for v, c in pairs(cats) do
        local cc = ('rgb(%d,%d,%d)'):format(c[1],c[2],c[3])
        local n = c[4] or ''
        svg = svg .. ('<rect display="absolute" x="0" y="%d" width="%d" height="5" \
                       fill="%s" fill-opacity="1"></rect>'):format(y+18, 11*#n, cc)
        svg = svg .. ('<text display="absolute" font-size="20" y="%d" \
                       fill="%s">%s</text>'):format(y, '#FFFFFF', n)
        y = y + 26
    end
    svg = svg .. '</svg>'
    svgs[name] = svg
end

local curshader = {}
function on_window_tick(w)
    local seq = w.sequences[w.index+1]
    if not seq then return end

    local c = seq.colormap
    if not c then return end

    local s = c:get_shader()
    if s ~= curshader[w.id] then
        curshader[w.id] = s
        seq:put_script_svg('catshader', svgs[s] or '')
    end
end

return {
    on_window_tick=on_window_tick,
    gen=gen,
}

