from api.api_key_manager import ApiKeyManager
from ui.ui_manager import UIManager
from engine.model_selector import ModelSelector
from engine.adventure_setup import AdventureSetup
# GameEngine will be imported here later when needed

class GameController:
    def __init__(self, api_key_manager: ApiKeyManager, ui_manager: UIManager, model_selector: ModelSelector, adventure_setup: AdventureSetup):
        self.api_key_manager = api_key_manager
        self.ui_manager = ui_manager
        self.model_selector = model_selector
        self.adventure_setup = adventure_setup
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
