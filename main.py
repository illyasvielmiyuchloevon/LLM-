from api.api_key_manager import ApiKeyManager
from ui.ui_manager import UIManager
from engine.game_engine import GameEngine
from game_logic.game_controller import GameController
from engine.model_selector import ModelSelector
from engine.adventure_setup import AdventureSetup
from api.api_key_manager import ApiKeyManager # Ensure ApiKeyManager is imported
from api.llm_interface import LLMInterface # Import LLMInterface

if __name__ == "__main__":
    ui_manager = UIManager() # Instantiate UIManager first as it's used by others for messages
    api_key_manager = ApiKeyManager()
    llm_interface = LLMInterface(api_key_manager) # Instantiate LLMInterface
    model_selector = ModelSelector(api_key_manager)
    adventure_setup = AdventureSetup(ui_manager, llm_interface, model_selector) # Update AdventureSetup instantiation
    game_engine = GameEngine()

    # GameController instantiation should already be correct from previous steps,
    # but ensuring it matches the required signature if it changed:
    game_controller = GameController(
        api_key_manager=api_key_manager,
        ui_manager=ui_manager,
        model_selector=model_selector,
        adventure_setup=adventure_setup
    )

    ui_manager.display_message("Main: Starting application setup...", "info")
    key_validated = game_controller.request_and_validate_api_key()

    if key_validated:
        ui_manager.display_message("Main: API Key validation successful.", "info")

        model_selected = game_controller.select_model_flow()
        if model_selected:
            ui_manager.display_message("Main: Model selection successful.", "info")

            adventure_pref_text = game_controller.request_adventure_preferences_flow()
            if adventure_pref_text:
                # Message from request_adventure_preferences_flow already indicates capture.
                # Main can now proceed to blueprint generation.
                ui_manager.display_message(f"Main: Adventure preference set. Proceeding to blueprint generation.", "info")

                blueprint_generated = game_controller.generate_blueprint_flow()
                if blueprint_generated:
                    ui_manager.display_message("Main: Detailed World Blueprint has been successfully generated.", "info")
                    ui_manager.display_message("Main: Ready for Phase 4 (World Conception Document Generation).", "info")
                    game_engine.start_game_loop() # Placeholder for actual game start
                else:
                    ui_manager.display_message("Main: Failed to generate the Detailed World Blueprint. Cannot proceed.", "error")
            else:
                ui_manager.display_message("Main: Adventure preference setup failed. Cannot proceed to blueprint generation.", "error")
        else:
            ui_manager.display_message("Main: Model selection failed. Cannot proceed.", "error")
    else:
        ui_manager.display_message("Main: API Key is invalid. Cannot start game.", "error")
