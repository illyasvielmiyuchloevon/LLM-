import json
import copy
from api.api_key_manager import ApiKeyManager
from ui.ui_manager import UIManager
from engine.model_selector import ModelSelector
from engine.adventure_setup import AdventureSetup
from engine.gwhr import GWHR
from api.llm_interface import LLMInterface
from game_logic.game_controller import GameController

print("--- Test GameController Full NPC Dialogue Interaction ---")

# 1. Setup components
ui = UIManager()
akm = ApiKeyManager()
llm = LLMInterface(akm)
ms = ModelSelector(akm)
adv_setup = AdventureSetup(ui, llm, ms) # GC requires adv_setup
gwhr = GWHR()
gc = GameController(akm, ui, ms, adv_setup, gwhr, llm)

akm.store_api_key("dialogue-flow-key")
ms.set_selected_model("gemini-pro-mock")

npc_id = "zebediah_the_wise"
# Use GWHR's default NPC structure and add/override specifics
default_npc_attrs = GWHR().get_data_store()['npcs'].get(npc_id, {}).get('attributes', {})
npc_attributes_for_test = copy.deepcopy(default_npc_attrs)
npc_attributes_for_test.update({"mood": "contemplative", "disposition_towards_player": 10})

initial_npc_data = {
    'id': npc_id, 'name': "Zebediah", 'role': "Sage", 'description': "An old, wise wizard.",
    'attributes': npc_attributes_for_test,
    'dialogue_log': [], 'status': 'observing', 'knowledge': [], 'current_location_id': 'library',
    'personality_traits':[], 'motivations':[], 'faction': None, 'last_interaction_time': 0,
    'status_effects':[], 'current_hp':100, 'max_hp':100 # Ensure HP is there
}
scene_data = {
    "scene_id": "library_entrance",
    "narrative": "You are at the entrance of a vast library. Zebediah the sage is here.",
    "interactive_elements": [
        {"id": "talk_zebediah", "name": "Talk to Zebediah", "type": "dialogue", "target_id": npc_id}
    ],
    "npcs_in_scene": [{"name": "Zebediah", "id": npc_id}] # For context in scene display
}
# Initialize GWHR with player state, this NPC, and set current scene
gwhr.initialize({
    "world_title": "Dialogue Flow Test", "initial_scene_id": "library_entrance",
    "player_state": GWHR().get_data_store()['player_state'],
    "npcs": {npc_id: copy.deepcopy(initial_npc_data)}
})
gwhr.update_state({'current_scene_data': scene_data, 'current_game_time': 0, 'scene_history':[], 'event_log':[]})
gc.current_game_state = "AWAITING_PLAYER_ACTION"

# --- Mock LLMInterface.generate for a multi-turn dialogue ---
llm_call_count = 0
prompts_received_by_llm = []
dialogue_responses_sequence = [
    json.dumps({
        "npc_id": npc_id, "dialogue_text": "Greetings. I sense you seek knowledge. What is it you wish to ask?",
        "new_npc_status": "questioning", "attitude_towards_player_change": "+1",
        "dialogue_options_for_player": [
            {"id": "ask_about_prophecy", "name": "Tell me about the ancient prophecy."},
            {"id": "ask_about_library", "name": "What secrets does this library hold?"}
        ]
    }),
    json.dumps({
        "npc_id": npc_id, "dialogue_text": "Ah, the prophecy... a weighty topic. It speaks of shadows and light. What more specific query burns in your mind?",
        "new_npc_status": "pensive", "attitude_towards_player_change": "+2",
        "knowledge_revealed": [{"topic_id": "prophecy_intro", "summary": "Zebediah confirms the prophecy exists and is complex."}],
        "dialogue_options_for_player": []
    }),
    json.dumps({
        "npc_id": npc_id, "dialogue_text": "The shadow... it is known only as Morian. Now, I must rest. Ponder what you have learned.",
        "new_npc_status": "ending_dialogue", "attitude_towards_player_change": "0",
        "knowledge_revealed": [{"topic_id": "shadow_name_morian", "summary": "The shadow is named Morian."}]
    })
]

original_llm_generate = llm.generate
def mocked_llm_dialogue_generator(prompt, model_id, expected_response_type):
    global llm_call_count, prompts_received_by_llm # Use global for outer scope variables
    prompts_received_by_llm.append(prompt)
    if expected_response_type == 'npc_dialogue_response':
        if llm_call_count < len(dialogue_responses_sequence):
            response = dialogue_responses_sequence[llm_call_count]
            print(f"MOCK LLM (dialogue turn {llm_call_count + 1}) responding...")
            llm_call_count += 1
            return response
        else:
            print("MOCK LLM (dialogue): Ran out of predefined responses!")
            return json.dumps({"dialogue_text": "I have nothing more to say.", "new_npc_status": "ending_dialogue"})
    elif expected_response_type == 'scene_description':
         # This might be called by process_player_action if the action is NOT dialogue,
         # or by image generation part of process_player_action.
         print(f"MOCK LLM (scene_description type for non-dialogue or image prompt context) returning generic scene...")
         # Return a generic scene that won't interfere with dialogue choice counts
         return json.dumps({
             "scene_id": "generic_action_outcome",
             "narrative":"A generic outcome occurred from a non-dialogue action or image generation.",
             "interactive_elements": []
         })
    return original_llm_generate(prompt, model_id, expected_response_type)

