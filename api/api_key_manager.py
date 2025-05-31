class ApiKeyManager:
    def __init__(self):
        self.api_key: str | None = None

    def request_api_key(self):
        print("UI: Please enter your API Key: ")

    def store_api_key(self, api_key: str):
        self.api_key = api_key

    def validate_api_key(self) -> bool:
        print("ApiKeyManager: Validating API Key...")
        if self.api_key and self.api_key.strip():
            print("ApiKeyManager: API Key is valid (simulated).")
            return True
        else:
            print("ApiKeyManager: API Key is invalid (simulated).")
            return False

    def get_api_key(self) -> str | None:
        return self.api_key
