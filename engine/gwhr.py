import copy

class GWHR: # GameWorldHistoryRecorder
    def __init__(self):
        self.data_store: dict = {}

    def initialize(self, initial_world_data: dict):
        # Perform a deep copy to ensure the internal data_store is independent
        self.data_store = copy.deepcopy(initial_world_data)
        # Using UIManager would be better, but print is fine for now.
        print(f"GWHR: Initialized with world data. World Title: '{self.data_store.get('world_title', 'N/A')}'")

    def update_state(self, updates: dict):
        # This is a placeholder. Real implementation might involve more complex merge logic,
        # conflict resolution, or specific handlers based on update types.
        # For now, a simple dictionary update. A deep copy of updates might be safer.
        # self.data_store.update(copy.deepcopy(updates))

        # For a potentially nested dictionary, a proper deep merge would be better.
        # For this phase, a shallow update is acceptable as per plan.
        # However, let's at least iterate and update to simulate a bit more care.
        for key, value in updates.items():
            # A real system might have specific handlers or deep merge for nested dicts
            self.data_store[key] = copy.deepcopy(value) # Deepcopy individual updates for safety

        print(f"GWHR: State updated with keys: {list(updates.keys())}. (Simulated deep merge/logic).")

    def get_current_context(self, granularity: str = "full", context_type: str = "general") -> dict:
        # This is a placeholder. Real implementation would filter and structure
        # the context based on granularity and context_type.
        print(f"GWHR: Getting current context (granularity: {granularity}, type: {context_type}). Returning full data store copy for now.")
        return copy.deepcopy(self.data_store) # Return a deep copy

    def get_data_store(self) -> dict:
        # Returns a deep copy of the entire data store
        return copy.deepcopy(self.data_store)
