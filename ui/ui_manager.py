class UIManager:
    def __init__(self):
        self.current_background_image_url: str | None = None

    def show_image_loading_indicator(self):
        print("\n[UI IMAGE]: --- Loading scene image ---")

    def hide_image_loading_indicator(self):
        print("[UI IMAGE]: --- Image loading attempt complete ---")

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
        print("\n" + "="*20 + " SCENE START " + "="*20 + "\n")

        # --- Image Part ---
        new_image_url = scene_data.get('background_image_url')
        if new_image_url:
            self.current_background_image_url = new_image_url
            print("="*15 + " SCENE IMAGE " + "="*15)
            print(f"[UI IMAGE]: Displaying image from: {self.current_background_image_url}")
            print("[UI IMAGE]: (Imagine a beautiful, contextually relevant image is displayed here, setting the scene visually.)")
            print("="*45 + "\n")
        elif self.current_background_image_url: # No new image, but there was an old one
            print("\n[UI IMAGE]: (Previous scene image fades or is removed. No new image for this view.)\n")
            self.current_background_image_url = None
        # If no new_image_url and no self.current_background_image_url, print nothing for image.

        # --- Textual Content Part ---
        print("--- SCENE DETAILS ---\n")

        narrative = scene_data.get('narrative', 'No narrative provided for this scene.')
        print(f"Narrative: {narrative}") # Added "Narrative: " prefix for clarity

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
        print("\n--- What do you do? ---") # This header will be part of display_interaction_menu or its alternative
        if interactive_elements: # Check if the list exists and is not empty
            self.display_interaction_menu(interactive_elements)
        else:
            # Print("\n--- ACTIONS ---") # Replaced by display_interaction_menu's handling or a generic message
            print("No specific actions seem possible right now.") # Fallback if no elements

        self.show_game_systems_menu_button() # Called at the end of scene display
        print("\n" + "="*20 + " SCENE END " + "="*20 + "\n")

    def display_interaction_menu(self, interactive_elements: list):
        print("\n--- INTERACTION MENU ---")
        if not interactive_elements or not isinstance(interactive_elements, list):
            print("No specific interactions currently available.")
            return

        for i, element in enumerate(interactive_elements):
            # Use 'name' for display, fallback to 'id', then to a generic message
            display_name = element.get('name', element.get('id', 'Unknown Interaction'))
            print(f"  {i+1}. {display_name}")

    def show_game_systems_menu_button(self):
        print("\n" + "-"*10 + "[ (M) Game Menu ]" + "-"*10)

    def display_character_status_screen(self, player_data: dict):
        print("\n" + "="*15 + " CHARACTER STATUS " + "="*15 + "\n")

        attributes = player_data.get('attributes', {})
        print("--- Attributes ---")
        print(f"  Strength:     {attributes.get('strength', 'N/A')}")
        print(f"  Dexterity:    {attributes.get('dexterity', 'N/A')}")
        print(f"  Intelligence: {attributes.get('intelligence', 'N/A')}")
        print(f"  Sanity:       {attributes.get('sanity', 'N/A')}")
        print(f"  Willpower:    {attributes.get('willpower', 'N/A')}")
        print(f"  Insight:      {attributes.get('insight', 'N/A')}")

        skills = player_data.get('skills', [])
        print("\n--- Skills ---")
        if not skills:
            print("  (No skills learned yet)")
        else:
            for skill in skills:
                print(f"  - {skill.get('name', 'Unknown Skill')} (Lvl: {skill.get('level', 1)})")

        equipment = player_data.get('equipment_slots', {})
        inventory = player_data.get('inventory', []) # Needed to resolve item names
        print("\n--- Equipment ---")
        if not equipment:
            print("  (No equipment slots defined or all empty)")
        else:
            for slot, item_id_or_obj in equipment.items():
                item_name = "Empty"
                if item_id_or_obj:
                    # This simple lookup assumes inventory items have 'id' and 'name'.
                    # A more robust system would have an item manager or pass resolved item objects.
                    found_item = next((item for item in inventory if item.get('id') == item_id_or_obj), None)
                    if found_item:
                        item_name = found_item.get('name', str(item_id_or_obj))
                    else: # If it's an object already (not planned yet but for robustness) or ID not found
                        item_name = str(item_id_or_obj) if not isinstance(item_id_or_obj, dict) else item_id_or_obj.get('name', 'Unknown Equipped Item')
                print(f"  {slot.capitalize()}: {item_name}")

        print(f"\nLocation: {player_data.get('current_location_id', 'Unknown')}")
        print("\n" + "="*48)
        input("--- Press Enter to close ---")

    def display_inventory_screen(self, inventory_list: list):
        print("\n" + "="*15 + " INVENTORY " + "="*15 + "\n")
        if not inventory_list:
            print("  (Inventory is empty)")
        else:
            for item in inventory_list:
                print(f"  - {item.get('name', 'Unknown Item')} (Qty: {item.get('quantity', 1)})")
                if item.get('description'):
                    print(f"    '{item.get('description')}'")
        print("\n" + "="*39)
        input("--- Press Enter to close ---")

    def display_equipment_screen(self, equipment_slots: dict, inventory_list: list):
        print("\n" + "="*15 + " EQUIPMENT " + "="*15 + "\n")
        if not equipment_slots:
            print("  (No equipment slots defined)")
        else:
            for slot, item_id_or_obj in equipment_slots.items():
                item_name = "Empty"
                if item_id_or_obj:
                    found_item = next((item for item in inventory_list if item.get('id') == item_id_or_obj), None)
                    if found_item:
                        item_name = found_item.get('name', str(item_id_or_obj))
                    else:
                        item_name = str(item_id_or_obj) if not isinstance(item_id_or_obj, dict) else item_id_or_obj.get('name', 'Unknown Equipped Item')
                print(f"  {slot.capitalize()}: {item_name}")
        print("\n" + "="*41)
        input("--- Press Enter to close ---")

    def show_game_systems_menu(self, player_state_data: dict) -> str:
        print("\n" + "="*15 + " GAME MENU " + "="*15 + "\n")
        print("  1. Character Status")
        print("  2. Inventory")
        print("  3. Equipment")
        print("  0. Close Menu")

        choice = input("Select an option: ").strip()

        if choice == '1':
            self.display_character_status_screen(player_state_data)
            return 'show_menu_again'
        elif choice == '2':
            inventory = player_state_data.get('inventory', [])
            self.display_inventory_screen(inventory)
            return 'show_menu_again'
        elif choice == '3':
            equipment_slots = player_state_data.get('equipment_slots', {})
            inventory = player_state_data.get('inventory', []) # For name resolution
            self.display_equipment_screen(equipment_slots, inventory)
            return 'show_menu_again'
        elif choice == '0':
            return 'close_menu'
        else:
            self.display_message("Invalid option, please try again.", "error") # Uses existing method
            return 'show_menu_again'

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
