import json 
from api.api_key_manager import ApiKeyManager
from api.llm_interface import LLMInterface

print("--- Test LLMInterface New Mock Responses (Codex, Dynamic Event, Weather) ---")

# Setup
akm = ApiKeyManager()
akm.store_api_key("fake-api-key-for-new-mocks-test") # API Key stored
llm_interface = LLMInterface(api_key_manager=akm)
model_for_test = "gemini-pro-mock" 

# --- Test 1: Codex Entry Generation ---
print("\n--- Test 1: expected_response_type == 'codex_entry_generation' ---")
prompt1 = "Context Hint: ancient_runes_translation\nSource Type: item_interaction\nSource Detail: ancient_tablet_001"
response1 = llm_interface.generate(prompt=prompt1, model_id=model_for_test, expected_response_type="codex_entry_generation")
print(f"Raw Response 1 (Codex):\n{response1}")
parsed_json1 = None
try:
    if response1: parsed_json1 = json.loads(response1)
except json.JSONDecodeError as e: print(f"JSONDecodeError for Response 1: {e}")
assert parsed_json1 is not None, "Response 1 should be valid JSON"
if parsed_json1:
    assert parsed_json1.get('knowledge_id') == "ancient_runes_translation_codex", f"S1 ID: {parsed_json1.get('knowledge_id')}"
    assert "Ancient Runes Translation" in parsed_json1.get('title', ''), f"S1 Title: {parsed_json1.get('title', '')}"
    assert parsed_json1.get('source_type', '') == "item_interaction", f"S1 SourceType: {parsed_json1.get('source_type', '')}"
    assert parsed_json1.get('source_detail', '') == "ancient_tablet_001", f"S1 SourceDetail: {parsed_json1.get('source_detail', '')}"
    assert "This is detailed lore about ancient runes translation" in parsed_json1.get('content', ''), f"S1 Content: {parsed_json1.get('content', '')}"
print("Test 1 Passed.")

# --- Test 2: Dynamic Event Outcome ---
print("\n--- Test 2: expected_response_type == 'dynamic_event_outcome' ---")
prompt2 = "Event Hint: earthquake_west_canyon"
response2 = llm_interface.generate(prompt=prompt2, model_id=model_for_test, expected_response_type="dynamic_event_outcome")
print(f"Raw Response 2 (Dynamic Event):\n{response2}")
parsed_json2 = None
try:
    if response2: parsed_json2 = json.loads(response2)
except json.JSONDecodeError as e: print(f"JSONDecodeError for Response 2: {e}")
assert parsed_json2 is not None, "Response 2 should be valid JSON"
if parsed_json2:
    api_key_suffix = akm.get_api_key()[-2:] if akm.get_api_key() else 'rand'
    expected_event_id = f"earthquake_west_canyon_event_{api_key_suffix}"
    assert parsed_json2.get('event_id', '') == expected_event_id, f"S2 EventID: Expected '{expected_event_id}', Got '{parsed_json2.get('event_id', '')}'"
    assert "earthquake_west_canyon" in parsed_json2.get('description', ''), f"S2 Description: {parsed_json2.get('description', '')}"
    assert len(parsed_json2.get('effects_on_world', [])) == 3, f"S2 Effects count: {len(parsed_json2.get('effects_on_world', []))}"
    assert parsed_json2.get('new_scene_id') is None, f"S2 new_scene_id: {parsed_json2.get('new_scene_id')}"
print("Test 2 Passed.")

# --- Test 3: Weather Update Description ---
print("\n--- Test 3: expected_response_type == 'weather_update_description' ---")
prompt3a = "Old Condition: clear" 
response3a = llm_interface.generate(prompt=prompt3a, model_id=model_for_test, expected_response_type="weather_update_description")
print(f"Raw Response 3a (Weather - clear to stormy):\n{response3a}")
parsed_json3a = None
try:
    if response3a: parsed_json3a = json.loads(response3a)
except json.JSONDecodeError as e: print(f"JSONDecodeError for Response 3a: {e}")
assert parsed_json3a is not None, "Response 3a should be valid JSON"
if parsed_json3a:
    assert parsed_json3a.get('new_weather_condition') == "stormy"
    assert parsed_json3a.get('new_weather_intensity') == "violent"
    assert "A sudden, violent thunderstorm erupts!" in parsed_json3a.get('weather_effects_description', '')

prompt3b = "Old Condition: stormy" 
response3b = llm_interface.generate(prompt=prompt3b, model_id=model_for_test, expected_response_type="weather_update_description")
print(f"Raw Response 3b (Weather - stormy to misty):\n{response3b}")
parsed_json3b = None
try:
    if response3b: parsed_json3b = json.loads(response3b)
except json.JSONDecodeError as e: print(f"JSONDecodeError for Response 3b: {e}")
assert parsed_json3b is not None, "Response 3b should be valid JSON"
if parsed_json3b:
    assert parsed_json3b.get('new_weather_condition') == "misty"
    assert parsed_json3b.get('new_weather_intensity') == "light"

prompt3c = "Old Condition: misty" 
response3c = llm_interface.generate(prompt=prompt3c, model_id=model_for_test, expected_response_type="weather_update_description")
parsed_json3c = None
try:
    if response3c: parsed_json3c = json.loads(response3c)
except json.JSONDecodeError as e: print(f"JSONDecodeError for Response 3c: {e}")
assert parsed_json3c is not None, "Response 3c should be valid JSON"
if parsed_json3c:
    assert parsed_json3c.get('new_weather_condition') == "clear"
print("Test 3 Passed.")

# --- Test 4: Ensure other types still work (e.g. scene_description) ---
print("\n--- Test 4: Other types still functional ---")
response4 = llm_interface.generate(prompt="scene prompt", model_id=model_for_test, expected_response_type="scene_description")
assert response4 is not None, "Response 4 should not be None"
parsed_json4 = json.loads(response4) # Check validity
assert "crossroads" in parsed_json4.get("narrative",""), f"S4 Narrative: {parsed_json4.get('narrative','')}"
print("Test 4 Passed.")

print("\n--- LLMInterface New Mocks Test Complete ---")
