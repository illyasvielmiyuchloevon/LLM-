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

    def display_scene(self, scene_data: dict):
        print("\n" + "="*20 + " SCENE " + "="*20 + "\n")

        narrative = scene_data.get('narrative', 'No narrative provided for this scene.')
        print(narrative)

        npcs_in_scene = scene_data.get('npcs_in_scene')
        if npcs_in_scene:
            print("\n--- NPCs Present ---")
            for npc in npcs_in_scene:
                status = f" ({npc.get('status', 'standing by')})" if npc.get('status') else ""
                dialogue_hook = f" Might say: \"{npc.get('dialogue_hook', '')}\"" if npc.get('dialogue_hook') else ""
                print(f"- {npc.get('name', 'Unknown NPC')}{status}{dialogue_hook}")

        environmental_effects = scene_data.get('environmental_effects')
        if environmental_effects:
            print("\n--- Environment ---")
            print(environmental_effects)

        interactive_elements = scene_data.get('interactive_elements', [])
        print("\n--- What do you do? ---")
        if not interactive_elements:
            print("There are no obvious actions to take.")
        else:
            for i, choice in enumerate(interactive_elements):
                print(f"  {i+1}. {choice.get('description', 'No description')} (ID: {choice.get('id', 'no_id')})")
        print("="*50 + "\n") # End of scene separator

    def display_narrative(self, text: str):
        print("\n" + "-"*10 + " NARRATIVE UPDATE " + "-"*10 + "\n")
        print(text)
        print("-"*(30 + len("NARRATIVE UPDATE")) + "\n")


    def get_player_action(self, choices: list) -> str | None:
        if not choices:
            print("No choices available to select from.")
            return None

        prompt_message = "Choose an action by number (1-{}): ".format(len(choices))

        while True:
            action_input = input(prompt_message).strip()
            try:
                selected_index = int(action_input) - 1
                if 0 <= selected_index < len(choices):
                    # Ensure the choice dictionary itself and its 'id' key exist
                    if isinstance(choices[selected_index], dict) and 'id' in choices[selected_index]:
                        return choices[selected_index].get('id')
                    else:
                        # This case should ideally not happen if choices are well-formed
                        print("Error: Choice format incorrect. No ID found.")
                        return None
                else:
                    print(f"Invalid choice. Please enter a number between 1 and {len(choices)}.")
            except ValueError:
                print("Invalid input. Please enter a number.")
