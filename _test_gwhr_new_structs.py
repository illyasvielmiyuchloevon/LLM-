from engine.gwhr import GWHR
import copy
import json # For pretty printing dicts if needed

print("--- Test GWHR New Data Structures Initialization ---")

default_weather_expected = {
    "condition": "clear",
    "intensity": "mild",
    "effects_description": "The sky is clear and the air is calm."
}

# Test 1: __init__ creates defaults
print("\n--- Test 1: Defaults from __init__ ---")
gwhr_t1 = GWHR()
store1 = gwhr_t1.get_data_store()

assert 'knowledge_codex' in store1 and store1['knowledge_codex'] == {}, \
    f"knowledge_codex init failed, got: {store1.get('knowledge_codex')}"
assert 'dynamic_world_events_log' in store1 and store1['dynamic_world_events_log'] == [], \
    f"dynamic_world_events_log init failed, got: {store1.get('dynamic_world_events_log')}"
assert 'world_state' in store1, "world_state key missing after __init__"
assert isinstance(store1.get('world_state'), dict), "world_state should be a dict"
assert 'current_weather' in store1['world_state'], "current_weather missing in world_state from __init__"
assert store1['world_state']['current_weather'] == default_weather_expected, \
    f"Default current_weather incorrect. Got: {store1['world_state']['current_weather']}"
print("Test 1 Passed.")

# Test 2: initialize without these new keys in initial_world_data
print("\n--- Test 2: initialize without new keys in input ---")
gwhr_t2 = GWHR()
initial_data_minimal = {"world_title": "Minimal World"}
gwhr_t2.initialize(initial_data_minimal) # This will print GWHR init messages
store2 = gwhr_t2.get_data_store()

assert store2.get('knowledge_codex') == {}, \
    f"knowledge_codex should be default empty dict, got: {store2.get('knowledge_codex')}"
assert store2.get('dynamic_world_events_log') == [], \
    f"dynamic_world_events_log should be default empty list, got: {store2.get('dynamic_world_events_log')}"
assert store2.get('world_state', {}).get('current_weather') == default_weather_expected, \
    f"Default current_weather should persist. Got: {store2.get('world_state', {}).get('current_weather')}"
print(f"Weather in Test 2: {store2.get('world_state', {}).get('current_weather')}")
print("Test 2 Passed.")

# Test 3: initialize WITH these new keys in initial_world_data
print("\n--- Test 3: initialize WITH new keys in input ---")
gwhr_t3 = GWHR()
custom_kc = {"lore_001": {"title": "Ancient Kings", "content": "..."}}
custom_dwel = [{"event_id": "volcano_erupt", "timestamp": 10, "description": "Mount Doom rumbled."}]
custom_weather = {"condition": "stormy", "intensity": "high", "effects_description": "A fierce storm rages!"}
initial_data_with_new_keys = {
    "world_title": "World With New Keys",
    "knowledge_codex": copy.deepcopy(custom_kc),
    "dynamic_world_events_log": copy.deepcopy(custom_dwel),
    "world_state": {
        "current_weather": copy.deepcopy(custom_weather),
        "other_world_state_var": "value"
    }
}
gwhr_t3.initialize(initial_data_with_new_keys)
store3 = gwhr_t3.get_data_store()

assert store3.get('knowledge_codex') == custom_kc, \
    f"Custom knowledge_codex not applied. Expected {custom_kc}, Got {store3.get('knowledge_codex')}"
assert store3.get('dynamic_world_events_log') == custom_dwel, \
    f"Custom dynamic_world_events_log not applied. Expected {custom_dwel}, Got {store3.get('dynamic_world_events_log')}"
assert store3.get('world_state', {}).get('current_weather') == custom_weather, \
    f"Custom current_weather not applied. Expected {custom_weather}, Got {store3.get('world_state', {}).get('current_weather')}"
assert store3.get('world_state', {}).get('other_world_state_var') == "value", \
    f"Other world_state var lost. Got {store3.get('world_state', {}).get('other_world_state_var')}"
print(f"Weather in Test 3: {store3.get('world_state', {}).get('current_weather')}")

# Verify deepcopy of top-level new keys during initialize
initial_data_with_new_keys['knowledge_codex']['lore_001']['title'] = "MODIFIED_KC"
assert gwhr_t3.get_data_store()['knowledge_codex']['lore_001']['title'] == "Ancient Kings", \
    "knowledge_codex was not deep_copied by overall WCD deepcopy in initialize (or by get_data_store)"

initial_data_with_new_keys['world_state']['current_weather']['condition'] = "sunny_modified"
assert gwhr_t3.get_data_store()['world_state']['current_weather']['condition'] == "stormy", \
    "world_state.current_weather was not deep_copied by overall WCD deepcopy in initialize (or by get_data_store)"
print("Test 3 Passed.")

# Test 4: initialize with world_state present but MISSING current_weather
print("\n--- Test 4: initialize with world_state but no current_weather ---")
gwhr_t4 = GWHR()
initial_data_ws_no_weather = {
    "world_title": "World State No Weather",
    "world_state": { # world_state exists
        "some_other_global_flag": True
        # but current_weather is missing from this input
    }
}
gwhr_t4.initialize(initial_data_ws_no_weather)
store4 = gwhr_t4.get_data_store()

assert 'current_weather' in store4.get('world_state', {}), \
    "current_weather should be defaulted into existing world_state"
assert store4.get('world_state', {}).get('current_weather') == default_weather_expected, \
    f"Default current_weather not applied. Got: {store4.get('world_state', {}).get('current_weather')}"
assert store4.get('world_state', {}).get('some_other_global_flag') is True, \
    "Other world_state var lost when defaulting weather"
print("Test 4 Passed.")

print("\n--- GWHR New Data Structures Initialization Tests Complete ---")
