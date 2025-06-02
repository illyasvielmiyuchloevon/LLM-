import json
import copy
from api.api_key_manager import ApiKeyManager
from ui.ui_manager import UIManager
from engine.model_selector import ModelSelector
from engine.adventure_setup import AdventureSetup
from engine.gwhr import GWHR
from api.llm_interface import LLMInterface
from game_logic.game_controller import GameController

print("--- Test GameController Puzzle Interaction Flow ---")

# 1. Setup
ui = UIManager()
akm = ApiKeyManager()
llm = LLMInterface(akm)
ms = ModelSelector(akm)
adv_setup = AdventureSetup(ui, llm, ms)
gwhr = GWHR()
gc = GameController(akm, ui, ms, adv_setup, gwhr, llm)

akm.store_api_key("gc-puzzle-flow-key")
ms.set_selected_model("gemini-pro-mock")

# --- Initial GWHR state for testing puzzles ---
puzzle_id_test = "rune_altar_puzzle"
initial_puzzle_log_state = {
    puzzle_id_test: {
        "status": "unsolved",
        "clues_found": [],
        "elements_state": {"altar_gem_slot": None, "north_rune": "dim", "south_rune": "dim"}
    }
}
scene_with_puzzle_element = {
    "scene_id": "altar_chamber",
    "narrative": "An ancient altar stands in the center. Runes glow faintly on the north and south walls.",
    "interactive_elements": [
        {"id": "press_north_rune", "name": "Press the North Rune", "type": "puzzle_element", "puzzle_id": puzzle_id_test},
        {"id": "place_gem_on_altar", "name": "Place Gem on Altar", "type": "puzzle_element", "puzzle_id": puzzle_id_test},
        {"id": "leave_chamber", "name": "Leave the chamber", "type": "navigate"}
    ],
    "background_image_url": None, # Explicitly set for consistent test data
    "image_prompt_elements": None
}
# Initialize GWHR and ensure scene_history and event_log are clean for this test
gwhr.initialize({
    "world_title": "Puzzle Test World",
    "environmental_puzzle_log": copy.deepcopy(initial_puzzle_log_state)
})
gwhr.update_state({
    'current_scene_data': scene_with_puzzle_element,
    'current_game_time': 1, # Start at time 1 for first action
    'scene_history':[],
    'event_log':[]
})
gc.current_game_state = "AWAITING_PLAYER_ACTION"

# --- Mock LLMInterface.generate for puzzle evaluation responses ---
llm_puzzle_eval_call_count = 0
puzzle_prompts_received = []
mock_puzzle_eval_responses = [
    json.dumps({
        "puzzle_id": puzzle_id_test,
        "action_feedback_narrative": "You press the North Rune. It glows brighter, and a faint click is heard from the altar.",
        "puzzle_state_changed": True,
        "updated_puzzle_elements_state": {"north_rune": "bright", "altar_gem_slot_status": "awaiting_gem"},
        "new_clues_revealed": ["The altar seems to be waiting for something."],
        "puzzle_solved": False,
        "solution_narrative": None
    }),
    json.dumps({
        "puzzle_id": puzzle_id_test,
        "action_feedback_narrative": "You place the Gem of Light onto the altar. The runes blaze with light, and the altar hums with power!",
        "puzzle_state_changed": True,
        "updated_puzzle_elements_state": {"altar_gem_slot": "gem_placed", "south_rune": "bright"},
        "new_clues_revealed": ["All runes are now bright!"],
        "puzzle_solved": True,
        "solution_narrative": "The altar fully activates, and a hidden compartment slides open revealing an ancient scroll!"
    })
]

original_llm_generate = llm.generate
def mocked_llm_puzzle_eval_generator(prompt, model_id, expected_response_type):
    global llm_puzzle_eval_call_count, puzzle_prompts_received
    puzzle_prompts_received.append(prompt)
    if expected_response_type == 'environmental_puzzle_solution_eval':
        if llm_puzzle_eval_call_count < len(mock_puzzle_eval_responses):
            response = mock_puzzle_eval_responses[llm_puzzle_eval_call_count]
            print(f"MOCK LLM (puzzle eval turn {llm_puzzle_eval_call_count + 1}) responding...")
            llm_puzzle_eval_call_count += 1
            return response
        else:
            return json.dumps({"action_feedback_narrative": "The puzzle seems unresponsive."})
    elif expected_response_type == 'scene_description': # For image gen context or generic actions
         return json.dumps(gwhr.get_data_store()['current_scene_data']) # Return a valid scene desc
    return original_llm_generate(prompt, model_id, expected_response_type)

llm.generate = mocked_llm_puzzle_eval_generator
original_llm_generate_image = llm.generate_image
def mock_generate_image_puzzle_test(image_prompt):
    print(f"MOCK generate_image called for: {image_prompt[:50]}...")
    return "https://fakeurl.com/puzzle_scene.png"
llm.generate_image = mock_generate_image_puzzle_test

# --- Test Flow ---
print("\n--- Test 1: Player presses North Rune ---")
gc.process_player_action("interact_element", "press_north_rune")

puzzle_log_after_action1 = gwhr.get_data_store()['environmental_puzzle_log']
assert llm_puzzle_eval_call_count == 1, "LLM puzzle eval not called once for Test 1"
assert puzzle_log_after_action1[puzzle_id_test]['elements_state']['north_rune'] == "bright"
assert "The altar seems to be waiting for something." in puzzle_log_after_action1[puzzle_id_test]['clues_found']
assert puzzle_log_after_action1[puzzle_id_test]['status'] == "unsolved"
assert gc.current_game_state == "AWAITING_PLAYER_ACTION"
assert gwhr.get_data_store()['current_game_time'] == 2
print("Test 1 assertions passed.")

print("\n--- Test 2: Player places Gem on Altar ---")
gc.process_player_action("interact_element", "place_gem_on_altar")

puzzle_log_after_action2 = gwhr.get_data_store()['environmental_puzzle_log']
assert llm_puzzle_eval_call_count == 2, "LLM puzzle eval not called a second time for Test 2"
assert puzzle_log_after_action2[puzzle_id_test]['elements_state']['altar_gem_slot'] == "gem_placed"
assert puzzle_log_after_action2[puzzle_id_test]['elements_state']['south_rune'] == "bright"
assert "All runes are now bright!" in puzzle_log_after_action2[puzzle_id_test]['clues_found']
assert puzzle_log_after_action2[puzzle_id_test]['status'] == "solved"
assert gc.current_game_state == "AWAITING_PLAYER_ACTION"
assert gwhr.get_data_store()['current_game_time'] == 3
print("Test 2 assertions passed.")

event_log = gwhr.get_data_store()['event_log']
print(f"Event Log: {json.dumps(event_log, indent=2)}")
puzzle_interaction_events = [e for e in event_log if e['type'] == 'puzzle_interaction']
assert len(puzzle_interaction_events) == 2
puzzle_update_events = [e for e in event_log if e['type'] == 'puzzle_update']
assert len(puzzle_update_events) == 2
puzzle_solved_events = [e for e in event_log if e['type'] == 'puzzle_solved']
assert len(puzzle_solved_events) == 1
print("Event log assertions passed.")

# Restore
llm.generate = original_llm_generate
llm.generate_image = original_llm_generate_image

print("\n--- GameController Puzzle Interaction Flow Test Complete ---")
