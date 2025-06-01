from api.api_key_manager import ApiKeyManager
from ui.ui_manager import UIManager
from engine.game_engine import GameEngine
from game_logic.game_controller import GameController
from engine.model_selector import ModelSelector
from engine.adventure_setup import AdventureSetup
# ApiKeyManager is already imported once at the top
from api.llm_interface import LLMInterface
from engine.gwhr import GWHR # Import GWHR
# UIManager is already imported once at the top

if __name__ == "__main__":
    ui_manager = UIManager()
    api_key_manager = ApiKeyManager()
    llm_interface = LLMInterface(api_key_manager)
    model_selector = ModelSelector(api_key_manager)
    # AdventureSetup now requires llm_interface and model_selector
    adventure_setup = AdventureSetup(ui_manager, llm_interface, model_selector)
    gwhr = GWHR() # Instantiate GWHR
    game_engine = GameEngine()

    game_controller = GameController(
        api_key_manager=api_key_manager,
        ui_manager=ui_manager,
        model_selector=model_selector,
        adventure_setup=adventure_setup,
        gwhr=gwhr, # Pass GWHR to GameController
        llm_interface=llm_interface # Add missing llm_interface
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
                ui_manager.display_message(f"Main: Adventure preference set. Proceeding to Detailed Blueprint generation.", "info")

                blueprint_generated = game_controller.generate_blueprint_flow()
                if blueprint_generated:
                    ui_manager.display_message("Main: Detailed World Blueprint generated. Proceeding to World Conception and GWHR init.", "info")

                    world_initialized = game_controller.initialize_world_from_blueprint_flow()
                    if world_initialized:
                        ui_manager.display_message("Main: World Conception Document generated and GWHR successfully initialized.", "info")
                        ui_manager.display_message("Main: System ready for Phase 5 (Basic Game Loop & Scene Presentation).", "info")
                        # game_engine.start_game_loop() # Placeholder for actual game start - REMOVE THIS
                        game_controller.start_game() # CALL NEW GAME CONTROLLER START
                    else:
                        ui_manager.display_message("Main: Failed to generate World Conception Document or initialize GWHR. Cannot proceed.", "error")
                else:
                    ui_manager.display_message("Main: Failed to generate the Detailed World Blueprint. Cannot proceed.", "error")
            else:
                ui_manager.display_message("Main: Adventure preference setup failed. Cannot proceed to blueprint generation.", "error")
        else:
            ui_manager.display_message("Main: Model selection failed. Cannot proceed.", "error")
    else:
        ui_manager.display_message("Main: API Key is invalid. Cannot start game.", "error")