llm.generate = mocked_llm_dialogue_generator
original_llm_generate_image = llm.generate_image
def mock_generate_image_dialogue_test(image_prompt):
    print(f"MOCK generate_image called with: {image_prompt[:50]}...")
    return "https://fakeurl.com/dialogue_test_img.png"
llm.generate_image = mock_generate_image_dialogue_test

print("\n--- Simulating Game Loop for Dialogue ---")
try:
    gc.game_loop()
except EOFError:
    print("EOFError caught, as expected after consuming all piped dialogue inputs.")

print("\n--- Assertions after Dialogue ---")
assert llm_call_count == 3, f"LLM should have been called 3 times for dialogue, was {llm_call_count}"
final_npc_state = gwhr.get_data_store()['npcs'][npc_id]
print(f"Final NPC state: {json.dumps(final_npc_state, indent=2)}")

assert final_npc_state['status'] == "ending_dialogue", f"NPC status incorrect: {final_npc_state['status']}"
# Initial disposition was 10. Changes: +1, +2, +0. Expected: 10 + 1 + 2 + 0 = 13.
assert final_npc_state['attributes']['disposition_towards_player'] == 13, \
    f"NPC disposition should be 13, got {final_npc_state['attributes']['disposition_towards_player']}"
assert len(final_npc_state['dialogue_log']) == 3, \
    f"NPC dialogue log should have 3 exchanges, got {len(final_npc_state['dialogue_log'])}"

if len(final_npc_state['dialogue_log']) == 3:
    expected_initial_player_input_for_log = "Selected interaction: 'Talk to Zebediah'"
    assert final_npc_state['dialogue_log'][0]['player'] == expected_initial_player_input_for_log
    assert final_npc_state['dialogue_log'][0]['npc'] == "Greetings. I sense you seek knowledge. What is it you wish to ask?"

    # Player chose option 1 from first set: "Tell me about the ancient prophecy."
    # The 'player_input_for_llm' for the 2nd LLM call should reflect this.
    # The dialogue log for the second exchange should have this as player's part.
    assert "Player says/does to you: 'Tell me about the ancient prophecy.'" in prompts_received_by_llm[1]
    assert final_npc_state['dialogue_log'][1]['player'] == "Tell me about the ancient prophecy."
    assert final_npc_state['dialogue_log'][1]['npc'] == "Ah, the prophecy... a weighty topic. It speaks of shadows and light. What more specific query burns in your mind?"

    # Player typed free text for third turn: "What is the shadow's name?"
    assert "Player says/does to you: 'What is the shadow's name?'" in prompts_received_by_llm[2]
    assert final_npc_state['dialogue_log'][2]['player'] == "What is the shadow's name?"
    assert final_npc_state['dialogue_log'][2]['npc'] == "The shadow... it is known only as Morian. Now, I must rest. Ponder what you have learned."

# After dialogue ends (due to "ending_dialogue" status), game_loop should set state to AWAITING_PLAYER_ACTION.
# However, because game_loop itself exits on EOFError, current_game_state might not be fully updated by the loop's end.
# The important part is that handle_npc_dialogue correctly sets it to original_game_state before exiting.
# And process_player_action returns, allowing game_loop to continue.
# Let's check the state *before* the EOFError would occur if the loop continued.
# The last state set by handle_npc_dialogue before breaking due to 'ending_dialogue' is original_game_state.
# The original_game_state passed to handle_npc_dialogue was set by process_player_action to "NPC_DIALOGUE" then original was "AWAITING_PLAYER_ACTION"
# Then handle_npc_dialogue sets its own original_game_state to gc.current_game_state which would be AWAITING_PLAYER_ACTION.
# This is a bit tangled. The key is that after process_player_action calls handle_npc_dialogue and it returns,
# process_player_action itself returns. The game_loop then continues.
# The last state *within* handle_npc_dialogue before it exits due to "ending_dialogue" is that it sets
# self.current_game_state = original_game_state (which was AWAITING_PLAYER_ACTION from the game_loop call).
# So, after handle_npc_dialogue returns, gc.current_game_state *should* be AWAITING_PLAYER_ACTION.
# The EOFError happens when game_loop tries to get the *next* command.
assert gc.current_game_state == "AWAITING_PLAYER_ACTION", \
    f"Game state should be AWAITING_PLAYER_ACTION after dialogue, but is {gc.current_game_state}"


event_log = gwhr.get_data_store()['event_log']
dialogue_exchange_events = [e for e in event_log if e['type'] == 'dialogue_exchange']
assert len(dialogue_exchange_events) == 3, f"Expected 3 dialogue_exchange events, got {len(dialogue_exchange_events)}"
player_dialogue_choice_events = [e for e in event_log if e['type'] == 'player_dialogue_choice']
assert len(player_dialogue_choice_events) == 1, f"Expected 1 player_dialogue_choice event, got {len(player_dialogue_choice_events)}"

llm.generate = original_llm_generate
llm.generate_image = original_llm_generate_image

print("\n--- GameController NPC Dialogue Interaction Test Complete ---")
