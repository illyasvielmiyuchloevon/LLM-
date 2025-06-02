import json
from api.api_key_manager import ApiKeyManager
from api.llm_interface import LLMInterface

print("--- Test LLMInterface Puzzle Elements in Scene Description ---")

# Setup
akm = ApiKeyManager()
akm.store_api_key("fake-api-key-for-puzzle-elements-test")
llm_interface = LLMInterface(api_key_manager=akm)

# Scenario 1: Request 'scene_description'
print("\nScenario 1: Request 'scene_description'")
prompt1 = "Test prompt for scene with puzzle elements."
model1 = "gemini-pro-mock"
type1 = "scene_description"
response1 = llm_interface.generate(prompt=prompt1, model_id=model1, expected_response_type=type1)

print(f"\nRaw Response (Scene Description with Puzzle Elements):\n{response1}")

is_valid_json = False
parsed_json = None
try:
    if response1:
        parsed_json = json.loads(response1)
        is_valid_json = True
except json.JSONDecodeError as e:
    print(f"JSONDecodeError: {e}")

assert is_valid_json, "Response for 'scene_description' should be valid JSON"

puzzle_elements_found_count = 0
if parsed_json:
    interactive_elements = parsed_json.get('interactive_elements', [])
    assert len(interactive_elements) == 5, \
        f"Expected 5 interactive elements, got {len(interactive_elements)}. Elements: {interactive_elements}"

    expected_puzzle_elements_details = {
        "inspect_inscription_north_wall": {
            "name": "Inspect strange inscription (North Wall)",
            "type": "puzzle_element",
            "puzzle_id": "rune_door_puzzle"
        },
        "pull_rusty_lever_A": {
            "name": "Pull the rusty lever (Lever A)",
            "type": "puzzle_element",
            "puzzle_id": "lever_sequence_puzzle"
        }
    }

    verified_expected_puzzles = set()

    for element in interactive_elements:
        assert 'id' in element and 'name' in element and 'type' in element, f"Element missing required keys: {element}"
        if element.get('type') == 'puzzle_element':
            puzzle_elements_found_count += 1
            assert 'puzzle_id' in element, \
                f"Puzzle element '{element.get('id')}' must have a 'puzzle_id'"

            element_id = element.get('id')
            if element_id in expected_puzzle_elements_details:
                expected_details = expected_puzzle_elements_details[element_id]
                assert element.get('name') == expected_details['name'], f"Name mismatch for {element_id}"
                assert element.get('puzzle_id') == expected_details['puzzle_id'], f"Puzzle ID mismatch for {element_id}"
                verified_expected_puzzles.add(element_id)

    assert puzzle_elements_found_count >= 2, \
        f"Expected at least 2 puzzle elements, found {puzzle_elements_found_count}"
    assert len(verified_expected_puzzles) == len(expected_puzzle_elements_details), \
        f"Did not find all expected puzzle elements. Verified: {verified_expected_puzzles}, Expected: {list(expected_puzzle_elements_details.keys())}"

    # Check environmental effects hint
    assert "strange symbols on the north wall" in parsed_json.get('environmental_effects',''), "Hint for inscription missing"
    assert "rusty lever near the east passage" in parsed_json.get('environmental_effects',''), "Hint for lever missing"


# Scenario 2: Check another response type to ensure no interference
print("\nScenario 2: Request 'combat_turn_outcome' (ensure no interference)")
response2 = llm_interface.generate(prompt="Player Strategy: Defend", model_id=model1, expected_response_type="combat_turn_outcome")
assert response2 is not None, "Response 2 should not be None"
parsed_response2 = json.loads(response2) # Should be valid JSON
assert "Player uses 'Defend' against" in parsed_response2.get("turn_summary_narrative",""), \
    f"Narrative mismatch in S2. Got: {parsed_response2.get('turn_summary_narrative','')}"

print("\n--- LLMInterface Puzzle Element Tests Complete ---")
