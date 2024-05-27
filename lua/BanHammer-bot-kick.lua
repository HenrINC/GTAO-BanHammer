util.keep_running()


-- less invasive command for debugging
-- local BAN_CMD = "flipveh "
local BAN_CMD = "kick "



function get_banned_players()
    local banned_players = {}

    local file = io.open(filesystem.stand_dir() .. "/bans.txt", "r")
    if not file then
        util.toast("Failed to open bans.txt for reading.")
        return banned_players
    end

    for line in file:lines() do
        util.toast("Bans: " .. line)
        local scid = tonumber(line)
        if scid then
            table.insert(banned_players, scid)
        end
    end

    file:close()

    return banned_players
end

function kick(player_id)
    local player_name = players.get_name(player_id)

    local command_ref = menu.ref_by_command_name(BAN_CMD .. player_name)
    if command_ref:isValid() then
        menu.trigger_command(command_ref)
    end
end

function kick_banned_players()
    local banned_players = get_banned_players()
    
    for _, player_id in ipairs(banned_players) do
        util.toast("Bans: " .. player_id)
    end
    local lobby_players = players.list(true, true, true)
    for _, player_id in ipairs(lobby_players) do
        local player_scid = players.get_rockstar_id(player_id)
        -- util.toast("Checking player SCID: " .. player_scid)
        if player_scid and table.contains(banned_players, player_scid) then
            kick(player_id)
        end
    end
end



util.create_tick_handler(function()
    local success, err = pcall(kick_banned_players)
    if not success then
        util.toast("Error enforcing bans: " .. err)
        util.log("Error enforcing bans: " .. err)
    end
    util.yield(100)
    return true
end)
