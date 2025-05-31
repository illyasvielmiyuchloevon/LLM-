from api.api_key_manager import ApiKeyManager
from ui.ui_manager import UIManager
# GameEngine will be imported here later when needed

class GameController:
    def __init__(self, api_key_manager: ApiKeyManager, ui_manager: UIManager):
        self.api_key_manager = api_key_manager
        self.ui_manager = ui_manager
        # self.game_engine will be initialized later

    def request_and_validate_api_key(self) -> bool:
        self.ui_manager.show_api_key_screen()
        # In a real application, ui_manager.get_api_key_input() would be called.
        # For now, we simulate input() directly here.
        # This will require manual input when testing with run_in_bash_session
        key_input = input()
        self.api_key_manager.store_api_key(key_input)
        is_valid = self.api_key_manager.validate_api_key()

        if is_valid:
            self.ui_manager.display_message("API Key validated successfully.", "info")
        else:
            self.ui_manager.display_message("API Key validation failed.", "error")

        return is_valid
