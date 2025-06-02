import json
from api.api_key_manager import ApiKeyManager
from api.llm_interface import LLMInterface

print("--- Test LLMInterface Combat Triggers (Simplified) ---")
akm = ApiKeyManager()
akm.store_api_key("testkey")
llm_interface = LLMInterface(api_key_manager=akm)

response = llm_interface.generate("test prompt for scene", "test_model", "scene_description")
assert response is not None, "Response for scene_description should not be None"
print(f"Scene Response Snippet: {response[:250]}...")

parsed_json_scene = None
try:
    parsed_json_scene = json.loads(response)
except json.JSONDecodeError as e:
    assert False, f"JSONDecodeError for scene_description: {e}. Response was: {response}"

assert parsed_json_scene is not None, "Parsed JSON for scene_description should not be None"
interactive_elements = parsed_json_scene.get('interactive_elements', [])

combat_trigger_found_and_verified = False
for element in interactive_elements:
    if element.get('id') == 'challenge_raven_combat':
        assert element.get('type') == 'combat_trigger', "Raven element type mismatch"
        assert element.get('target_id') == 'mysterious_raven_npc', "Raven target_id mismatch"
        assert element.get('name') == 'Challenge the Mysterious Raven!', "Raven name mismatch"
        combat_trigger_found_and_verified = True
        break 
assert combat_trigger_found_and_verified, "Combat trigger 'challenge_raven_combat' not found or incorrect."
print("Combat trigger 'challenge_raven_combat' verified successfully.")

# Check another type to ensure no interference
response_wcd = llm_interface.generate("other prompt for wcd", "test_model", "world_conception_document")
assert response_wcd is not None, "Response for world_conception_document should not be None"
print(f"WCD Response Snippet: {response_wcd[:250]}...")
try:
    json.loads(response_wcd)
except json.JSONDecodeError as e:
    assert False, f"JSONDecodeError for world_conception_document: {e}. Response was: {response_wcd}"
print("world_conception_document also generated valid JSON.")

print("--- Test LLMInterface Combat Triggers (Simplified) Complete ---")
