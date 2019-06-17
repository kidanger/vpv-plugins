
local function align(seq)
    local function basename(f)
        return f:match '^.*/(.-)[.].+$'
    end

    local sref
    for i, s in ipairs(get_sequences()) do
        if seq.player.id == s.player.id
            and seq.collection:get_length() > s.collection:get_length() then
            sref = s
        end
    end

    local filenames = {}
    for i = 0, seq.collection:get_length()-1 do
        local f = seq.collection:get_filename(i)
        filenames[basename(f)] = f
    end

    local kept = {}
    for i = 0, sref.collection:get_length()-1 do
        local f = sref.collection:get_filename(i)
        local b = basename(f)
        if filenames[b] ~= nil then
            table.insert(kept, filenames[b])
        end
    end

    local glob = table.concat(kept, ':')
    seq:set_glob(glob)
    seq:load_filenames()
end

return {
    align=align,
}

