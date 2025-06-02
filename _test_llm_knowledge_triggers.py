import json
from api.api_key_manager import ApiKeyManager
from api.llm_interface import LLMInterface

print("--- Test LLMInterface Knowledge Triggers in Mocks ---")

# Setup
akm = ApiKeyManager()
akm.store_api_key("fake-api-key-for-knowledge-triggers-test")
llm_interface = LLMInterface(api_key_manager=akm)
model_for_test = "gemini-pro-mock" 

# --- Test 1: 'scene_description' for 'on_scene_load_knowledge' ---
print("\n--- Test 1: 'scene_description' for 'on_scene_load_knowledge' ---")
response1 = llm_interface.generate(prompt="Load scene X", model_id=model_for_test, expected_response_type="scene_description")
print(f"Raw Response S1 (Scene):\n{response1 if response1 else 'None'}")
parsed_json1 = None
try:
    if response1: parsed_json1 = json.loads(response1)
except Exception as e: print(f"S1 JSON Error: {e}")
assert parsed_json1 is not None, "S1: Response should be valid JSON"
assert 'on_scene_load_knowledge' in parsed_json1, "S1: 'on_scene_load_knowledge' field missing"
knowledge1 = parsed_json1.get('on_scene_load_knowledge', []) # Use .get for safety in assertion
assert isinstance(knowledge1, list) and len(knowledge1) > 0, "S1: 'on_scene_load_knowledge' should be a non-empty list"
if knowledge1: # Check structure only if list is not empty
    assert 'topic_id' in knowledge1[0] and 'summary' in knowledge1[0] and \
           'source_type' in knowledge1[0] and 'source_detail' in knowledge1[0], "S1: Knowledge item structure incorrect"
    print(f"Scene load knowledge (first item): {knowledge1[0]}")
print("Test 1 Passed.")

# --- Test 2: 'npc_dialogue_response' for 'knowledge_revealed' ---
print("\n--- Test 2: 'npc_dialogue_response' for 'knowledge_revealed' ---")
# For the dynamic NPC name in source_detail, the mock extracts from "NPC: <Name>"
npc_name_for_test2 = "Zebediah"
prompt2 = f"NPC: {npc_name_for_test2}\nPlayer: Tell me a secret."
response2 = llm_interface.generate(prompt=prompt2, model_id=model_for_test, expected_response_type="npc_dialogue_response")
print(f"Raw Response S2 (NPC Dialogue):\n{response2 if response2 else 'None'}")
parsed_json2 = None
try:
    if response2: parsed_json2 = json.loads(response2)
except Exception as e: print(f"S2 JSON Error: {e}")
assert parsed_json2 is not None, "S2: Response should be valid JSON"
assert 'knowledge_revealed' in parsed_json2, "S2: 'knowledge_revealed' field missing"
knowledge2 = parsed_json2.get('knowledge_revealed', [])
assert isinstance(knowledge2, list) and len(knowledge2) > 0, "S2: 'knowledge_revealed' should be a non-empty list"
if knowledge2:
    assert 'topic_id' in knowledge2[0] and 'summary' in knowledge2[0] and \
           'source_type' in knowledge2[0] and 'source_detail' in knowledge2[0], "S2: Knowledge item structure incorrect"
    assert knowledge2[0]['source_type'] == "dialogue", f"S2: Source type. Expected 'dialogue', Got '{knowledge2[0]['source_type']}'"
    assert npc_name_for_test2 in knowledge2[0]['source_detail'], f"S2: NPC name '{npc_name_for_test2}' missing from source_detail. Got: '{knowledge2[0]['source_detail']}'"
    print(f"NPC dialogue knowledge (first item): {knowledge2[0]}")
print("Test 2 Passed.")

# --- Test 3: 'environmental_puzzle_solution_eval' for 'knowledge_revealed' ---
print("\n--- Test 3: 'environmental_puzzle_solution_eval' for 'knowledge_revealed' ---")
# Test the solved case
prompt3_solved = "Puzzle ID: rune_door_puzzle\nAction: use_sunstone_on_altar"
response3_solved = llm_interface.generate(prompt=prompt3_solved, model_id=model_for_test, expected_response_type="environmental_puzzle_solution_eval")
print(f"Raw Response S3 Solved (Puzzle Eval):\n{response3_solved if response3_solved else 'None'}")
parsed_json3_solved = None
try:
    if response3_solved: parsed_json3_solved = json.loads(response3_solved)
except Exception as e: print(f"S3 Solved JSON Error: {e}")
assert parsed_json3_solved is not None, "S3 Solved: Response should be valid JSON"
assert 'knowledge_revealed' in parsed_json3_solved, "S3 Solved: 'knowledge_revealed' field missing"
knowledge3_solved = parsed_json3_solved.get('knowledge_revealed', [])
assert isinstance(knowledge3_solved, list) and len(knowledge3_solved) > 0, "S3 Solved: 'knowledge_revealed' should be a non-empty list"
if knowledge3_solved:
    assert 'topic_id' in knowledge3_solved[0] and 'summary' in knowledge3_solved[0] and \
           'source_type' in knowledge3_solved[0] and 'source_detail' in knowledge3_solved[0], "S3 Solved: Knowledge item structure incorrect"
    assert knowledge3_solved[0]['source_type'] == "puzzle_solution", f"S3 Solved: Source type. Expected 'puzzle_solution', Got '{knowledge3_solved[0]['source_type']}'"
    print(f"Puzzle solved knowledge (first item): {knowledge3_solved[0]}")

# Test a non-solving case that still reveals knowledge
prompt3_partial = "Puzzle ID: lever_sequence\nAction: pull_lever_A"
response3_partial = llm_interface.generate(prompt=prompt3_partial, model_id=model_for_test, expected_response_type="environmental_puzzle_solution_eval")
print(f"Raw Response S3 Partial (Puzzle Eval):\n{response3_partial if response3_partial else 'None'}")
parsed_json3_partial = None
try:
    if response3_partial: parsed_json3_partial = json.loads(response3_partial)
except Exception as e: print(f"S3 Partial JSON Error: {e}")
assert parsed_json3_partial is not None, "S3 Partial: Response should be valid JSON"
assert 'knowledge_revealed' in parsed_json3_partial, "S3 Partial: 'knowledge_revealed' field missing"
knowledge3_partial = parsed_json3_partial.get('knowledge_revealed', [])
assert isinstance(knowledge3_partial, list) and len(knowledge3_partial) > 0, "S3 Partial: 'knowledge_revealed' should be a non-empty list"
if knowledge3_partial:
    assert knowledge3_partial[0]['source_type'] == "puzzle_interaction", f"S3 Partial: Source type. Expected 'puzzle_interaction', Got '{knowledge3_partial[0]['source_type']}'"
    print(f"Puzzle partial knowledge (first item): {knowledge3_partial[0]}")
print("Test 3 Passed.")

print("\n--- LLMInterface Knowledge Trigger Tests Complete ---")
