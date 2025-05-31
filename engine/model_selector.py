from api.api_key_manager import ApiKeyManager # Assumes execution from root or api in PYTHONPATH

class ModelSelector:
    def __init__(self, api_key_manager: ApiKeyManager):
        self.api_key_manager = api_key_manager
        self.selected_model_id: str | None = None

    def fetch_available_models(self) -> list[str]:
        api_key = self.api_key_manager.get_api_key()
        if not api_key:
            print("ModelSelector: Error - API Key not available.") # Later, use UIManager
            return []

        print("ModelSelector: Simulating Gemini API call to fetch available models...")
        # In a real scenario, this would involve an actual API call
        return ["gemini-2.5-pro-mock", "gemini-2.5-flash-mock"]

    def display_models(self, model_list: list[str]):
        print("ModelSelector: Available models:")
        if not model_list:
            print("- No models found or fetched.")
            return
        for model in model_list:
            print(f"- {model}")

    def set_selected_model(self, model_id: str):
        self.selected_model_id = model_id
        print(f"ModelSelector: Model set to {model_id}")

    def get_selected_model(self) -> str | None:
        return self.selected_model_id
