from api.api_key_manager import ApiKeyManager
from ui.ui_manager import UIManager
from engine.game_engine import GameEngine
from game_logic.game_controller import GameController
from engine.model_selector import ModelSelector
from engine.adventure_setup import AdventureSetup

if __name__ == "__main__":
    ui_manager = UIManager() # Instantiate UIManager first as it's used by others for messages
    api_key_manager = ApiKeyManager()
    model_selector = ModelSelector(api_key_manager)
    adventure_setup = AdventureSetup(ui_manager)
    game_engine = GameEngine()

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
                pref_snippet = adventure_pref_text[:50] + "..." if len(adventure_pref_text) > 50 else adventure_pref_text
                ui_manager.display_message(f"Main: Adventure preference '{pref_snippet}' set. Setup complete.", "info")
                ui_manager.display_message("Main: Ready for Phase 3 (World Blueprint Generation).", "info")
                game_engine.start_game_loop() # Placeholder for actual game start
            else:
                ui_manager.display_message("Main: Adventure preference setup failed. Cannot proceed.", "error")
        else:
            ui_manager.display_message("Main: Model selection failed. Cannot proceed.", "error")
    else:
        ui_manager.display_message("Main: API Key is invalid. Cannot start game.", "error")
