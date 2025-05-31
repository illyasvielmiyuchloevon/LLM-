class UIManager:
    def show_api_key_screen(self):
        print("UI: Please enter your API Key: ")

    def display_message(self, message: str, message_type: str = "info"):
        print(f"[{message_type.upper()}] {message}")

    def show_model_selection_screen(self, models: list[str]) -> str | None:
        print("UI: Available Models:")
        if not models:
            print("UI: No models available for selection.")
            return None

        for i, model_name in enumerate(models):
            print(f"  {i+1}: {model_name}")

        choice = input("UI: Select a model by number (or press Enter to skip): ")

        if not choice:
            print("UI: No model selected.")
            return None

        try:
            choice_num = int(choice)
            if 1 <= choice_num <= len(models):
                return models[choice_num - 1]
            else:
                print("UI: Invalid selection (out of range).")
                return None
        except ValueError:
            print("UI: Invalid selection (not a number).")
            return None

    def show_adventure_preference_screen(self) -> str:
        preference = input("UI: Describe your desired adventure theme/setting: ")
        return preference.strip()
