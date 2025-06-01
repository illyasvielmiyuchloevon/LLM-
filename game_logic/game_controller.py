from api.api_key_manager import ApiKeyManager
from ui.ui_manager import UIManager
import json # For LLM response parsing
import time # For game loop delay
from api.api_key_manager import ApiKeyManager
from ui.ui_manager import UIManager
from engine.model_selector import ModelSelector
from engine.adventure_setup import AdventureSetup
from engine.gwhr import GWHR
from api.llm_interface import LLMInterface # Ensure LLMInterface is available for GameController to use directly or via other components

# GameEngine will be imported here later when needed

class GameController:
    def __init__(self, api_key_manager: ApiKeyManager, ui_manager: UIManager,
                 model_selector: ModelSelector, adventure_setup: AdventureSetup,
                 gwhr: GWHR, llm_interface: LLMInterface): # Added llm_interface
        self.api_key_manager = api_key_manager
        self.ui_manager = ui_manager
        self.model_selector = model_selector
        self.adventure_setup = adventure_setup
        self.gwhr = gwhr
        self.llm_interface = llm_interface # Store LLMInterface
        self.current_game_state: str = "INIT"
        # self.game_engine will be initialized later

    def request_and_validate_api_key(self) -> bool:
        self.ui_manager.show_api_key_screen()
        # In a real application, ui_manager.get_api_key_input() would be called.
        # For now, we simulate input() directly here.
        # This will require manual input when testing with run_in_bash_session
        # In a real app, self.ui_manager.get_api_key_input() or similar would be called.
        key_input = input() # Simulating direct input for API key
        self.api_key_manager.store_api_key(key_input)
        is_valid = self.api_key_manager.validate_api_key()

        if is_valid:
            self.ui_manager.display_message("API Key validated successfully.", "info")
        else:
            self.ui_manager.display_message("API Key validation failed.", "error")

        return is_valid

    def select_model_flow(self) -> bool:
        models = self.model_selector.fetch_available_models()
        if models:
            selected_model_id = self.ui_manager.show_model_selection_screen(models)
            if selected_model_id:
                self.model_selector.set_selected_model(selected_model_id)
                self.ui_manager.display_message(f"GameController: Model selected - {selected_model_id}", "info")
                return True
            else:
                self.ui_manager.display_message("GameController: No model was selected by the user.", "warning")
                return False
        else:
            self.ui_manager.display_message("GameController: Could not fetch any models to select from.", "error")
            return False

    def request_adventure_preferences_flow(self) -> str | None:
        # AdventureSetup.request_adventure_preference now calls UIManager.show_adventure_preference_screen
        # and also calls its own store_preference method if input is valid.
        preference_text = self.adventure_setup.request_adventure_preference()

        if preference_text:
            # Display a snippet in GameController's log
            snippet = preference_text[:50] + "..." if len(preference_text) > 50 else preference_text
            self.ui_manager.display_message(f"GameController: Adventure preference captured - '{snippet}'", "info")
            return preference_text
        else:
            self.ui_manager.display_message("GameController: No adventure preference was provided.", "warning")
            return None

    def generate_blueprint_flow(self) -> bool:
        self.ui_manager.display_message("GameController: Starting detailed world blueprint generation process...", "info")
        blueprint_text = self.adventure_setup.generate_detailed_world_blueprint()

        if blueprint_text:
            self.ui_manager.display_message("GameController: Detailed world blueprint generated successfully.", "info")
            # Displaying a snippet for confirmation
            self.ui_manager.display_message(f"GameController: Blueprint Preview (first 100 chars): {blueprint_text[:100]}...", "info")
            return True
        else:
            self.ui_manager.display_message("GameController: Detailed world blueprint generation failed.", "error")
            return False

    def initialize_world_from_blueprint_flow(self) -> bool:
        self.ui_manager.display_message("GameController: Starting World Conception Document generation and GWHR initialization...", "info")
        world_data_dict = self.adventure_setup.generate_initial_world()

        if world_data_dict:
            self.ui_manager.display_message("GameController: World Conception Document generated and parsed successfully.", "info")
            self.gwhr.initialize(world_data_dict) # GWHR will print its own confirmation

            # Verify by fetching title from GWHR
            retrieved_title = self.gwhr.get_data_store().get('world_title', 'N/A')
            self.ui_manager.display_message(f"GameController: GWHR has been initialized. World Title from GWHR: '{retrieved_title}'.", "info")
            return True
        else:
            # adventure_setup.generate_initial_world() would have already printed detailed error
            self.ui_manager.display_message("GameController: Failed to generate or parse World Conception Document. GWHR not initialized.", "error")
            return False

    def advance_time(self, duration: int = 1):
        current_time = self.gwhr.data_store.get('current_game_time', 0)
        new_time = current_time + duration
        # GWHR's update_state handles deepcopy if needed for other complex states,
        # but for simple int like game_time, direct assignment is fine.
        # However, to use the GWHR's logging and unified update path:
        self.gwhr.update_state({'current_game_time': new_time})
        # log_event is now part of GWHR, which uses its internal current_game_time
        # self.gwhr.log_event(f"Time advanced by {duration}. New time: {new_time}", event_type="time_advance")
        # The update_state for current_game_time should ideally log this, or we log it here.
        # For now, GWHR's update_state doesn't log individual key changes.
        # Let's assume for now direct logging is okay if update_state itself isn't verbose enough.
        # Decision: Let GWHR handle all direct data_store changes.
        # If advance_time is a conceptual game event, it should be logged as such.
        # The GWHR update_state for current_game_time already prints "State updated for keys: ['current_game_time']"
        # We can add a specific event log for time advancement if desired.
        # For now, the update_state log is sufficient.

    def validate_and_get_action_id(self, command: str, choices: list) -> str | None:
        try:
            choice_num = int(command)
            if 1 <= choice_num <= len(choices):
                selected_0_based_index = choice_num - 1
                # Ensure the choice dictionary itself and its 'id' key exist
                if isinstance(choices[selected_0_based_index], dict) and 'id' in choices[selected_0_based_index]:
                    return choices[selected_0_based_index].get('id')
                else:
                    # This case should ideally not happen if choices are well-formed by LLM
                    self.ui_manager.display_message(f"Error: Choice format incorrect for command '{command}'. No ID found.", "error")
                    return None
            else:
                # Error message for out-of-range will be handled by the calling context (game_loop)
                return None
        except ValueError:
            # Error message for non-numeric will be handled by the calling context (game_loop)
            return None

    def handle_game_menu(self):
        player_state = self.gwhr.get_data_store().get('player_state', {})
        while True:
            menu_action_result = self.ui_manager.show_game_systems_menu(player_state)
            if menu_action_result == 'close_menu':
                break
            # elif menu_action_result == 'show_menu_again':
            #     continue # Loop continues by default
            # No other actions from this menu result in direct game state changes yet

    def initiate_scene(self, scene_id: str) -> bool:
        self.current_game_state = "PRESENTING_SCENE"
        self.ui_manager.display_message(f"GameController: Loading scene '{scene_id}'...", "info")
        self.gwhr.log_event(f"Initiating scene: {scene_id}", event_type="scene_load")

        # Get context (currently full dump, will be refined)
        context_for_llm = self.gwhr.get_current_context()

        # Limit context size for prompt (example: take first 1000 chars of JSON string)
        context_json_str = json.dumps(context_for_llm, indent=2)
        truncated_context_str = context_json_str[:1000]
        if len(context_json_str) > 1000:
            truncated_context_str += "\n... (context truncated)"

        prompt = (
            f"Current Game Context (JSON):\n{truncated_context_str}\n\n"
            f"Requested Scene ID: {scene_id}\n\n"
            "Task: Generate the scene description, NPCs, interactive elements, and environmental effects for the scene "
            "specified by 'Requested Scene ID'. Ensure the output is a single valid JSON object adhering to the "
            "established scene data structure. The 'scene_id' in your response should match the 'Requested Scene ID'."
        )

        model_id = self.model_selector.get_selected_model()
        if not model_id:
            self.ui_manager.display_message("GameController: CRITICAL - No model selected for LLM call during scene initiation.", "error")
            self.current_game_state = "GAME_OVER"
            return False

        scene_json_str = self.llm_interface.generate(prompt, model_id, expected_response_type='scene_description')

        if scene_json_str:
            try:
                scene_data = json.loads(scene_json_str)
                # Validate if LLM followed instructions for scene_id
                if scene_data.get('scene_id') != scene_id:
                    self.ui_manager.display_message(
                        f"LLM Warning: Returned scene_id '{scene_data.get('scene_id')}' "
                        f"does not match requested '{scene_id}'. Using requested ID.", "warning"
                    )
                    scene_data['scene_id'] = scene_id # Force consistency

                # --- Image Generation for new scene ---
                narrative_for_prompt = scene_data.get('narrative', '')
                npcs_for_prompt = ", ".join([npc.get('name', 'N/A') for npc in scene_data.get('npcs_in_scene', []) if npc.get('name')])
                image_prompt_text = f"Scene: {narrative_for_prompt[:150]}. NPCs: {npcs_for_prompt[:100]}."
                scene_data['image_prompt_elements'] = [image_prompt_text] # Store the generated prompt

                self.ui_manager.show_image_loading_indicator()
                image_url = self.llm_interface.generate_image(image_prompt_text)
                self.ui_manager.hide_image_loading_indicator()

                if image_url:
                    scene_data['background_image_url'] = image_url
                    self.ui_manager.display_message(f"GameController: Image generated for scene '{scene_data.get('scene_id', scene_id)}'. URL: {image_url}", "info")
                else:
                    scene_data['background_image_url'] = None
                    self.ui_manager.display_message(f"GameController: Failed to generate image for scene '{scene_data.get('scene_id', scene_id)}'.", "warning")
                # --- End Image Generation ---

                self.gwhr.update_state({'current_scene_data': scene_data}) # This also logs to scene_history
                self.ui_manager.display_scene(scene_data)
                self.current_game_state = "AWAITING_PLAYER_ACTION"
                return True
            except json.JSONDecodeError as e:
                self.ui_manager.display_message(f"GameController: Error parsing scene JSON from LLM: {e}. Response snippet: {scene_json_str[:200]}...", "error")
                self.current_game_state = "GAME_OVER" # Critical error
                return False
        else: # LLM returned None
            self.ui_manager.display_message(f"GameController: Failed to get scene data from LLM for scene '{scene_id}'.", "error")
            self.current_game_state = "GAME_OVER" # Critical if first scene fails
            return False

    def process_player_action(self, action_type: str, action_detail: any):
        self.current_game_state = "PROCESSING_ACTION"
        self.ui_manager.display_message(f"GameController: Processing action: {action_type} on '{action_detail}'...", "info")
        self.gwhr.log_event(f"Player action: {action_type} on element '{action_detail}'", event_type="player_action")

        self.advance_time(1) # Advance game time by 1 unit

        context_for_llm = self.gwhr.get_current_context()
        current_scene_id_from_gwhr = context_for_llm.get('current_scene_data', {}).get('scene_id', 'UNKNOWN_SCENE')

        context_json_str = json.dumps(context_for_llm, indent=2)
        truncated_context_str = context_json_str[:1000]
        if len(context_json_str) > 1000:
            truncated_context_str += "\n... (context truncated)"

        # New prompt structure for process_player_action
        current_scene_elements = context_for_llm.get('current_scene_data', {}).get('interactive_elements', [])
        chosen_element_info = next((el for el in current_scene_elements if el.get('id') == action_detail), None)
        chosen_element_name = chosen_element_info.get('name', action_detail) if chosen_element_info else action_detail

        prompt = (
            f"Current Game Context (JSON):\n{truncated_context_str}\n\n"
            f"Player selected the option '{chosen_element_name}' (ID: '{action_detail}') from the interaction menu in scene '{current_scene_id_from_gwhr}'.\n\n"
            f"Task: Generate the outcome of this specific interaction. This might mean updating the current scene (e.g., a narrative update, changed NPC status, modified/new interactive elements) or transitioning to a new scene. "
            f"If transitioning to a new scene, provide the full data for the new scene, including a new 'scene_id' which MUST be different from '{current_scene_id_from_gwhr}'. "
            f"If updating the current scene, the response can omit 'scene_id' or use the current one ('{current_scene_id_from_gwhr}'), but should detail changes, potentially including a 'narrative_update' field. "
            f"Ensure the output is a single valid JSON object structured as scene data."
        )

        model_id = self.model_selector.get_selected_model()
        if not model_id:
            self.ui_manager.display_message("GameController: CRITICAL - No model selected for LLM call during action processing.", "error")
            self.current_game_state = "GAME_OVER" # Or AWAITING_PLAYER_ACTION to allow recovery if possible
            return

        response_json_str = self.llm_interface.generate(prompt, model_id, expected_response_type='scene_description') # Re-using scene_description type

        if response_json_str:
            try:
                response_data = json.loads(response_json_str)
                new_scene_id = response_data.get('scene_id')


                # --- Image Generation for action outcome scene data ---
                narrative_for_prompt_action = response_data.get('narrative', '')
                npcs_for_prompt_action = ", ".join([npc.get('name', 'N/A') for npc in response_data.get('npcs_in_scene', []) if npc.get('name')])
                image_prompt_text_action = f"Scene after action: {narrative_for_prompt_action[:150]}. NPCs: {npcs_for_prompt_action[:100]}."
                response_data['image_prompt_elements'] = [image_prompt_text_action]

                self.ui_manager.show_image_loading_indicator()
                image_url_action = self.llm_interface.generate_image(image_prompt_text_action)
                self.ui_manager.hide_image_loading_indicator()

                if image_url_action:
                    response_data['background_image_url'] = image_url_action
                    self.ui_manager.display_message(f"GameController: Image updated/generated for scene '{response_data.get('scene_id')}'. URL: {image_url_action}", "info")
                else:
                    response_data['background_image_url'] = None
                    self.ui_manager.display_message(f"GameController: Failed to update/generate image for scene '{response_data.get('scene_id')}'.", "warning")
                # --- End Image Generation for action outcome ---

                if new_scene_id and new_scene_id != current_scene_id_from_gwhr: # LLM decided to change scene
                    self.ui_manager.display_message(f"GameController: Transitioning to new scene: {new_scene_id}", "info")
                    self.gwhr.update_state({'current_scene_data': response_data})
                    self.ui_manager.display_scene(response_data)
                elif new_scene_id == current_scene_id_from_gwhr and response_data.get('narrative'): # Update to current scene (full refresh)
                    self.ui_manager.display_message(f"GameController: Current scene '{current_scene_id_from_gwhr}' updated.", "info")
                    self.gwhr.update_state({'current_scene_data': response_data})
                    self.ui_manager.display_scene(response_data) # Display the updated scene
                elif response_data.get('narrative_update'): # A specific narrative update for current scene
                    # This path might need more fleshing out if LLM is expected to send *only* narrative_update
                    # and not a full scene. The image logic above assumes response_data is the new full scene data.
                    # If it's just a delta, image wouldn't typically change unless also in delta.
                    self.ui_manager.display_narrative(response_data.get('narrative_update',''))
                    # If only narrative_update, current_scene_data in GWHR is not updated with response_data here.
                    # This means the image displayed would be the old one. This might be desired.
                    # For now, we assume LLM sends full scene data if image is to change.
                else: # Fallback or unrecognized partial update
                    self.ui_manager.display_message("GameController: Action resulted in a minor or unclear update. Re-displaying current scene context.", "info")
                    self.ui_manager.display_scene(self.gwhr.get_data_store().get('current_scene_data', {}))

                # --- Player Growth/Update Processing ---
                if 'player_updates' in response_data:
                    updates_to_log = []
                    # Get a mutable copy of player_state from GWHR to modify
                    # Note: get_data_store() returns a deepcopy, so we're modifying a copy.
                    # We need to explicitly save it back to GWHR if changes are made.
                    # A more direct approach might be: player_state_ref = self.gwhr.data_store['player_state']
                    # But to respect GWHR's interface providing copies, let's get, modify, then update.
                    current_player_state_copy = self.gwhr.get_data_store().get('player_state', {})
                    player_state_modified = False

                    # Process attribute updates
                    if 'attributes' in response_data['player_updates']:
                        attributes_updates = response_data['player_updates']['attributes']
                        if isinstance(attributes_updates, dict):
                            player_attributes = current_player_state_copy.setdefault('attributes', {})
                            for attr, change in attributes_updates.items():
                                if attr in player_attributes: # Only update existing attributes
                                    current_value = player_attributes[attr]
                                    try:
                                        new_value = current_value # Default if change is invalid
                                        if isinstance(change, str):
                                            if change.startswith('+'):
                                                new_value = current_value + int(change[1:])
                                            elif change.startswith('-'):
                                                new_value = current_value - int(change[1:])
                                            else: # Absolute value
                                                new_value = int(change)
                                        elif isinstance(change, (int, float)): # Absolute value
                                            new_value = int(change) # cast to int just in case
                                        else:
                                            self.ui_manager.display_message(f"Warning: Unrecognized attribute change format for {attr}: {change}", "warning")
                                            continue

                                        player_attributes[attr] = new_value
                                        player_state_modified = True
                                        update_msg = f"Attribute {attr} changed from {current_value} to {new_value}."
                                        self.ui_manager.display_message(update_msg, "growth")
                                        updates_to_log.append(update_msg)
                                    except ValueError:
                                        self.ui_manager.display_message(f"Warning: Invalid value for attribute change {attr}: {change}", "warning")
                                else:
                                    self.ui_manager.display_message(f"Warning: Attempt to update unknown attribute {attr}.", "warning")
                        else:
                            self.ui_manager.display_message(f"Warning: Malformed 'attributes' in player_updates (not a dict): {attributes_updates}", "warning")

                    # Process skill updates
                    if 'skills_learned' in response_data['player_updates']:
                        skills_to_learn_list = response_data['player_updates']['skills_learned']
                        if isinstance(skills_to_learn_list, list):
                            player_skills = current_player_state_copy.setdefault('skills', [])
                            for skill_to_learn in skills_to_learn_list:
                                if isinstance(skill_to_learn, dict) and 'name' in skill_to_learn:
                                    existing_skill = next((s for s in player_skills if s.get('name') == skill_to_learn['name']), None)
                                    if not existing_skill:
                                        # Ensure default level if not provided
                                        skill_to_learn.setdefault('level', 1)
                                        player_skills.append(skill_to_learn) # skill_to_learn is a dict
                                        player_state_modified = True
                                        update_msg = f"New skill learned: {skill_to_learn['name']} (Level {skill_to_learn.get('level', 1)})!"
                                        self.ui_manager.display_message(update_msg, "growth")
                                        updates_to_log.append(update_msg)
                                else:
                                    self.ui_manager.display_message(f"Warning: Malformed skill_learned entry: {skill_to_learn}", "warning")
                        else:
                             self.ui_manager.display_message(f"Warning: Malformed 'skills_learned' in player_updates (not a list): {skills_to_learn_list}", "warning")

                    # Process inventory updates
                    if 'inventory_updates' in response_data['player_updates']:
                        inventory_changes = response_data['player_updates']['inventory_updates']
                        if isinstance(inventory_changes, dict):
                            player_inventory = current_player_state_copy.setdefault('inventory', [])
                            if 'add' in inventory_changes and isinstance(inventory_changes['add'], list):
                                for item_to_add in inventory_changes['add']:
                                    if isinstance(item_to_add, dict) and 'id' in item_to_add and 'name' in item_to_add and 'quantity' in item_to_add:
                                        existing_item = next((item for item in player_inventory if item.get('id') == item_to_add['id']), None)
                                        if existing_item:
                                            existing_item['quantity'] = existing_item.get('quantity', 0) + item_to_add['quantity']
                                        else:
                                            player_inventory.append(item_to_add) # item_to_add is a dict
                                        player_state_modified = True
                                        update_msg = f"Obtained: {item_to_add['name']} (x{item_to_add['quantity']})."
                                        self.ui_manager.display_message(update_msg, "growth")
                                        updates_to_log.append(update_msg)
                                    else:
                                        self.ui_manager.display_message(f"Warning: Malformed item_to_add entry: {item_to_add}", "warning")
                            # TODO: Implement 'remove' logic similarly if needed
                            # if 'remove' in inventory_changes ...
                        else:
                            self.ui_manager.display_message(f"Warning: Malformed 'inventory_updates' in player_updates (not a dict): {inventory_changes}", "warning")

                    if player_state_modified and updates_to_log: # Only update GWHR if actual changes happened
                        self.gwhr.update_state({'player_state': current_player_state_copy})
                        self.gwhr.log_event(f"Player growth/update: {'; '.join(updates_to_log)}", event_type="player_update")
                # --- End Player Growth/Update Processing ---

                self.current_game_state = "AWAITING_PLAYER_ACTION"
            except json.JSONDecodeError as e:
                self.ui_manager.display_message(f"GameController: Error parsing action response JSON from LLM: {e}. Response snippet: {response_json_str[:200]}...", "error")
                self.current_game_state = "AWAITING_PLAYER_ACTION" # Allow player to try again
        else: # LLM returned None
            self.ui_manager.display_message("GameController: Failed to get action response from LLM.", "error")
            self.current_game_state = "AWAITING_PLAYER_ACTION" # Allow player to try again

    def game_loop(self):
        self.ui_manager.display_message("GameController: Entering game loop.", "info")
        while self.current_game_state != "GAME_OVER":
            if self.current_game_state == "AWAITING_PLAYER_ACTION":
                current_scene_data = self.gwhr.get_data_store().get('current_scene_data', {})
                interactive_choices = current_scene_data.get('interactive_elements', [])

                # Display scene first, which now includes the (M) Game Menu hint
                self.ui_manager.display_scene(current_scene_data)

                if not interactive_choices: # Check after display_scene, as scene might say "no actions"
                    self.ui_manager.display_message("No interactive actions presented by the scene. The story might require a different approach or this path ends here.", "info")
                    self.current_game_state = "GAME_OVER" # Or some other state if game can continue without choices
                    self.gwhr.log_event("Game ended: No interactive choices available in scene.", event_type="game_flow_end")
                    break

                raw_command = input("Your command (e.g., 1, 2, ..., or M for Menu): ").strip().lower()

                if raw_command == 'm':
                    self.handle_game_menu()
                    self.ui_manager.display_message("\n--- Returning to game ---", "info")
                    # Re-display current scene after menu closes to refresh context for player
                    refreshed_scene_data = self.gwhr.get_data_store().get('current_scene_data', {})
                    # self.ui_manager.display_scene(refreshed_scene_data) # This would re-print the menu hint.
                    # The loop will re-enter AWAITING_PLAYER_ACTION and call display_scene.
                    # So, no explicit re-display here is needed, just let the loop continue.
                    continue # Continue to next iteration of game_loop to re-evaluate state and display scene
                else:
                    action_id = self.validate_and_get_action_id(raw_command, interactive_choices)
                    if action_id:
                        self.process_player_action(action_type="interact_element", action_detail=action_id)
                    else:
                        self.ui_manager.display_message(f"Invalid command: '{raw_command}'. Please enter a valid action number or 'M' for the menu.", "error")
                        # Game state remains AWAITING_PLAYER_ACTION, loop will re-prompt after re-displaying scene.

            elif self.current_game_state == "GAME_OVER":
                break

            # Small delay to prevent tight loop if states are rapidly changing without blocking input
            # also makes game feel a bit more paced if LLM responses were instant.
            time.sleep(0.1)

        self.ui_manager.display_message("GameController: Exited game loop.", "info")
        if self.current_game_state == "GAME_OVER":
             self.ui_manager.display_message("Game Over.", "info")


    def start_game(self):
        self.ui_manager.display_message("GameController: Starting game setup...", "info")
        self.gwhr.log_event("Game started by GameController.", event_type="game_flow_start")
        self.current_game_state = "INIT" # Reset state

        # Determine initial scene ID.
        # For now, using a placeholder or a value potentially set in WCD.
        # The WCD from LLMInterface mock has "initial_plot_hook" but not a direct scene_id.
        # Let's assume a convention or add it to WCD later. For now, fixed ID.
        initial_scene_id_from_wcd = self.gwhr.get_data_store().get('initial_scene_id', 'scene_01_start')

        if self.initiate_scene(initial_scene_id_from_wcd):
            self.game_loop()
        else:
            self.ui_manager.display_message("GameController: Failed to initiate the first scene. Cannot start game.", "error")
            self.current_game_state = "GAME_OVER"
            # Log this specific failure
            self.gwhr.log_event(f"Game start failed: Could not initiate scene '{initial_scene_id_from_wcd}'.", event_type="game_flow_error")

        if self.current_game_state == "GAME_OVER":
             self.ui_manager.display_message("Game Over.", "info") # Ensure game over is messaged if loop not entered.
