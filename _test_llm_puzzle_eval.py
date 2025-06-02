import json
from api.api_key_manager import ApiKeyManager
from api.llm_interface import LLMInterface

print("--- Test LLMInterface Puzzle Evaluation Response ---")

# Setup
akm = ApiKeyManager()
akm.store_api_key("fake-api-key-for-puzzle-test")
llm_interface = LLMInterface(api_key_manager=akm)
model_for_test = "gemini-pro-mock"

# Scenario 1: Generic puzzle action (not the specific mocked solution)
print("\nScenario 1: Generic puzzle action")
prompt1 = "Puzzle ID: rune_door_puzzle\nAction: inspect_runes" # This specific combo is not a special case in mock
response1 = llm_interface.generate(prompt=prompt1, model_id=model_for_test, expected_response_type="environmental_puzzle_solution_eval")
print(f"\nRaw Response 1:\n{response1}")

is_valid_json1 = False
parsed_json1 = None
try:
    if response1:
        parsed_json1 = json.loads(response1)
        is_valid_json1 = True
except json.JSONDecodeError as e:
    print(f"JSONDecodeError for Response 1: {e}")

assert is_valid_json1, "Response 1 should be valid JSON"
if parsed_json1:
    assert parsed_json1.get('puzzle_id') == "rune_door_puzzle", f"S1 Puzzle ID. Expected 'rune_door_puzzle', Got {parsed_json1.get('puzzle_id')}"
    assert "Player attempts action 'inspect_runes' on puzzle 'rune_door_puzzle'. Nothing obvious happens." in parsed_json1.get('action_feedback_narrative', ''), f"S1 Narrative. Got {parsed_json1.get('action_feedback_narrative')}"
    assert parsed_json1.get('puzzle_state_changed') is False, f"S1 puzzle_state_changed. Expected False, Got {parsed_json1.get('puzzle_state_changed')}"
    # Empty dict {} becomes null when json.dumps(None if not dict else dict) is not used, but {} if dict is empty
    # The mock uses json.dumps(updated_elements if updated_elements else None)
    # If updated_elements is {}, it becomes null. If it's {'a':1}, it's {"a":1}.
    assert parsed_json1.get('updated_puzzle_elements_state') is None, f"S1 updated_elements. Expected None (from empty dict), Got {parsed_json1.get('updated_puzzle_elements_state')}"
    assert parsed_json1.get('new_clues_revealed') is None, f"S1 new_clues. Expected None (from empty list), Got {parsed_json1.get('new_clues_revealed')}"
    assert parsed_json1.get('puzzle_solved') is False, f"S1 puzzle_solved. Expected False, Got {parsed_json1.get('puzzle_solved')}"
    assert parsed_json1.get('solution_narrative') is None, f"S1 solution_narrative. Expected None, Got {parsed_json1.get('solution_narrative')}"
print("Scenario 1 assertions passed.")

# Scenario 2: Specific mocked solution for "rune_door_puzzle"
print("\nScenario 2: Specific solution for 'rune_door_puzzle'")
prompt2 = "Puzzle ID: rune_door_puzzle\nAction: use_sunstone_on_altar"
response2 = llm_interface.generate(prompt=prompt2, model_id=model_for_test, expected_response_type="environmental_puzzle_solution_eval")
print(f"\nRaw Response 2:\n{response2}")

is_valid_json2 = False
parsed_json2 = None
try:
    if response2:
        parsed_json2 = json.loads(response2)
        is_valid_json2 = True
except json.JSONDecodeError as e:
    print(f"JSONDecodeError for Response 2: {e}")
assert is_valid_json2, "Response 2 should be valid JSON"
if parsed_json2:
    assert parsed_json2.get('puzzle_id') == "rune_door_puzzle"
    assert "You place the Sunstone onto the altar." in parsed_json2.get('action_feedback_narrative', '')
    assert parsed_json2.get('puzzle_state_changed') is True
    assert parsed_json2.get('updated_puzzle_elements_state') == {"altar_state": "sunstone_placed", "door_runes": "all_glowing"}
    assert parsed_json2.get('new_clues_revealed') == ["The door seems to hum with energy."]
    assert parsed_json2.get('puzzle_solved') is True
    assert "massive stone door groans and slides open" in parsed_json2.get('solution_narrative', '')
print("Scenario 2 assertions passed.")

# Scenario 3: Specific mocked action for "lever_sequence"
print("\nScenario 3: Specific action for 'lever_sequence'")
prompt3 = "Puzzle ID: lever_sequence\nAction: pull_lever_A"
response3 = llm_interface.generate(prompt=prompt3, model_id=model_for_test, expected_response_type="environmental_puzzle_solution_eval")
print(f"\nRaw Response 3:\n{response3}")
is_valid_json3 = False
parsed_json3 = None
try:
    if response3:
        parsed_json3 = json.loads(response3)
        is_valid_json3 = True
except json.JSONDecodeError as e:
    print(f"JSONDecodeError for Response 3: {e}")
assert is_valid_json3, "Response 3 should be valid JSON"
if parsed_json3:
    assert parsed_json3.get('puzzle_id') == "lever_sequence"
    assert "You pull Lever A. A distant click is heard." in parsed_json3.get('action_feedback_narrative', '')
    assert parsed_json3.get('puzzle_state_changed') is True
    assert parsed_json3.get('updated_puzzle_elements_state') == {"lever_A_state": "down"}
    assert parsed_json3.get('new_clues_revealed') == ["One of the three lights above the door now glows green."]
    assert parsed_json3.get('puzzle_solved') is False
    assert parsed_json3.get('solution_narrative') is None
print("Scenario 3 assertions passed.")

# Scenario 4: Check another response type to ensure no interference
print("\nScenario 4: Request 'combat_turn_outcome' (ensure no interference)")
response4 = llm_interface.generate(prompt="Player Strategy: Attack", model_id=model_for_test, expected_response_type="combat_turn_outcome")
assert response4 is not None, "Response 4 should not be None"
parsed_response4 = json.loads(response4) # Should be valid JSON
assert "Player uses 'Attack' against" in parsed_response4.get("turn_summary_narrative",""), \
    f"Narrative mismatch in S4. Got: {parsed_response4.get('turn_summary_narrative','')}"
print("Scenario 4 assertions passed.")

print("\n--- LLMInterface Puzzle Evaluation Tests Complete ---")
