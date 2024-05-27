util.keep_running()

local SOLO_PUBLIC_CMD = "go solopublic"

function ensure_host()
    local local_player = players.user()
    if players.get_host() ~= local_player then
        util.yield(5000)
        local command_ref = menu.ref_by_command_name(SOLO_PUBLIC_CMD)
        if command_ref:isValid() then
            menu.trigger_command(command_ref)
        end
    end
end

util.create_tick_handler(function()
    local success, err = pcall(ensure_host)
    if not success then
        util.toast("Error ensuring host: " .. err)
        util.log("Error ensuring host: " .. err)
    end
    util.yield(5000)
    return true
end)