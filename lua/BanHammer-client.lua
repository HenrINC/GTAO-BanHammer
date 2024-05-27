function ban(player_id)
    local player_scid = players.get_rockstar_id(player_id)
    if not player_scid then
        util.toast("Invalid player SCID. Cannot execute command.")
        return
    end
    
    local player_name = players.get_name(player_id)
    
    local banfile = io.open(filesystem.stand_dir() .. "/bans.txt", "a")
    
    if banfile then
        banfile:write(player_scid .. ";" .. player_name .. "\n")
        banfile:close()
    else
        util.toast("Failed to open banfile.txt for writing.")
    end
    
    chat.send_message(player_name .. " has been banned from the H0TF1X network", false, true, true)
end

function create_player_command_menu()
    local root = menu.my_root()
    local player_command_list = menu.list(root, "Ban Players", {}, "")
    local player_actions = {}

    function update_player_list()
        for _, player_id in ipairs(players.list(true, true, true)) do
            local player_name = players.get_name(player_id)
            if not player_actions[player_id] then
                player_actions[player_id] = menu.action(player_command_list, player_name, {}, "", function()
                    ban(player_id)
                end)
            end
        end
    end

    -- Function to remove a player from the list
    function remove_player_from_list(player_id)
        if player_actions[player_id] then
            menu.delete(player_actions[player_id])
            player_actions[player_id] = nil
        end
    end

    -- Initial update of the player list
    update_player_list()

    -- Bind to player join and leave events
    players.on_join(update_player_list)
    players.on_leave(remove_player_from_list)
end

local success, err = pcall(create_player_command_menu)
if not success then
    util.toast("Error creating player command menu: " .. err)
    util.log("Error creating player command menu: " .. err)
end
