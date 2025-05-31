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
        else:
            # Generic mock response for other types
            mock_response = f"Mock LLM Response for {expected_response_type} using prompt (first 20 chars: '{prompt_str[:20]}...')."
            print(f"LLMInterface: Mock LLM call successful ({expected_response_type}).")
            return mock_response
