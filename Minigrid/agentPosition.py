def check_environment_changes(initial_state, final_state):
    # Agent state
    #if(final_state.agent.dest_pos[:2] == initial_state.agent.dest_pos[:2]):
        #print('x')

    # print("Agent state Inital",initial_state.agent.path,"final_state.path",final_state.agent.path)
    if initial_state.agent.dest_pos[:2] != final_state.agent.dest_pos[:2]:
        #print("Agent is NOT at its original starting position.")
        return True
    
    if initial_state.agent.path != final_state.agent.path:
        # print("path",True)
        return True
    
    else:
        # print("Agent has returned to its original starting position.")
        return False
    
    # for initial_door, final_door in zip(initial_state.doors, final_state.doors):
    #     if initial_door.status != final_door.status:
    #         print(f"Door at ({initial_door.x}, {initial_door.y}) has changed status.")
    #         return True
    #     else :
    #         return False
    