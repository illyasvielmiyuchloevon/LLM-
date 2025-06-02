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
        print("\n" + "="*41) # Length of " EQUIPMENT " + 2*15 + 2 = 11+30+2 = 43. Matches roughly.
        input("--- Press Enter to close ---")

    def display_codex_entry_content(self, entry_title: str, entry_content: str, entry_source_type: str, entry_source_detail: str):
        header = f"--- Codex: {entry_title} ---"
        print(f"\n{header}")
        print(f"Content: {entry_content}")
        print(f"Source: Discovered via {entry_source_type} from '{entry_source_detail}'.")
        print("-" * len(header))
        input("--- Press Enter to close entry ---")

    def display_knowledge_codex_ui(self, codex_entries: dict) -> tuple[str, str | None] | None:
        header = "="*15 + " KNOWLEDGE CODEX " + "="*15
        print(f"\n{header}\n")

        if not codex_entries or not isinstance(codex_entries, dict) or not codex_entries:
            print("  (No knowledge entries discovered yet.)")
            # Wait for input before returning to prevent instant loop if called from menu
            input("--- Press Enter to return to menu ---")
            return ('show_codex_again', None) # Or 'close_menu' depending on desired flow

        entries_list = list(codex_entries.values())
        for i, entry in enumerate(entries_list):
            print(f"  {i+1}. {entry.get('title', 'Untitled Entry')}")
        print("  0. Exit Codex")

        choice_str = input("\nSelect an entry to read (number) or 0 to exit: ").strip()

        try:
            choice_num = int(choice_str)
            if choice_num == 0:
                return ('exit_codex', None)
            elif 1 <= choice_num <= len(entries_list):
                selected_entry = entries_list[choice_num - 1]
                self.display_codex_entry_content(
                    selected_entry.get('title','N/A'),
                    selected_entry.get('content','N/A'),
                    selected_entry.get('source_type','N/A'),
                    selected_entry.get('source_detail','N/A')
                )
                return ('viewed_entry', selected_entry.get('knowledge_id'))
            else:
                self.display_message(f"Invalid selection. Please enter a number between 0 and {len(entries_list)}.", "error")
                return ('show_codex_again', None)
        except ValueError:
            self.display_message("Invalid input. Please enter a number.", "error")
            return ('show_codex_again', None)

    def display_dynamic_event_notification(self, event_description: str):
        print(f"\n[WORLD EVENT]: {event_description}\n")

    def show_game_systems_menu(self, player_state_data: dict) -> str:
        print("\n" + "="*15 + " GAME MENU " + "="*15 + "\n")
        print("  1. Character Status")
        print("  2. Inventory")
        print("  3. Equipment")
        print("  4. Knowledge Codex") # New Option
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
            inventory = player_state_data.get('inventory', [])
            self.display_equipment_screen(equipment_slots, inventory)
            return 'show_menu_again'
        elif choice == '4': # New case for Codex
            codex_data = player_state_data.get('knowledge_codex', {}) # Assumes codex is part of player_state or passed differently
                                                                    # Plan implies GameController gets it from GWHR and passes it.
                                                                    # For now, let's assume it's passed in player_state_data for simplicity,
                                                                    # or this method needs direct GWHR access or codex passed separately.
                                                                    # The goal says `show_game_systems_menu(self, player_state_data: dict)`
                                                                    # GWHR has codex at top level, not in player_state.
                                                                    # This method signature needs to be reconsidered or codex needs to be passed.
                                                                    # For now, I'll assume it's passed via player_state_data for the test.
            # Correct access would be: (assuming codex_data is passed as a separate arg or fetched by GC)
            # For this UIManager test, we'll assume it's within player_state_data for simplicity of the method call.
            # In GameController, it will fetch from gwhr.get_data_store()['knowledge_codex'] and pass it.
            # So, let's adjust show_game_systems_menu to accept codex_data directly.
            # NO, the plan says: show_game_systems_menu(self, player_state_data: dict)
            # This means GameController must put codex into player_state_data for this call, or UIManager needs GWHR.
            # Let's assume GameController will pass a richer player_state_data that includes a 'knowledge_codex' key.
            codex_entries = player_state_data.get('knowledge_codex_for_ui', {}) # Expect GC to put it here
            codex_action_result = self.display_knowledge_codex_ui(codex_entries)
            # display_knowledge_codex_ui will loop until 'exit_codex'
            return 'show_menu_again' # Always return to main game menu after codex closes
        elif choice == '0':
            return 'close_menu'
        else:
            self.display_message("Invalid option, please try again.", "error")
            return 'show_menu_again'

    def display_npc_dialogue(self, npc_name: str, dialogue_text: str, player_options: list = None):
        print(f"\n--- Dialogue: {npc_name} ---")
        print(f"{npc_name}: \"{dialogue_text}\"")

        if player_options and isinstance(player_options, list):
            print("\nYour reply options:")
            for i, option in enumerate(player_options):
                if isinstance(option, dict):
                    display_text = option.get('name', option.get('text', option.get('id', 'Unknown option')))
                    print(f"  {i+1}. {display_text}")
                else:
                    print(f"  {i+1}. (Malformed option: {option})") # Should not happen with good data
        # If no options, or not a list, just prints NPC dialogue. GameController would then decide what to do.
        # (e.g., proceed, or call get_free_text_input if that's the flow)

    def get_free_text_input(self, prompt_message: str) -> str:
        user_input = input(f"\n{prompt_message} ").strip()
        return user_input

    def show_combat_interface(self, player_hp: int, player_max_hp: int, combatants_info: list):
        print("\n" + "="*20 + " COMBAT " + "="*20 + "\n")
        print(f"Player HP: {player_hp}/{player_max_hp}")
        print("--- Opponents ---")
        if not combatants_info:
            print("  (No opponents visible or combat ended)")
        else:
            for npc_info in combatants_info:
                print(f"  - {npc_info.get('name', 'Unknown Combatant')} HP: {npc_info.get('hp', '?')}/{npc_info.get('max_hp', '?')}")
        # Note: Player actions/strategies will be displayed separately by present_combat_strategies

    def display_combat_narrative(self, text: str):
        print("\n--- Combat Action ---")
        print(text)

    def update_combatants_status(self, updates: list): # Placeholder
        print(f"[UI Placeholder: Combatant statuses updated: {updates}]")

    def present_combat_strategies(self, strategies: list) -> str | None:
        print("\n--- Choose Your Strategy ---")
        if not strategies or not isinstance(strategies, list): # Added type check for robustness
            print("No specific strategies available.")
            return None

        # display_interaction_menu might be too specific with its "INTERACTION MENU" header.
        # Re-implementing the list display here for "Choose Your Strategy" context.
        for i, strategy in enumerate(strategies):
            if isinstance(strategy, dict):
                display_name = strategy.get('name', strategy.get('id', 'Unnamed Strategy'))
                print(f"  {i+1}. {display_name}")
            else:
                print(f"  {i+1}. (Malformed strategy data: {strategy})")

        # Use existing get_player_action for selection logic
        return self.get_player_action(strategies)

    def show_combat_results(self, results_summary: str, victor: str | None): # victor can be None
        print("\n" + "="*15 + " COMBAT ENDED " + "="*15 + "\n")
        print(f"Outcome: {results_summary}")
        if victor == 'player':
            print("YOU ARE VICTORIOUS!")
        elif victor == 'npc': # Assuming generic NPC win
            print("You have been defeated.")
        elif victor == 'draw':
            print("The battle ends in a draw.")
        else: # Covers None or other unexpected victor strings
            print(f"Combat finished. Victor: {victor if victor else 'Undetermined'}")
        print("="*46) # Matches header length roughly
        input("\n--- Press Enter to continue ---")

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
