import copy

class GWHR: # GameWorldHistoryRecorder
    def __init__(self):
        self.data_store: dict = {
            'current_game_time': 0,
            'scene_history': [],
            'event_log': [],
            'current_scene_data': {}
        }

    def initialize(self, initial_world_data: dict):
        # Start with a fresh set of defaults for GWHR-specific keys
        self.data_store = {
            'current_game_time': 0,
            'scene_history': [],
            'event_log': [],
            'current_scene_data': {}
        }
        # Then, deepcopy and update with initial_world_data.
        # This ensures initial_world_data overwrites any common keys (like 'world_title')
        # but GWHR specific keys are preserved if not in initial_world_data.
        current_store = copy.deepcopy(initial_world_data)

        # Ensure GWHR specific keys are present, using setdefault for those not typically in WCD
        current_store.setdefault('current_game_time', self.data_store['current_game_time'])
        current_store.setdefault('scene_history', list(self.data_store['scene_history'])) # ensure list copy
        current_store.setdefault('event_log', list(self.data_store['event_log'])) # ensure list copy
        current_store.setdefault('current_scene_data', dict(self.data_store['current_scene_data'])) # ensure dict copy

        self.data_store = current_store

        print(f"GWHR: Initialized. World Title: '{self.data_store.get('world_title', 'N/A')}'. Game Time: {self.data_store.get('current_game_time')}.")

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
                    'image_url': new_scene_data.get('background_image_url'), # New
                    'image_prompt_elements': new_scene_data.get('image_prompt_elements') # New
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
