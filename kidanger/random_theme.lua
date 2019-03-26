local default_theme = setup_theme()

local function get_theme(random)
    if not random then return default_theme end
    local style = ImGuiStyle()
    local Colors = style.Colors
    for k, v in pairs(default_theme.Colors) do
        Colors[k] = v
    end
    style.FrameRounding = math.random() * 5
    style.WindowRounding = math.random() * 5
    local primary = ImVec4(math.random(), math.random(), math.random(), 1.)
    local secondary = ImVec4(math.random(), math.random(), math.random(), 1.)
    Colors[ImGuiCol_FrameBg]               = primary
    Colors[ImGuiCol_FrameBgActive]         = secondary
    Colors[ImGuiCol_TitleBg]               = primary
    Colors[ImGuiCol_TitleBgActive]         = secondary
    Colors[ImGuiCol_Button]                = primary
    Colors[ImGuiCol_ButtonActive]          = secondary
    Colors[ImGuiCol_Header]                = primary
    Colors[ImGuiCol_HeaderActive]          = secondary
    style.Colors = Colors
    return style
end

function set_random_theme()
    set_theme(get_theme(true))
end

return {
    set_random_theme=set_random_theme,
}

