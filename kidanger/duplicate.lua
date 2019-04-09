
local function frame(s, filename)
    local player = new_player()
    local seqk = new_sequence(s.colormap, player, s.view)
    seqk:set_glob(filename)
    seqk:load_filenames()
    local win = new_window()
    win.sequences = { seqk }
end

return {
    frame=frame,
    gui=function()
        for _, s in pairs(get_sequences()) do
            local c = s.collection
            local len = c:get_length()
            for i = 0, len-1 do
                local filename = c:get_filename(i)
                if button(filename) then
                    frame(s, filename)
                end
            end
        end
    end
}

