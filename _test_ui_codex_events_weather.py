from ui.ui_manager import UIManager
from engine.gwhr import GWHR # For default player_state structure (though not directly used here)
import copy # if needed for deepcopying mock data

print("--- Test UIManager Codex, Events, Weather ---")
ui = UIManager()

# --- Mock Data ---
mock_codex_entries = {
    "lore_001": {"knowledge_id": "lore_001", "title": "The Ancient Kings", "content": "Long ago, kings ruled with wisdom and valor over these lands.", "source_type": "ancient_tome", "source_detail": "Dusty Tome, Vol. III"},
    "beast_002": {"knowledge_id": "beast_002", "title": "Gorgons of the Grey Peak", "content": "Scaled beasts with a petrifying gaze, rumored to guard untold treasures.", "source_type": "local_legend", "source_detail": "Old Man Hemlock's tales"}
}
mock_empty_codex = {}

mock_scene_with_weather = {
  "scene_id": "rainy_pass",
  "narrative": "The mountain pass is treacherous under the downpour.",
  "current_weather_in_scene": { # This key is what display_scene will look for
      "condition": "rainy", 
      "intensity": "heavy",
      "effects_description": "A heavy rain lashes down, reducing visibility and making the path slick."
  },
  "interactive_elements": [{"id": "take_shelter", "name": "Look for shelter"}] # For display_scene
}
mock_scene_no_weather = {
    "scene_id": "calm_meadow",
    "narrative": "A calm meadow, the sun shines brightly."
    # No 'current_weather_in_scene' key
}

# --- Test display_dynamic_event_notification ---
print("\n--- Test 1: display_dynamic_event_notification ---")
ui.display_dynamic_event_notification("A distant volcano has erupted, spewing ash into the sky! The horizon darkens.")
print("Test 1 Passed.")

# --- Test display_codex_entry_content ---
print("\n--- Test 2: display_codex_entry_content ---")
print("Expecting input: <enter> (for 'Press Enter to close entry')")
entry_to_display = mock_codex_entries["lore_001"]
ui.display_codex_entry_content(
    entry_to_display.get('title','N/A'), 
    entry_to_display.get('content','N/A'), 
    entry_to_display.get('source_type','N/A'), 
    entry_to_display.get('source_detail','N/A')
)
print("Test 2 Passed.")

# --- Test display_knowledge_codex_ui ---
# This test requires careful piping of inputs.
# Sequence of inputs provided via echo:
# For Test 3.1: "1" (select entry), "" (close entry sub-prompt), "0" (exit codex main prompt)
# For Test 3.2: "" (close empty codex sub-prompt)
# For Test 3.3: "xyz" (invalid choice), "0" (exit codex main prompt)

print("\n--- Test 3: display_knowledge_codex_ui ---")

print("\nTest 3.1: Select entry 1, close sub-screen, then exit codex (0)")
print("Expecting inputs: 1 -> <enter> -> 0")
action_result_1a = ui.display_knowledge_codex_ui(mock_codex_entries) 
print(f"Codex UI returned (after selecting entry): {action_result_1a}")
assert action_result_1a == ('viewed_entry', "lore_001"), f"Test 3.1a failed. Got {action_result_1a}"

action_result_1b = ui.display_knowledge_codex_ui(mock_codex_entries) 
print(f"Codex UI returned (after exiting): {action_result_1b}")
assert action_result_1b == ('exit_codex', None), f"Test 3.1b failed. Got {action_result_1b}"
print("Test 3.1 Passed.")


print("\nTest 3.2: Empty codex")
print("Expecting input: <enter>")
action_result_empty = ui.display_knowledge_codex_ui(mock_empty_codex)
print(f"Codex UI (empty) returned: {action_result_empty}")
assert action_result_empty == ('show_codex_again', None), f"Test 3.2 failed. Got {action_result_empty}"
print("Test 3.2 Passed.")


print("\nTest 3.3: Invalid selection then exit")
print("Expecting inputs: xyz -> 0")
action_result_invalid = ui.display_knowledge_codex_ui(mock_codex_entries) 
print(f"Codex UI (invalid input) returned: {action_result_invalid}")
assert action_result_invalid == ('show_codex_again', None), f"Test 3.3a failed. Got {action_result_invalid}"

action_result_exit_after_invalid = ui.display_knowledge_codex_ui(mock_codex_entries) 
print(f"Codex UI (exit after invalid) returned: {action_result_exit_after_invalid}")
assert action_result_exit_after_invalid == ('exit_codex', None), f"Test 3.3b failed. Got {action_result_exit_after_invalid}"
print("Test 3.3 Passed.")

# --- Test display_scene for weather ---
print("\n--- Test 4: display_scene with weather ---")
print("\nTest 4.1: Scene with weather data")
ui.display_scene(mock_scene_with_weather)
# Visual check of output for weather info

print("\nTest 4.2: Scene without weather data (after a scene with weather)")
ui.display_scene(mock_scene_no_weather)
# Visual check that weather info is not printed, or previous weather not shown
print("Test 4 Passed (visual check for output).")


print("\n--- UIManager Codex, Events, Weather Tests Complete ---")
