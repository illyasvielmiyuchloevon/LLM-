from api.api_key_manager import ApiKeyManager
from ui.ui_manager import UIManager
from engine.game_engine import GameEngine
from game_logic.game_controller import GameController

if __name__ == "__main__":
    api_key_manager = ApiKeyManager()
    ui_manager = UIManager()
    game_engine = GameEngine()
    # GameController currently only takes api_key_manager and ui_manager
    # game_engine will be integrated later
    game_controller = GameController(api_key_manager, ui_manager)

    key_validated = game_controller.request_and_validate_api_key()

    if key_validated:
        print("Main: API Key is valid. Game can proceed.")
        game_engine.start_game_loop()
    else:
        print("Main: API Key is invalid. Cannot start game.")
