import json
import copy
from api.api_key_manager import ApiKeyManager
from ui.ui_manager import UIManager
from engine.model_selector import ModelSelector
from engine.adventure_setup import AdventureSetup
from engine.gwhr import GWHR
from api.llm_interface import LLMInterface
from game_logic.game_controller import GameController

print("--- Test GameController Combat Flow ---")

# 1. Setup
ui = UIManager()
akm = ApiKeyManager()
llm = LLMInterface(akm)
ms = ModelSelector(akm)
adv_setup = AdventureSetup(ui, llm, ms)
gwhr = GWHR()
gc = GameController(akm, ui, ms, adv_setup, gwhr, llm)

akm.store_api_key("combat-flow-key")
ms.set_selected_model("gemini-pro-mock")

# --- Initial Player and NPC data for GWHR ---
player_attrs_template = GWHR().get_data_store()['player_state']['attributes']
player_initial_attrs = copy.deepcopy(player_attrs_template)
player_initial_attrs.update({"current_hp": 100, "max_hp": 100, "attack_power": 12, "defense_power": 6})

npc_id_goblin = "goblin_warrior_1"
default_npc_attrs_template = { 
    "mood": "neutral", "disposition_towards_player": 0, "current_hp": 50, "max_hp": 50, 
    "attack_power": 8, "defense_power": 3, "evasion_chance": 0.05, "hit_chance": 0.7
}
npc_goblin_attributes = copy.deepcopy(default_npc_attrs_template)
npc_goblin_attributes.update({"current_hp": 30, "max_hp": 30, "attack_power": 7, "defense_power": 2, "mood":"aggressive"})
npc_goblin_data = {
    'id': npc_id_goblin, 'name': "Goblin Warrior", 'role': "Enemy", 'attributes': npc_goblin_attributes,
    'status': 'hostile', 'skills': [], 'knowledge': [], 'status_effects': [], 
    'current_location_id': None, 'personality_traits': [], 'motivations': [], 
    'faction': None, 'dialogue_log': [], 'last_interaction_time': 0
}
scene_with_combat_trigger = {
    "scene_id": "battle_arena_entry",
    "narrative": "You enter a dusty arena. A fierce Goblin Warrior glares at you!",
    "interactive_elements": [
        {"id": "fight_goblin", "name": "Challenge the Goblin Warrior", "type": "combat_trigger", "target_id": npc_id_goblin},
        {"id": "flee_arena", "name": "Attempt to flee the arena", "type": "navigate"}
    ],
    "npcs_in_scene": [{"name": "Goblin Warrior", "id": npc_id_goblin}]
}
gwhr.initialize({
    "world_title": "Combat Test Arena", "initial_scene_id": "battle_arena_entry",
    "player_state": {"attributes": player_initial_attrs}, 
    "npcs": {npc_id_goblin: copy.deepcopy(npc_goblin_data)}
})
gwhr.update_state({
    'current_scene_data': scene_with_combat_trigger, 'current_game_time': 0, 
    'scene_history':[], 'event_log':[], 'combat_log':[]
})
# gc.current_game_state = "AWAITING_PLAYER_ACTION" # process_player_action will set its own state

# --- Mock LLMInterface.generate for combat outcomes ---
llm_combat_call_count = 0
combat_prompts_received = []
mock_combat_outcomes = [
    json.dumps({
        "turn_summary_narrative": "Player attacks Goblin! Hits for 8 damage. Goblin retaliates, -5 HP to Player.",
        "player_hp_change": -5, "npc_hp_changes": [{"npc_id": npc_id_goblin, "hp_change": -8}], 
        "combat_ended": False, "victor": None, "player_strategy_feedback": "Direct attack worked!",
        "available_player_strategies": [{"id": "power_attack", "name": "Power Attack"}, {"id": "defend", "name": "Defend"}]
    }),
    json.dumps({
        "turn_summary_narrative": "Player uses Power Attack! Goblin defeated!",
        "player_hp_change": 0, "npc_hp_changes": [{"npc_id": npc_id_goblin, "hp_change": -25}], 
        "combat_ended": True, "victor": "player", "player_strategy_feedback": "Devastating Power Attack!",
        "available_player_strategies": [] 
    })
]
original_llm_generate = llm.generate
def mocked_llm_combat_generator(prompt, model_id, expected_response_type):
    global llm_combat_call_count, combat_prompts_received 
    combat_prompts_received.append(prompt)
    if expected_response_type == 'combat_turn_outcome':
        if llm_combat_call_count < len(mock_combat_outcomes):
            response = mock_combat_outcomes[llm_combat_call_count]
            print(f"MOCK LLM (combat turn {llm_combat_call_count + 1}) responding...")
            llm_combat_call_count += 1
            return response
        else:
            print("MOCK LLM (combat): Ran out of predefined combat responses!")
            return json.dumps({"turn_summary_narrative": "Stalemate...", "player_hp_change": 0, "npc_hp_changes": [], "combat_ended": True, "victor": "draw"})
    # This mock no longer needs to handle 'scene_description' for initial scene load if we don't call game_loop
    return original_llm_generate(prompt, model_id, expected_response_type) 
