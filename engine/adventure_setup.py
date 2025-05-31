from ui.ui_manager import UIManager
from api.llm_interface import LLMInterface
from engine.model_selector import ModelSelector

class AdventureSetup:
    def __init__(self, ui_manager: UIManager, llm_interface: LLMInterface, model_selector: ModelSelector):
        self.ui_manager = ui_manager
        self.llm_interface = llm_interface
        self.model_selector = model_selector
        self.adventure_preference: str | None = None
        self.detailed_world_blueprint: str | None = None

    def _engine_guidelines(self) -> str:
        return "Engine Guidelines: The world must be coherent and offer multiple paths. Include at least one friendly NPC and one potential adversary. The primary goal should be discoverable through exploration or interaction. Ensure there's a sense of mystery."

    def request_adventure_preference(self) -> str | None:
        # This method assumes ui_manager.show_adventure_preference_screen() will be implemented
        # and will return the text input from the user or None/empty if no input.

        # UIManager.show_adventure_preference_screen() was implemented in a previous step
        preference_text = self.ui_manager.show_adventure_preference_screen()

        if preference_text and preference_text.strip():
            self.store_preference(preference_text.strip()) # store_preference now uses ui_manager
            return self.adventure_preference
        else:
            # No message here, GameController will handle messaging if no preference provided overall
            return None

    def get_adventure_preference(self) -> str | None:
        return self.adventure_preference

    def store_preference(self, preference_text: str):
        self.adventure_preference = preference_text
        self.ui_manager.display_message(f"AdventureSetup: Preference stored: {preference_text}", "info")

    def generate_detailed_world_blueprint(self) -> str | None:
        player_adventure_preference = self.get_adventure_preference()
        selected_model_id = self.model_selector.get_selected_model()

        if not player_adventure_preference:
            self.ui_manager.display_message("AdventureSetup: Error - Adventure preference not set. Cannot generate blueprint.", "error")
            return None

        if not selected_model_id:
            self.ui_manager.display_message("AdventureSetup: Error - Model not selected. Cannot generate blueprint.", "error")
            return None

        guidelines = self._engine_guidelines()
        prompt = (
            f"Player Adventure Preference: '{player_adventure_preference}'\n\n"
            f"Engine Guidelines: '{guidelines}'\n\n"
            "Task: Based on the player's preference and adhering to the engine guidelines, "
            "generate a detailed world blueprint. The blueprint should outline key locations, "
            "potential characters, main objectives, and a central conflict or mystery. "
            "It should be rich enough to form the basis of a text adventure game."
        )

        self.ui_manager.display_message("AdventureSetup: Requesting detailed world blueprint from LLM...", "info")
        blueprint_str = self.llm_interface.generate(
            prompt,
            selected_model_id,
            expected_response_type='detailed_world_blueprint'
        )

        if blueprint_str:
            self.detailed_world_blueprint = blueprint_str
            self.ui_manager.display_message("AdventureSetup: Detailed world blueprint received successfully.", "info")
            return blueprint_str
        else:
            self.ui_manager.display_message("AdventureSetup: Failed to generate detailed world blueprint from LLM.", "error")
            return None

    def get_detailed_world_blueprint(self) -> str | None:
        return self.detailed_world_blueprint
