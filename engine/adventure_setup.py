from ui.ui_manager import UIManager # Assumes execution from root or ui in PYTHONPATH

class AdventureSetup:
    def __init__(self, ui_manager: UIManager):
        self.ui_manager = ui_manager
        self.adventure_preference: str | None = None

    def request_adventure_preference(self) -> str | None:
        # This method assumes ui_manager.show_adventure_preference_screen() will be implemented
        # and will return the text input from the user or None/empty if no input.
        # For now, direct input() is used as a placeholder for UIManager's role.
        # Later, UIManager.show_adventure_preference_screen will handle the actual prompt
        # and input gathering.

        # Placeholder for where UIManager would prompt and get input:
        # self.ui_manager.display_message("Please describe your desired adventure setting or theme:", "input")
        # preference_text = input("Enter adventure preference: ") # This line will be replaced by UIManager call

        # The following line is what we expect once UIManager is updated
        preference_text = self.ui_manager.show_adventure_preference_screen()

        if preference_text and preference_text.strip():
            self.store_preference(preference_text.strip())
            return self.adventure_preference
        else:
            # self.ui_manager.display_message("No adventure preference provided.", "info")
            return None

    def get_adventure_preference(self) -> str | None:
        return self.adventure_preference

    def store_preference(self, preference_text: str):
        self.adventure_preference = preference_text
        # Using ui_manager to display message for consistency, rather than print
        self.ui_manager.display_message(f"Adventure preference stored: {preference_text}", "info")