llm.generate = mocked_llm_combat_generator

original_llm_generate_image = llm.generate_image
def mock_generate_image_combat_test(image_prompt): 
    print(f"MOCK generate_image called for: {image_prompt[:50]}...")
    return "https://fakeurl.com/combat_test_img.png"
llm.generate_image = mock_generate_image_combat_test

# --- Simulate combat flow by directly calling process_player_action that triggers initiate_combat ---
if __name__ == "__main__":
    print("\n--- Directly testing combat initiation and loop via process_player_action ---")
    action_id_to_trigger_combat = "fight_goblin" 
    gc.current_game_state = "AWAITING_PLAYER_ACTION" # State before player makes a choice in game_loop

    try:
        # This call will enter initiate_combat, then combat_loop, which will consume piped inputs
        gc.process_player_action("interact_element", action_id_to_trigger_combat)
        # After combat, process_player_action returns, and this script continues.
        # The combat_loop itself should handle all piped inputs for combat.
        # The last input is for show_combat_results.
    except EOFError:
        print("EOFError caught in test script, possibly from 'Press Enter to continue' in show_combat_results.")
    except Exception as e:
        print(f"UNEXPECTED ERROR during combat test: {e}")
        import traceback
        traceback.print_exc()

    print("\n--- Assertions after Combat ---")
    assert llm_combat_call_count == 2, f"LLM should have been called 2 times for combat, was {llm_combat_call_count}"

    final_gwhr_store = gwhr.get_data_store()
    final_player_state = final_gwhr_store['player_state']
    final_npcs_state = final_gwhr_store['npcs']

    print(f"Final Player HP: {final_player_state['attributes']['current_hp']}")
    assert final_player_state['attributes']['current_hp'] == 95, \
        f"Player HP after combat incorrect. Expected 95, Got {final_player_state['attributes']['current_hp']}" 

    assert npc_id_goblin in final_npcs_state, f"Goblin NPC {npc_id_goblin} not found in final GWHR."
    final_goblin_data = final_npcs_state[npc_id_goblin]
    print(f"Final Goblin HP: {final_goblin_data['attributes']['current_hp']}")
    print(f"Final Goblin Status: {final_goblin_data.get('status')}")
    assert final_goblin_data['attributes']['current_hp'] <= 0, \
        f"Goblin HP should be <= 0. Got {final_goblin_data['attributes']['current_hp']}"
    assert final_goblin_data.get('status') == 'defeated', \
        f"Goblin status should be 'defeated'. Got {final_goblin_data.get('status')}"

    # After combat_loop finishes, it sets state to AWAITING_PLAYER_ACTION.
    # process_player_action (which called initiate_combat) then returns.
    # So gc.current_game_state should be AWAITING_PLAYER_ACTION.
    assert gc.current_game_state == "AWAITING_PLAYER_ACTION", \
        f"Game state should be AWAITING_PLAYER_ACTION after combat, but is {gc.current_game_state}"
    assert gc.active_combat_data == {}, \
        f"active_combat_data should be cleared after combat, but is {gc.active_combat_data}"

    event_log = final_gwhr_store['event_log']
    combat_start_event = next((e for e in event_log if e['type'] == 'combat_start'), None)
    assert combat_start_event is not None, "combat_start event not logged"
    combat_end_event = next((e for e in event_log if e['type'] == 'combat_end'), None)
    assert combat_end_event is not None, "combat_end event not logged"
    # Check the summary in the combat_end event. It comes from active_combat_data['final_summary_narrative']
    # which is the turn_summary_narrative of the *last* combat turn.
    # The mock response for turn 2 (ending turn) is "Player uses Power Attack! Goblin defeated!"
    # The HP check adds " All opponents defeated!"
    expected_combat_end_summary = "Player uses Power Attack! Goblin defeated! All opponents defeated!"
    assert combat_end_event['payload']['summary'] == expected_combat_end_summary, \
        f"Combat end summary mismatch: Expected '{expected_combat_end_summary}', Got '{combat_end_event['payload']['summary']}'"
    
    combat_turn_events = [e for e in event_log if e['type'] == 'combat_turn_detail']
    assert len(combat_turn_events) == 2, f"Expected 2 combat_turn_detail events, got {len(combat_turn_events)}"

    llm.generate = original_llm_generate
    llm.generate_image = original_llm_generate_image

    print("\n--- GameController Combat Flow Test Complete ---")
