import copy

class GWHR: # GameWorldHistoryRecorder
    def __init__(self):
        default_player_state = {
            'attributes': {
                "strength": 10, "dexterity": 10, "intelligence": 10,
                "sanity": 100, "willpower": 100, "insight": 5
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
            'player_state': copy.deepcopy(default_player_state) # Initialize with default player state
        }

    def initialize(self, initial_world_data: dict):
        # Create a deep copy of the incoming data to avoid modifying the original
        processed_initial_data = copy.deepcopy(initial_world_data)

        # Handle player_state separately: if present in initial_world_data, it overrides the default.
        # Otherwise, the default from __init__ is kept.
        if 'player_state' in processed_initial_data:
            # Assume initial_world_data['player_state'] is complete if provided
            self.data_store['player_state'] = copy.deepcopy(processed_initial_data.pop('player_state'))
        # else: player_state remains as the default from __init__

        # Update the rest of self.data_store with other keys from initial_world_data
        # This will overwrite common keys like 'world_title' if present in processed_initial_data,
        # and add any other new keys from processed_initial_data.
        self.data_store.update(processed_initial_data)

        # Ensure other GWHR specific keys (not player_state which is handled above)
        # have their defaults from __init__ if not provided by initial_world_data
        # (though .update() would have added them if they were in processed_initial_data)
        # This setdefault logic is more about ensuring they exist if initial_world_data was minimal.
        # Given __init__ now sets them, this is more of a safeguard or for clarity.
        self.data_store.setdefault('current_game_time', 0)
        self.data_store.setdefault('scene_history', [])
        self.data_store.setdefault('event_log', [])
        self.data_store.setdefault('current_scene_data', {})

        print(f"GWHR: Initialized/Merged with world data. World Title: '{self.data_store.get('world_title', 'N/A')}'")
        print(f"GWHR: Player state attributes: {self.data_store.get('player_state', {}).get('attributes')}")

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
                    'num_interactive_elements': len(new_scene_data.get('interactive_elements', [])) # New
                }
                scene_history.append(scene_summary)
                updated_keys.append(key)
            elif key == 'current_game_time': # Make sure game time is not deepcopied if it's just an int
                 self.data_store[key] = value
                 updated_keys.append(key)
            else:
                # Deepcopy other updates for safety
                self.data_store[key] = copy.deepcopy(value)
                updated_keys.append(key)

        if updated_keys:
             print(f"GWHR: State updated for keys: {updated_keys}. (Simulated deep merge/logic).")
        else:
             print(f"GWHR: Update_state called with no keys to update or empty updates dictionary.")


    def get_current_context(self, granularity: str = "full", context_type: str = "general") -> dict:
        print("GWHR: get_current_context currently returns a full copy. This will be refined for targeted context provision.")
        # This is a placeholder. Real implementation would filter and structure
        # the context based on granularity and context_type.
        return copy.deepcopy(self.data_store) # Return a deep copy

    def get_data_store(self) -> dict:
        # Returns a deep copy of the entire data store
        return copy.deepcopy(self.data_store)
