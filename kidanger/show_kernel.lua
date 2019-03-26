local sharedview
local cache = {}

local log = function(text) end

local function show_one(w)
    if w.dont_layout then return end

    local win = cache[w.id]
    if not win then
        local seq = w.sequences[w.index+1]
        local c = new_colormap()
        c:set_shader('jet')
        if not sharedview then
            sharedview = new_view()
        end

        local seqk = new_sequence(c, seq.player, sharedview)
        seqk:set_glob(seq:get_glob() .. '.k')
        seqk:load_filenames()

        win = new_window()
        win.sequences = { seqk }
        win.dont_layout = true
        cache[w.id] = win
    end

    win.force_geometry = true
    win.size = w.size/3
    win.position = w.position + w.size - win.size
    win.always_on_top = not win.always_on_top

    log('added kernel for ' .. w.id)
end

local function show_all()
    for _, ww in ipairs(get_windows()) do
        show_one(ww)
    end
end

return {
    init=function(plugins)
        log = plugins.log or log
    end,
    show_one=show_one,
    show_all=show_all,
}

