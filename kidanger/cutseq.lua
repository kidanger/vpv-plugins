
local cutseq
local pref
local offset

local function auto_center_cut(seq)
    cutseq = seq
    local sref = nil
    for i, s in ipairs(get_sequences()) do
        if seq.player.id == s.player.id
            and seq.collection:get_length() > s.collection:get_length() then
            sref = s
        end
    end
    offset = (seq.collection:get_length() - sref.collection:get_length() - 4) // 2
    print(offset)
    pref = sref.player
    seq.player = new_player()
end

local function tick()
    if cutseq then
        cutseq.player.frame = pref.frame + offset
    end
end

return {
    auto_center_cut=auto_center_cut,
    on_tick=tick,
}

