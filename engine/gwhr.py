import copy

class GWHR: # GameWorldHistoryRecorder
    def __init__(self):
        default_player_state = {
            'attributes': {
                "strength": 10, "dexterity": 10, "intelligence": 10,
                "sanity": 100, "willpower": 100, "insight": 5,
                "current_hp": 100, "max_hp": 100,
                "attack_power": 10, "defense_power": 5,
                "evasion_chance": 0.1, "hit_chance": 0.8
            },
            'skills': [],
            'inventory': [],
            'equipment_slots': {
                "head": None, "torso": None, "hands": None,
                "legs": None, "feet": None, "main_hand": None, "off_hand": None
            },
            'current_location_id': None
        }
        self.data_store: dict = {
            'current_game_time': 0,
            'scene_history': [],
            'event_log': [],
            'current_scene_data': {},
            'player_state': copy.deepcopy(default_player_state),
            'npcs': {},
            'combat_log': [],
            'environmental_puzzle_log': {},
            'knowledge_codex': {}, # New
            'dynamic_world_events_log': [], # New
            'world_state': { # New or ensure exists
                'current_weather': { # New
                    "condition": "clear",
                    "intensity": "mild",
                    "effects_description": "The sky is clear and the air is calm."
                }
            }
        }

    def initialize(self, initial_world_data: dict):
        # Start by taking a deep copy of the defaults set in __init__
        # This ensures all keys, including player_state and npcs, are initialized with their default structures.
        temp_store = copy.deepcopy(self.data_store)

        # Create a deep copy of the incoming initial_world_data to safely manipulate it
        processed_initial_data = copy.deepcopy(initial_world_data)

        # Handle player_state specifically: merge attributes, otherwise replace wholesale.
        if 'player_state' in processed_initial_data:
            incoming_ps = processed_initial_data.pop('player_state') # Remove from processed_initial_data

            # Merge attributes: default attributes < incoming attributes
            # Ensure target_ps['attributes'] exists if it somehow didn't from __init__ (it should)
            target_ps_attributes = temp_store['player_state'].setdefault('attributes', {})
            if 'attributes' in incoming_ps: # Check if incoming_ps has attributes to merge
                incoming_player_attributes = incoming_ps.get('attributes', {})
                target_ps_attributes.update(incoming_player_attributes) # Update existing attributes dict

            # For other top-level keys in player_state (skills, inventory, equipment_slots, current_location_id),
            # if they are present in incoming_ps, they replace the defaults.
            # If not present, the defaults from __init__ (already in temp_store['player_state']) remain.
            for key in ['skills', 'inventory', 'equipment_slots', 'current_location_id']:
                if key in incoming_ps:
                    temp_store['player_state'][key] = copy.deepcopy(incoming_ps[key])

        # If 'player_state' not in processed_initial_data, temp_store['player_state'] (from __init__) is used.

        # Handle npcs specifically if 'main_characters' are provided in original initial_world_data
        if 'main_characters' in initial_world_data and isinstance(initial_world_data['main_characters'], list):
            default_npc_attributes_template = { # Template for defaults for each NPC
                "mood": "neutral", "disposition_towards_player": 0,
                "current_hp": 50, "max_hp": 50,
                "attack_power": 8, "defense_power": 3,
                "evasion_chance": 0.05, "hit_chance": 0.7
            }
            processed_npcs = {}
            for char_data in initial_world_data['main_characters']:
                npc_id = char_data.get('id', char_data.get('name', '').lower().replace(' ', '_'))
                if not npc_id:
                    print(f"GWHR Warning: Skipping character due to missing id/name: {char_data}")
                    continue

                # Merge attributes: default_npc_attributes_template < char_data.attributes
                current_npc_attributes = copy.deepcopy(default_npc_attributes_template)
                if isinstance(char_data.get('attributes'), dict):
                    current_npc_attributes.update(char_data.get('attributes'))

                processed_npcs[npc_id] = {
                    'id': npc_id,
                    'name': char_data.get('name', 'Unknown NPC'),
                    'description': char_data.get('description', ''),
                    'role': char_data.get('role', 'character'),
                    'attributes': current_npc_attributes, # Use merged attributes
                    'skills': char_data.get('skills', []),
                    'knowledge': char_data.get('knowledge', []),
                    'status_effects': char_data.get('status_effects', []),
                    'current_location_id': char_data.get('current_location_id', None),
                    'personality_traits': char_data.get('personality_traits', []),
                    'motivations': char_data.get('motivations', []),
                    'faction': char_data.get('faction', None),
                    'dialogue_log': [],
                    'last_interaction_time': 0
                }
            temp_store['npcs'] = processed_npcs # Replace the initial empty 'npcs' dict
        # If 'main_characters' not in initial_world_data, temp_store keeps the 'npcs': {} from __init__

        # Update temp_store with any remaining keys from processed_initial_data (e.g. world_title)
        # This will overwrite keys in temp_store if they also exist in processed_initial_data
        temp_store.update(processed_initial_data)

        # Ensure other core GWHR keys are present (mostly as a safeguard, __init__ sets them)
        temp_store.setdefault('current_game_time', 0)
        temp_store.setdefault('scene_history', [])
        temp_store.setdefault('event_log', [])
        temp_store.setdefault('current_scene_data', {})
        temp_store.setdefault('combat_log', [])
        temp_store.setdefault('knowledge_codex', {}) # New
        temp_store.setdefault('dynamic_world_events_log', []) # New

        # Ensure world_state and its current_weather sub-key are correctly defaulted
        # Get the world_state from temp_store, defaulting to an empty dict if it wasn't in initial_world_data
        # (though __init__ ensures it exists in self.data_store, and thus in temp_store initially)
        world_state_in_temp = temp_store.setdefault('world_state', {})

        # Get the default weather from the original self.data_store (from __init__)
        # This is a bit indirect; simpler would be to define default_weather_structure once.
        # However, this ensures we use the structure defined in __init__.
        default_weather_structure = self.data_store['world_state']['current_weather']
        world_state_in_temp.setdefault('current_weather', copy.deepcopy(default_weather_structure))

        self.data_store = temp_store # Assign the fully constructed store

        print(f"GWHR: Initialized/Merged with world data. World Title: '{self.data_store.get('world_title', 'N/A')}'")
        print(f"GWHR: Player state attributes: {self.data_store.get('player_state', {}).get('attributes')}")
        print(f"GWHR: NPC data processed. Found {len(self.data_store.get('npcs', {}))} NPCs.")
        if len(self.data_store.get('npcs', {})) > 0:
            first_npc_id = list(self.data_store['npcs'].keys())[0]
            print(f"GWHR: First NPC ({first_npc_id}) attributes: {self.data_store['npcs'][first_npc_id].get('attributes')}")

    def log_event(self, event_description: str, event_type: str = "general", causal_factors: list = None):
        event_log = self.data_store.setdefault('event_log', [])
        event_entry = {
            "time": self.data_store.get('current_game_time', 0),
            "type": event_type,
            "description": event_description,
            "causal_factors": causal_factors if causal_factors is not None else []
        }
        event_log.append(event_entry)

    def log_dialogue(self, speaker: str, utterance: str, npc_id: str = None):
        self.log_event(
            event_description=f"Dialogue: {speaker} says, '{utterance}'",
            event_type="dialogue",
            causal_factors=[npc_id] if npc_id else []
        )

    def update_state(self, updates: dict):
        updated_keys = []
        for key, value in updates.items():
            if key == 'current_scene_data':
                new_scene_data = copy.deepcopy(value)
                self.data_store['current_scene_data'] = new_scene_data

                scene_history = self.data_store.setdefault('scene_history', [])
                scene_summary = {
                    'time': self.data_store.get('current_game_time', 0),
                    'scene_id': new_scene_data.get('scene_id'),
                    'narrative_snippet': (new_scene_data.get('narrative', '')[:50] + "...") if new_scene_data.get('narrative') else "N/A...",
                    'image_url': new_scene_data.get('background_image_url'),
                    'image_prompt_elements': new_scene_data.get('image_prompt_elements'),
                    'num_interactive_elements': len(new_scene_data.get('interactive_elements', []))
                }
                scene_history.append(scene_summary)
                updated_keys.append(key)
            elif key == 'current_game_time':
                 self.data_store[key] = value
                 updated_keys.append(key)
            else:
                self.data_store[key] = copy.deepcopy(value)
                updated_keys.append(key)

        if updated_keys:
             print(f"GWHR: State updated for keys: {updated_keys}. (Simulated deep merge/logic).")
        else:
             print(f"GWHR: Update_state called with no keys to update or empty updates dictionary.")

    def get_current_context(self, granularity: str = "full", context_type: str = "general") -> dict:
        print("GWHR: get_current_context currently returns a full copy. This will be refined for targeted context provision.")
        return copy.deepcopy(self.data_store)

    def get_data_store(self) -> dict:
        return copy.deepcopy(self.data_store)
