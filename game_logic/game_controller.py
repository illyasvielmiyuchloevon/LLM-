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

        prompt = (
            f"Current Game Context (JSON):\n{truncated_context_str}\n\n"
            f"Player Action: Interacted with element '{action_detail}' (type: {action_type}) in scene '{current_scene_id_from_gwhr}'.\n\n"
            "Task: Generate the outcome of this action. This might mean updating the current scene "
            "(e.g., a narrative update, changed NPC status, modified interactive elements) or transitioning to a new scene. "
            "If transitioning to a new scene, provide the full data for the new scene, and its 'scene_id' MUST be different "
            "from the current one ('{current_scene_id_from_gwhr}'). If it's an update to the current scene, "
            "the 'scene_id' in your response MUST be '{current_scene_id_from_gwhr}', and you should include fields that changed, "
            "or a 'narrative_update' field for minor text results. Output a single valid JSON object."
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

                if new_scene_id and new_scene_id != current_scene_id_from_gwhr: # LLM decided to change scene
                    self.ui_manager.display_message(f"GameController: Transitioning to new scene: {new_scene_id}", "info")
                    # self.initiate_scene(new_scene_id) # This would re-prompt LLM for the same scene.
                    # Instead, directly use the data LLM provided for the new scene.
                    self.gwhr.update_state({'current_scene_data': response_data})
                    self.ui_manager.display_scene(response_data)
                elif new_scene_id == current_scene_id_from_gwhr and response_data.get('narrative'): # Update to current scene (full refresh)
                    self.ui_manager.display_message(f"GameController: Current scene '{current_scene_id_from_gwhr}' updated.", "info")
                    self.gwhr.update_state({'current_scene_data': response_data})
                    self.ui_manager.display_scene(response_data) # Display the updated scene
                elif response_data.get('narrative_update'): # A specific narrative update for current scene
                    self.ui_manager.display_narrative(response_data.get('narrative_update',''))
                    # Potentially merge other small changes from response_data into current_scene_data here
                    # For now, just displaying the narrative update. A more complex merge might be needed.
                    # Example: self.gwhr.update_state({'current_scene_data': {'some_flag': True}}) # if LLM sends deltas
                else: # Fallback or unrecognized partial update
                    self.ui_manager.display_message("GameController: Action resulted in a minor or unclear update. Re-displaying current scene context.", "info")
                    self.ui_manager.display_scene(self.gwhr.get_data_store().get('current_scene_data', {}))

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
                choices = current_scene_data.get('interactive_elements', [])

                if not choices:
                    self.ui_manager.display_message("No interactive actions available in this scene. The story ends here for now.", "info")
                    self.current_game_state = "GAME_OVER"
                    # Potentially log this specific game end reason
                    self.gwhr.log_event("Game ended: No actions available.", event_type="game_flow_end")
                    break

                action_id = self.ui_manager.get_player_action(choices)
                if action_id:
                    self.process_player_action(action_type="interact_element", action_detail=action_id)
                else:
                    # This case implies get_player_action itself returned None,
                    # which happens if choices were empty (handled above) or malformed.
                    # Or if we implement a 'quit' or 'system' command there.
                    # For now, assume it means the input loop in get_player_action was broken by non-standard means
                    # or a malformed choice was processed.
                    self.ui_manager.display_message("GameController: No valid action processed from input. If you see choices, try again.", "warning")
                    # To prevent tight loop if get_player_action returns None without good reason:
                    # self.current_game_state = "GAME_OVER" # Or some other recovery
                    # For now, it will just re-prompt if choices are still available.

            elif self.current_game_state == "GAME_OVER": # Double check, as state can change in process_player_action
                break # Exit loop

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
