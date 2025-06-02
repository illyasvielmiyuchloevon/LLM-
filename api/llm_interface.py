import urllib.parse # For URL encoding image prompt snippets
import json # For using json.dumps in mock responses
from api.api_key_manager import ApiKeyManager # Assuming execution from root or PYTHONPATH configured

class LLMInterface:
    def __init__(self, api_key_manager: ApiKeyManager):
        self.api_key_manager = api_key_manager

    def generate(self, prompt: str, model_id: str, expected_response_type: str) -> str | None:
        api_key = self.api_key_manager.get_api_key()
        if not api_key:
            print("LLMInterface: Error - API Key not available. Cannot make LLM call.")
            # In a real app, this might use UIManager or raise an exception
            return None

        if not model_id:
            print("LLMInterface: Error - Model ID not provided. Cannot make LLM call.")
            return None

        print("LLMInterface: Preparing to call LLM (simulated)...")
        print(f"  Model ID: {model_id}")
        print(f"  Expected Response Type: {expected_response_type}")
        # Ensure prompt is a string before slicing, though type hint suggests it is.
        prompt_str = str(prompt)
        print(f"  Prompt (first 100 chars): {prompt_str[:100]}...")

        # Simulate LLM call based on expected_response_type
        if expected_response_type == 'detailed_world_blueprint':
            mock_response = f"Mock Detailed World Blueprint: Based on preference supplied in prompt (first 20 chars of prompt: '{prompt_str[:20]}...'). Key elements: ancient ruins, hidden prophecy, mythical creature. Goal: uncover the secrets of the ancients."
            print("LLMInterface: Mock LLM call successful (detailed_world_blueprint).")
            return mock_response
        elif expected_response_type == 'world_conception_document':
            # Ensure prompt_str is used for embedding
            prompt_snippet = prompt_str[:50].replace("\n", " ")
            mock_json_string = f'''
{{
  "world_title": "The Mocked Isle of Eldoria",
  "setting_description": "A mysterious island generated from a mock LLM call, shrouded in digital mist, home to placeholder ruins and forgotten comment blocks.",
  "key_locations": [
    {{"name": "Whispering Code Jungle", "description": "A dense jungle of spaghetti code with hidden functions and strange bugs."}},
    {{"name": "Sunken Database of Azura", "description": "An ancient database partially corrupted, rumored to hold a powerful primary key."}},
    {{"name": "Debuggers Peak", "description": "A high stack trace offering a panoramic view, home to a wise, talking rubber duck."}}
  ],
  "main_characters": [
    {{"name": "Captain 'Stacktrace' Silas", "role": "Helper Function", "description": "A grizzled old function who knows the system's secrets."}},
    {{"name": "NullPointer Witch Lysandra", "role": "Exception", "description": "A sorceress seeking to exploit the system's vulnerabilities."}}
  ],
  "initial_plot_hook": "The player's program crashes on the island after a mysterious segmentation fault, driven by rumors of a legendary lost algorithm hidden somewhere on Eldoria. The prompt received started with: '{prompt_snippet}'"
}}'''
            print("LLMInterface: Mock LLM call successful (world_conception_document as JSON string).")
            return mock_json_string
        elif expected_response_type == 'scene_description':
            prompt_snippet_for_scene_id = prompt_str[:70].replace("\n", " ").replace("'", "\\'").replace('"', '\\"') # Escape single and double quotes
            mock_json_string = f'''
{{
  "scene_id": "mock_scene_for_prompt_start_'{prompt_snippet_for_scene_id}'",
  "narrative": "You are standing at a crossroads. A weathered signpost points in three directions: north towards the mountains, east towards a dark forest, and west towards a shimmering lake. The air is still, and a sense of anticipation hangs heavy.",
  "npcs_in_scene": [
    {{"name": "Old Man Willow", "status": "seems to be asleep", "dialogue_hook": "Zzzzz..."}},
    {{"name": "Mysterious Raven", "status": "observing you intently from a nearby branch", "dialogue_hook": "Caw! (It seems to suggest you choose wisely.)"}}
  ],
  "interactive_elements": [
    {{"id": "go_north_mountains", "name": "Head north towards the towering mountains.", "type": "navigate"}},
    {{"id": "challenge_raven_combat", "name": "Challenge the Mysterious Raven!", "type": "combat_trigger", "target_id": "mysterious_raven_npc"}},
    {{"id": "inspect_signpost_detail", "name": "Examine the weathered signpost closely.", "type": "examine", "target_id": "signpost_object"}},
    {{"id": "talk_to_old_man_willow", "name": "Talk to Old Man Willow.", "type": "dialogue", "target_id": "old_man_willow_npc"}},
    {{"id": "enter_dark_forest", "name": "Venture east into the ominous dark forest.", "type": "navigate"}}
    # Reordered slightly to keep 5 elements, replaced one with combat trigger
  ],
  "environmental_effects": "A gentle breeze rustles the leaves on the trees. The distant cry of a bird echoes."
}}
'''
            print("LLMInterface: Mock LLM call successful (scene_description as JSON string).")
            return mock_json_string
        elif expected_response_type == 'npc_dialogue_response':
            npc_name_in_prompt = "Unknown NPC" # Default
            # Attempt to extract NPC name from prompt (simple parsing)
            if "NPC:" in prompt_str: # Use prompt_str which is guaranteed to be a string
                try:
                    # Assumes format like "Context... \nNPC: Actual Name\nPlayer says..."
                    # or "NPC ID: actual_id" or "NPC Name: Actual Name"
                    # This is a very basic extraction for mock purposes.
                    # A more robust system would pass structured data about the target NPC.
                    split_by_npc_tag = prompt_str.split("NPC:")
                    if len(split_by_npc_tag) > 1:
                         # Take the part after "NPC:", then take first line, strip spaces.
                        npc_name_in_prompt = split_by_npc_tag[1].split("\n")[0].strip()
                        # Further try to clean if it was "NPC ID: npc_id_val" to get "npc_id_val"
                        if npc_name_in_prompt.startswith("ID:"):
                            npc_name_in_prompt = npc_name_in_prompt.split("ID:")[1].strip()
                        elif npc_name_in_prompt.startswith("Name:"):
                             npc_name_in_prompt = npc_name_in_prompt.split("Name:")[1].strip()

                except IndexError:
                    pass # Keep default "Unknown NPC" if parsing fails

            # Sanitize npc_name_in_prompt for use as an ID (if it's not already an ID)
            # and also for embedding in f-string if it contains quotes.
            npc_id_from_name = npc_name_in_prompt.lower().replace(' ', '_').replace("'", "").replace('"', "")
            # Only need to escape double quotes for JSON validity if the snippet itself is part of a JSON string value.
            # Newlines should be removed or replaced for single-line display.
            dialogue_prompt_snippet = prompt_str[:30].replace("\n", " ").replace('"', '\\"')


            mock_json_string = f'''
{{
  "npc_id": "{npc_id_from_name}",
  "dialogue_text": "Well, hello there, traveler! You mentioned something about '{dialogue_prompt_snippet}'. What can I do for you, {npc_name_in_prompt}?",
  "new_npc_status": "curious",
  "attitude_towards_player_change": "+2",
  "knowledge_revealed": [
    {{"topic_id": "local_dangers", "summary": "Implied this area can be dangerous based on your query."}}
  ],
  "dialogue_options_for_player": [
    {{"id": "ask_npc_name_{npc_id_from_name}", "name": "Actually, I wanted to ask your name."}},
    {{"id": "ask_about_location_{npc_id_from_name}", "name": "Can you tell me more about this place?"}},
    {{"id": "state_own_predicament_{npc_id_from_name}", "name": "I find myself in a bit of a bind..."}},
    {{"id": "leave_dialogue_{npc_id_from_name}", "name": "Nothing for now, thank you. Farewell."}}
  ]
}}
'''
            print("LLMInterface: Mock LLM call successful (npc_dialogue_response as JSON string).")
            return mock_json_string
        elif expected_response_type == 'combat_turn_outcome':
            player_strategy_mentioned = "Unknown strategy"
            if "Player Strategy:" in prompt_str:
                try:
                    player_strategy_mentioned = prompt_str.split("Player Strategy:")[1].split("\n")[0].strip()
                except IndexError:
                    pass # Keep default

            target_npc_id = "generic_enemy_id_001" # Placeholder, could be parsed from prompt context in a real system
            # Example: if "Target NPC ID: specific_id" in prompt_str: target_npc_id = ...

            # Simple mock logic: Player hits, NPC takes damage. Combat continues for a few turns.
            # A real system would need to check current HP from context.
            # For this mock, let's assume combat ends after a hypothetical 3rd turn if we could track turns.
            # Since we can't easily track turns here without more context, we'll mostly return combat_ended: false.

            npc_hp_change = -10 # Player always hits for 10 in this mock
            player_hp_change = 0 # Player always dodges in this mock
            combat_ended_mock = False
            victor_mock = None

            # Could add logic here to make combat end sometimes, e.g. based on prompt content
            # if "low health" in prompt_str.lower() and "player" in prompt_str.lower():
            #    player_hp_change = -15 # Player gets hit hard
            #    combat_ended_mock = True
            #    victor_mock = "npc"

            mock_json_string = f'''
{{
  "turn_summary_narrative": "Player uses '{player_strategy_mentioned}' against {target_npc_id}! It's a solid hit for {abs(npc_hp_change)} damage! {target_npc_id} stumbles back, then lunges wildly, but Player deftly dodges the attack.",
  "player_hp_change": {player_hp_change},
  "npc_hp_changes": [
    {{"npc_id": "{target_npc_id}", "hp_change": {npc_hp_change}}}
  ],
  "combat_ended": {json.dumps(combat_ended_mock)},
  "victor": {json.dumps(victor_mock)},
  "player_strategy_feedback": "A well-executed '{player_strategy_mentioned}'!",
  "available_player_strategies": [
    {{"id": "attack_again_{player_strategy_mentioned.lower().replace(' ','_')}", "name": "Attack again with {player_strategy_mentioned}"}},
    {{"id": "defensive_stance", "name": "Take a Defensive Stance"}},
    {{"id": "use_item_healing_potion", "name": "Use Healing Potion (if available)"}},
    {{"id": "try_flee", "name": "Attempt to Flee"}}
  ]
}}
'''
            print("LLMInterface: Mock LLM call successful (combat_turn_outcome as JSON string).")
            return mock_json_string
        else:
            # Generic mock response for other types
            mock_response = f"Mock LLM Response for {expected_response_type} using prompt (first 20 chars: '{prompt_str[:20]}...')."
            print(f"LLMInterface: Mock LLM call successful ({expected_response_type}).")
            return mock_response

    def generate_image(self, image_prompt: str) -> str | None:
        api_key = self.api_key_manager.get_api_key()
        if not api_key:
            print("LLMInterface: Error - API Key not available. Cannot make Image LLM call.")
            return None

        print("LLMInterface: Preparing to call Image Generation LLM (imagen-3.0-generate-002 - simulated)...")
        # Ensure image_prompt is a string before slicing
        image_prompt_str = str(image_prompt)
        print(f"  Image Prompt (first 100 chars): {image_prompt_str[:100]}...")

        # Create a URL-encoded snippet of the prompt for the placeholder URL.
        prompt_for_url = image_prompt_str[:30] # Max 30 chars for the text part of the URL
        url_encoded_prompt_snippet = urllib.parse.quote(prompt_for_url)

        mock_image_url = f"https://via.placeholder.com/800x600.png?text=Scene:{url_encoded_prompt_snippet}"

        print(f"LLMInterface: Mock Image LLM call successful. Returning URL: {mock_image_url}")
        return mock_image_url
