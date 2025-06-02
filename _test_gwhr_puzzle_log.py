from engine.gwhr import GWHR
import copy
import json # For pretty printing dicts if needed, though not strictly for this test

print("--- Test GWHR Environmental Puzzle Log Initialization ---")

# Test 1: __init__ creates default 'environmental_puzzle_log'
print("\n--- Test 1: Default 'environmental_puzzle_log' from __init__ ---")
gwhr_t1 = GWHR()
store1 = gwhr_t1.get_data_store()
assert 'environmental_puzzle_log' in store1, "environmental_puzzle_log key missing after __init__"
assert store1['environmental_puzzle_log'] == {}, \
    f"Default environmental_puzzle_log should be an empty dict, got {store1['environmental_puzzle_log']}"
print("Test 1 Passed.")

# Test 2: initialize without 'environmental_puzzle_log' in initial_world_data
print("\n--- Test 2: initialize without 'environmental_puzzle_log' in input ---")
gwhr_t2 = GWHR() # Fresh instance
initial_data_no_puzzle_log = {"world_title": "No Puzzle Log World"}
gwhr_t2.initialize(initial_data_no_puzzle_log) # This will print GWHR init messages
store2 = gwhr_t2.get_data_store()
assert 'environmental_puzzle_log' in store2, \
    "environmental_puzzle_log key missing after initialize (no input puzzle log)"
assert store2['environmental_puzzle_log'] == {}, \
    f"environmental_puzzle_log should be empty if not in input, got {store2['environmental_puzzle_log']}"
print("Test 2 Passed.")

# Test 3: initialize WITH 'environmental_puzzle_log' in initial_world_data
print("\n--- Test 3: initialize WITH 'environmental_puzzle_log' in input ---")
gwhr_t3 = GWHR() # Fresh instance
custom_puzzle_log_content = {
    "rune_door_west_wing": {
        "status": "unsolved",
        "clues_found": ["rune_symbol_alpha"],
        "elements_state": {"slot_1": "empty", "slot_2": "empty"}
    }
}
initial_data_with_puzzle_log = {
    "world_title": "World With Puzzles",
    "environmental_puzzle_log": copy.deepcopy(custom_puzzle_log_content)
}
gwhr_t3.initialize(initial_data_with_puzzle_log)
store3 = gwhr_t3.get_data_store()

assert 'environmental_puzzle_log' in store3, \
    "environmental_puzzle_log key missing after initialize (with input puzzle log)"
assert store3['environmental_puzzle_log'] == custom_puzzle_log_content, \
    f"Custom environmental_puzzle_log not applied correctly. Expected {custom_puzzle_log_content}, got {store3['environmental_puzzle_log']}"

# Verify deepcopy during initialize for the puzzle log
initial_data_with_puzzle_log['environmental_puzzle_log']['rune_door_west_wing']['status'] = "MODIFIED_EXTERNALLY"
assert gwhr_t3.get_data_store()['environmental_puzzle_log']['rune_door_west_wing']['status'] == "unsolved", \
    "environmental_puzzle_log was not deep_copied during initialize (or via get_data_store)"
print("Test 3 Passed.")

# Test 4: Ensure other GWHR keys are still defaulted/handled if puzzle_log is in input
print("\n--- Test 4: Other GWHR keys with puzzle_log in input ---")
# store3 is from gwhr_t3 which was initialized with custom_puzzle_log
assert 'player_state' in store3 and store3['player_state']['attributes']['strength'] == 10, \
    f"Default player_state missing or incorrect when puzzle_log is provided. Strength: {store3.get('player_state',{}).get('attributes',{}).get('strength')}"
assert 'npcs' in store3 and store3['npcs'] == {}, \
    f"Default npcs missing or incorrect when puzzle_log is provided. NPCs: {store3.get('npcs')}"
assert 'combat_log' in store3 and store3['combat_log'] == [], \
    f"Default combat_log missing or incorrect when puzzle_log is provided. Log: {store3.get('combat_log')}"
print("Test 4 Passed.")


print("\n--- GWHR Environmental Puzzle Log Initialization Tests Complete ---")
