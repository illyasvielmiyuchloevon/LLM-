from api.api_key_manager import ApiKeyManager
from ui.ui_manager import UIManager
import json # For LLM response parsing
import time # For game loop delay
from api.api_key_manager import ApiKeyManager
from ui.ui_manager import UIManager
from engine.model_selector import ModelSelector
from engine.adventure_setup import AdventureSetup
from engine.gwhr import GWHR
from api.llm_interface import LLMInterface
import copy # For deepcopying NPC data for dialogue session

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
        self.llm_interface = llm_interface
        self.current_game_state: str = "INIT"
        self.active_combat_data: dict = {} # Initialize active_combat_data
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

    def initiate_combat(self, npc_ids_to_engage: list):
        self.current_game_state = "IN_COMBAT"
        self.ui_manager.display_message("Combat initiated!", "info")

        player_gwhr_state = self.gwhr.get_data_store().get('player_state', {})
        player_attrs = player_gwhr_state.get('attributes', {})

        self.active_combat_data = {
            'turn': 0,
            'player': {
                'id': 'player',
                'name': 'Player', # Could get player name if stored
                'current_hp': player_attrs.get('current_hp', 100),
                'max_hp': player_attrs.get('max_hp', 100),
                'attack_power': player_attrs.get('attack_power', 10),
                'defense_power': player_attrs.get('defense_power', 5),
                'evasion_chance': player_attrs.get('evasion_chance', 0.1),
                'hit_chance': player_attrs.get('hit_chance', 0.8)
                # Not storing original_attributes for player here, as player_state in GWHR is the source of truth
            },
            'npcs': [],
            # Initial strategies, can be updated by LLM combat outcomes
            'last_turn_player_strategies': [
                {"id": "standard_attack", "name": "Standard Attack"},
                {"id": "power_attack", "name": "Power Attack (Low Hit, High Dmg)"},
                {"id": "quick_attack", "name": "Quick Attack (High Hit, Low Dmg)"},
                {"id": "defend", "name": "Defend"},
                {"id": "try_flee", "name": "Attempt to Flee"}
            ],
            'combat_ended': False,
            'victor': None,
            'final_summary_narrative': '' # For storing the text that combat_loop will pass to show_combat_results
        }

        all_gwhr_npcs = self.gwhr.get_data_store().get('npcs', {})
        for npc_id in npc_ids_to_engage:
            npc_gwhr_data = all_gwhr_npcs.get(npc_id)
            if not npc_gwhr_data:
                self.ui_manager.display_message(f"Warning: NPC {npc_id} not found in GWHR for combat.", "warning")
                continue

            npc_attrs = npc_gwhr_data.get('attributes', {})
            self.active_combat_data['npcs'].append({
                'id': npc_id,
                'name': npc_gwhr_data.get('name', npc_id),
                'current_hp': npc_attrs.get('current_hp', 50), # Default if not in NPC's specific attrs
                'max_hp': npc_attrs.get('max_hp', 50),
                'attack_power': npc_attrs.get('attack_power', 8),
                'defense_power': npc_attrs.get('defense_power', 3),
                'evasion_chance': npc_attrs.get('evasion_chance', 0.05),
                'hit_chance': npc_attrs.get('hit_chance', 0.7),
                'original_gwhr_data_snapshot': copy.deepcopy(npc_gwhr_data) # Store snapshot for post-combat state update
            })

        if not self.active_combat_data['npcs']:
            self.ui_manager.display_message("No valid opponents found to engage in combat.", "error")
            self.current_game_state = "AWAITING_PLAYER_ACTION" # Revert state
            self.active_combat_data = {} # Clear combat data
            return

        self.gwhr.log_event(f"Combat started against: {[npc['name'] for npc in self.active_combat_data['npcs']]}", event_type="combat_start")
        self.combat_loop()

    def combat_loop(self):
        while self.current_game_state == "IN_COMBAT":
            self.active_combat_data['turn'] += 1
            self.ui_manager.display_message(f"\n--- Combat Turn {self.active_combat_data['turn']} ---", "info")

            player_combat_data = self.active_combat_data['player']
            # Only include NPCs with HP > 0 in the UI list and for LLM context
            active_npc_combatants = [npc for npc in self.active_combat_data['npcs'] if npc.get('current_hp', 0) > 0]

            npc_combatants_info_for_ui = [
                {'name': n['name'], 'hp': n['current_hp'], 'max_hp': n['max_hp'], 'id': n['id']}
                for n in active_npc_combatants
            ]

            # Check if combat should have ended before player gets to choose a strategy
            # (e.g. if all NPCs were defeated by an environmental effect or prior DOT, though not implemented yet)
            if not npc_combatants_info_for_ui and not self.active_combat_data.get('combat_ended'):
                 self.ui_manager.display_message("All opponents appear to be defeated!", "info")
                 self.active_combat_data['combat_ended'] = True
                 self.active_combat_data['victor'] = 'player'
                 self.active_combat_data.setdefault('final_summary_narrative', "With no more foes standing, the battle ends.")
                 # Fall through to the combat_ended block below

            self.ui_manager.show_combat_interface(
                player_combat_data['current_hp'],
                player_combat_data['max_hp'],
                npc_combatants_info_for_ui
            )

            if self.active_combat_data.get('combat_ended'):
                self.ui_manager.show_combat_results(
                    self.active_combat_data.get('final_summary_narrative', "The dust settles."),
                    self.active_combat_data.get('victor')
                )

                # Post-combat updates to GWHR
                final_player_hp = self.active_combat_data['player']['current_hp']
                # Get a fresh copy of player_state to modify, then update GWHR
                player_state_gwhr = copy.deepcopy(self.gwhr.get_data_store().get('player_state', {}))
                player_state_gwhr.setdefault('attributes', {})['current_hp'] = final_player_hp
                self.gwhr.update_state({'player_state': player_state_gwhr})

                # Update NPC states in GWHR based on their original snapshot + final combat HP
                npcs_gwhr_full_update = copy.deepcopy(self.gwhr.get_data_store().get('npcs', {}))
                for npc_combat_data in self.active_combat_data['npcs']: # Iterate through all initial combatants
                    npc_id_to_update = npc_combat_data['id']
                    if npc_id_to_update in npcs_gwhr_full_update: # Should always be true
                        # Restore original data, then update HP and status
                        restored_npc_data = copy.deepcopy(npc_combat_data['original_gwhr_data_snapshot'])
                        restored_npc_data.setdefault('attributes', {})['current_hp'] = npc_combat_data['current_hp']
                        if npc_combat_data['current_hp'] <= 0:
                            restored_npc_data['status'] = 'defeated'
                            # Log individual defeat only once if not already logged by LLM outcome processing
                            # This specific log might be redundant if process_combat_turn also logs it.
                            # For now, let's assume this is a summary log.
                            # self.gwhr.log_event(f"NPC {npc_combat_data['name']} was defeated during combat resolution.", event_type="combat_npc_defeat", causal_factors=[f"npc:{npc_id_to_update}"])
                        npcs_gwhr_full_update[npc_id_to_update] = restored_npc_data
                    else: # NPC was somehow not in GWHR, add them (less likely path)
                         npcs_gwhr_full_update[npc_id_to_update] = npc_combat_data['original_gwhr_data_snapshot']
                         npcs_gwhr_full_update[npc_id_to_update].setdefault('attributes',{})['current_hp'] = npc_combat_data['current_hp']
                         if npc_combat_data['current_hp'] <= 0: npcs_gwhr_full_update[npc_id_to_update]['status'] = 'defeated'

                self.gwhr.update_state({'npcs': npcs_gwhr_full_update})

                self.gwhr.log_event(
                    f"Combat ended. Victor: {self.active_combat_data.get('victor', 'Unknown')}. Summary: {self.active_combat_data.get('final_summary_narrative', '')}",
                    event_type="combat_end"
                )
                self.current_game_state = "AWAITING_PLAYER_ACTION"
                self.active_combat_data = {} # Clear active combat data

                # Refresh scene display after combat
                current_scene_data_after_combat = self.gwhr.get_data_store().get('current_scene_data', {})
                self.ui_manager.display_scene(current_scene_data_after_combat)
                break # Exit combat loop

            available_strategies = self.active_combat_data.get(
                'last_turn_player_strategies',
                [{"id": "standard_attack", "name": "Standard Attack"}] # Fallback default
            )
            player_chosen_strategy_id = self.ui_manager.present_combat_strategies(available_strategies)

            if not player_chosen_strategy_id:
                self.ui_manager.display_message("No strategy chosen, defaulting to 'defend'.", "warning")
                player_chosen_strategy_id = "defend"

            self.process_combat_turn(player_chosen_strategy_id)

            time.sleep(0.1) # Small delay

    def process_combat_turn(self, player_strategy_id: str):
        self.ui_manager.display_message(f"Processing your strategy: {player_strategy_id}...", "info")

        active_npcs_for_prompt = [
            npc for npc in self.active_combat_data.get('npcs', []) if npc.get('current_hp', 0) > 0
        ]
        prompt_combatants_state = [{
            'id': 'player',
            'hp': self.active_combat_data['player']['current_hp'],
            'attack_power': self.active_combat_data['player']['attack_power'], # Added missing base stats for player
            'defense_power': self.active_combat_data['player']['defense_power'],
            'evasion_chance': self.active_combat_data['player']['evasion_chance'],
            'hit_chance': self.active_combat_data['player']['hit_chance']
        }]
        for npc_data in active_npcs_for_prompt:
            prompt_combatants_state.append({
                'id': npc_data['id'],
                'name': npc_data['name'],
                'hp': npc_data['current_hp'],
                'attack_power': npc_data['attack_power'],  # Added missing base stats for NPCs
                'defense_power': npc_data['defense_power'],
                'evasion_chance': npc_data['evasion_chance'],
                'hit_chance': npc_data['hit_chance']
            })

        # Include relevant parts of GWHR context, like player inventory for item use, skills etc.
        # For now, keeping it simple as per initial plan.
        # context_for_llm = self.gwhr.get_current_context() # Could be too large
        # For combat, focus on combatant states and player's chosen strategy.

        llm_prompt = (
            f"Combat Turn: {self.active_combat_data['turn']}\n"
            f"Player chose strategy: '{player_strategy_id}'.\n"
            f"Current Combatants State (active ones): {json.dumps(prompt_combatants_state)}\n\n"
            f"Task: Based on player's chosen strategy and current combatant states, determine the detailed outcome of this combat turn. "
            f"Narrate the action and its results. Calculate HP changes for all affected combatants. "
            f"Decide if the combat has ended (e.g., player defeated, or all NPCs defeated). "
            f"Provide feedback on the player's strategy if appropriate. "
            f"Suggest 3-4 available strategies for the player's next turn if combat continues. "
            f"Output a single valid JSON object with fields: 'turn_summary_narrative' (string), "
            f"'player_hp_change' (int, e.g., -5 for damage, 0 for no change, positive for healing), "
            f"'npc_hp_changes' (list of objects, each like {{'npc_id': string, 'hp_change': int}}), "
            f"'combat_ended' (boolean), 'victor' (string: 'player', 'npc', 'draw', or null if not ended), "
            f"'player_strategy_feedback' (optional string), "
            f"and 'available_player_strategies' (list of {{'id': string, 'name': string}} objects for next turn if combat is not ended)."
        )

        model_id = self.model_selector.get_selected_model()
        if not model_id:
            self.ui_manager.display_message("GameController: CRITICAL - No model selected for LLM call in combat!", "error")
            self.active_combat_data.update({
                'combat_ended': True,
                'victor': 'error_no_model',
                'final_summary_narrative': 'Critical Error: No LLM model available for combat simulation.'
            })
            return

        outcome_json_str = self.llm_interface.generate(llm_prompt, model_id, expected_response_type='combat_turn_outcome')

        outcome_data = {}
        if not outcome_json_str:
            self.ui_manager.display_message("GameController: LLM failed to provide combat outcome. Assuming a glancing blow from all sides.", "error")
            outcome_data = {
                "turn_summary_narrative": "The combatants eye each other warily; a tense moment passes with no major effect.",
                "player_hp_change": 0, "npc_hp_changes": [], "combat_ended": False, "victor": None,
                "available_player_strategies": self.active_combat_data.get('last_turn_player_strategies') # Reuse last strategies
            }
        else:
            try:
                outcome_data = json.loads(outcome_json_str)
            except json.JSONDecodeError as e:
                self.ui_manager.display_message(f"GameController: Error parsing combat outcome JSON from LLM: {e}. Assuming glancing blows.", "error")
                outcome_data = {
                    "turn_summary_narrative": f"Confusion in the ranks due to garbled orders (LLM Error: {e}). The turn yields no clear result.",
                    "player_hp_change": 0, "npc_hp_changes": [], "combat_ended": False, "victor": None,
                    "available_player_strategies": self.active_combat_data.get('last_turn_player_strategies')
                }

        # Apply updates from outcome_data to self.active_combat_data
        player_c_data = self.active_combat_data['player']
        player_c_data['current_hp'] += outcome_data.get('player_hp_change', 0)
        player_c_data['current_hp'] = max(0, player_c_data['current_hp'])

        for npc_hp_update in outcome_data.get('npc_hp_changes', []):
            for npc_combatant in self.active_combat_data['npcs']:
                if npc_combatant['id'] == npc_hp_update.get('npc_id'):
                    npc_combatant['current_hp'] += npc_hp_update.get('hp_change', 0)
                    npc_combatant['current_hp'] = max(0, npc_combatant['current_hp'])
                    break

        self.active_combat_data['last_turn_player_strategies'] = outcome_data.get(
            'available_player_strategies',
            self.active_combat_data.get('last_turn_player_strategies') # Keep old if new not provided
        )
        self.active_combat_data['combat_ended'] = outcome_data.get('combat_ended', False)
        self.active_combat_data['victor'] = outcome_data.get('victor')
        # Store this turn's narrative for display by combat_loop if combat ends.
        self.active_combat_data['final_summary_narrative'] = outcome_data.get('turn_summary_narrative', "The turn ends without detailed narration.")

        self.gwhr.log_event(
            f"Combat Turn {self.active_combat_data['turn']}: Player chose '{player_strategy_id}'. Outcome: {outcome_data.get('turn_summary_narrative','')}",
            event_type="combat_turn_detail",
            payload=copy.deepcopy(outcome_data) # Log a copy of the full outcome
        )
        self.ui_manager.display_combat_narrative(outcome_data.get('turn_summary_narrative', "No narrative for turn outcome."))
        if outcome_data.get('player_strategy_feedback'):
            self.ui_manager.display_message(f"Feedback: {outcome_data.get('player_strategy_feedback')}", "info")

        # Check for combat end conditions if LLM didn't explicitly state it but HP dropped
        if not self.active_combat_data['combat_ended']:
            if player_c_data['current_hp'] <= 0:
                self.active_combat_data.update({
                    'combat_ended': True,
                    'victor': 'npc',
                    'final_summary_narrative': self.active_combat_data.get('final_summary_narrative','') + " Player has fallen!"
                })
                self.gwhr.log_event("Player defeated in combat by HP loss.", event_type="combat_end_condition")

            # Check if all active NPCs are defeated
            # active_npcs_for_prompt already contains NPCs with HP > 0 at start of this method.
            # We need to check based on current HP values in self.active_combat_data['npcs']
            current_live_npcs = [n for n in self.active_combat_data['npcs'] if n['current_hp'] > 0]
            if not current_live_npcs and self.active_combat_data['npcs']: # Ensure there were NPCs to begin with
                self.active_combat_data.update({
                    'combat_ended': True,
                    'victor': 'player',
                    'final_summary_narrative': self.active_combat_data.get('final_summary_narrative','') + " All opponents defeated!"
                })
                self.gwhr.log_event("All NPCs defeated in combat by HP loss.", event_type="combat_end_condition")

    def handle_npc_dialogue(self, npc_id: str, initial_player_input: str = None):
        # original_game_state = self.current_game_state # Not strictly needed if we always aim for AWAITING_PLAYER_ACTION
        self.current_game_state = "NPC_DIALOGUE"
        self.ui_manager.display_message(f"\nStarting dialogue with NPC ID: {npc_id}...", "info")

        all_npcs_data = self.gwhr.get_data_store().get('npcs', {})
        npc_data_snapshot = copy.deepcopy(all_npcs_data.get(npc_id))

        if not npc_data_snapshot:
            self.ui_manager.display_message(f"Error: NPC with ID '{npc_id}' not found in GWHR.", "error")
            self.current_game_state = "AWAITING_PLAYER_ACTION" # Revert to a known safe state
            return

        npc_name = npc_data_snapshot.get('name', npc_id)
        player_input_for_llm = initial_player_input if initial_player_input is not None else "..."

        while self.current_game_state == "NPC_DIALOGUE":
            gwhr_snapshot = self.gwhr.get_current_context()

            npc_specific_context = {
                "id": npc_data_snapshot.get('id'), "name": npc_name,
                "description": npc_data_snapshot.get('description', '')[:100] + "...",
                "role": npc_data_snapshot.get('role'),
                "attributes": npc_data_snapshot.get('attributes'),
                "status": npc_data_snapshot.get('status'),
                "knowledge_preview": [k.get('topic_id', k) for k in npc_data_snapshot.get('knowledge', [])[:3]],
                "dialogue_log_with_player_preview": npc_data_snapshot.get('dialogue_log', [])[-2:]
            }

            prompt_context_for_llm = {
                "player_state_summary": {
                    "attributes": gwhr_snapshot.get('player_state',{}).get('attributes'),
                    "current_location_id": gwhr_snapshot.get('player_state',{}).get('current_location_id')
                },
                "current_scene_summary": {
                    "scene_id": gwhr_snapshot.get('current_scene_data',{}).get('scene_id'),
                    "narrative_snippet": gwhr_snapshot.get('current_scene_data',{}).get('narrative', '')[:100] + "..."
                },
                "game_time": gwhr_snapshot.get('current_game_time')
            }

            llm_prompt = (
                f"You are roleplaying as {npc_name} (ID: {npc_id}).\n"
                f"Your Character Details (NPC): {json.dumps(npc_specific_context, indent=2)}\n"
                f"Overall Game Context: {json.dumps(prompt_context_for_llm, indent=2)}\n"
                f"Player says/does to you: '{player_input_for_llm}'\n\n"
                f"Task: Generate {npc_name}'s dialogue response. Your response must be a single valid JSON object including fields: "
                f"'dialogue_text' (string, what you, {npc_name}, say), "
                f"'new_npc_status' (string, your updated short-term status, e.g., 'intrigued', 'annoyed', 'helpful'), "
                f"'attitude_towards_player_change' (string, e.g., '+5', '-2', or '0', reflecting change in your disposition), "
                f"'knowledge_revealed' (list of new knowledge topic objects with 'topic_id' and 'summary' if you reveal something new), "
                f"and optional 'dialogue_options_for_player' (list of 2-4 objects with 'id' and 'name' for player choices to continue talking to you). "
                f"If the player says '/bye' or '/end', or if the conversation naturally concludes, make 'dialogue_text' a polite closing and set 'new_npc_status' to 'ending_dialogue'."
            )

            model_id = self.model_selector.get_selected_model()
            if not model_id:
                self.ui_manager.display_message("GameController: CRITICAL Error - No model selected for LLM call in dialogue.", "error")
                self.current_game_state = "GAME_OVER"
                break

            response_json_str = self.llm_interface.generate(llm_prompt, model_id, expected_response_type='npc_dialogue_response')

            if not response_json_str:
                self.ui_manager.display_message(f"Error: {npc_name} seems lost for words (LLM failed to respond). Try again or type '/bye'.", "error")
                player_input_for_llm = self.ui_manager.get_free_text_input(f"Your reply to {npc_name} (or /bye to end): ")
                if player_input_for_llm.lower() in ["/bye", "/end"]:
                    self.current_game_state = "AWAITING_PLAYER_ACTION" # Exit dialogue
                continue

            try:
                dialogue_data = json.loads(response_json_str)
            except json.JSONDecodeError as e:
                self.ui_manager.display_message(f"Error: Received garbled response from {npc_name} (JSON Error: {e}). Snippet: {response_json_str[:100]}...", "error")
                player_input_for_llm = self.ui_manager.get_free_text_input(f"Your reply to {npc_name} (or /bye to end): ")
                if player_input_for_llm.lower() in ["/bye", "/end"]:
                    self.current_game_state = "AWAITING_PLAYER_ACTION" # Exit dialogue
                continue

            npc_actual_response_text = dialogue_data.get('dialogue_text', f"({npc_name} seems unresponsive.)")
            player_reply_options = dialogue_data.get('dialogue_options_for_player')

            self.ui_manager.display_npc_dialogue(npc_name, npc_actual_response_text, player_reply_options)

            npc_data_snapshot['status'] = dialogue_data.get('new_npc_status', npc_data_snapshot.get('status'))
            dialogue_log_entry = {'player': player_input_for_llm, 'npc': npc_actual_response_text, 'time': self.gwhr.data_store.get('current_game_time')}
            npc_data_snapshot.setdefault('dialogue_log', []).append(dialogue_log_entry)
            npc_data_snapshot['last_interaction_time'] = self.gwhr.data_store.get('current_game_time')

            attitude_change_str = dialogue_data.get('attitude_towards_player_change', '0')
            try:
                attitude_change = int(attitude_change_str)
                npc_data_snapshot.setdefault('attributes', {}).setdefault('disposition_towards_player', 0)
                npc_data_snapshot['attributes']['disposition_towards_player'] += attitude_change
            except ValueError:
                self.ui_manager.display_message(f"Warning: Invalid attitude_towards_player_change format: {attitude_change_str}", "warning")

            current_npcs_in_gwhr = self.gwhr.get_data_store().get('npcs', {})
            current_npcs_in_gwhr[npc_id] = npc_data_snapshot
            self.gwhr.update_state({'npcs': current_npcs_in_gwhr})

            self.gwhr.log_event(
                f"Dialogue: Player: '{player_input_for_llm}', {npc_name}: '{npc_actual_response_text[:50]}...'. Attitude change: {attitude_change_str}.",
                event_type="dialogue_exchange",
                causal_factors=[f"npc:{npc_id}"]
            )

            if npc_data_snapshot.get('status') == 'ending_dialogue':
                self.current_game_state = "AWAITING_PLAYER_ACTION" # Dialogue ended by NPC
                break

            if player_reply_options:
                self.ui_manager.display_message("You can choose an option or type your own reply (or /bye to end).", "info")
                raw_next_input = self.ui_manager.get_free_text_input(f"Your response to {npc_name}: ")

                processed_choice = False
                try:
                    choice_num = int(raw_next_input)
                    if 1 <= choice_num <= len(player_reply_options):
                        selected_option = player_reply_options[choice_num-1]
                        player_input_for_llm = selected_option.get('name', selected_option.get('id'))
                        self.gwhr.log_event(f"Player selected dialogue option: '{player_input_for_llm}' (ID: {selected_option.get('id')})", event_type="player_dialogue_choice")
                        processed_choice = True
                except ValueError:
                    pass

                if not processed_choice:
                    player_input_for_llm = raw_next_input
            else:
                player_input_for_llm = self.ui_manager.get_free_text_input(f"Your reply to {npc_name} (or /bye to end): ")

            if player_input_for_llm.lower() in ["/bye", "/end"]:
                self.current_game_state = "AWAITING_PLAYER_ACTION" # Player ends dialogue

        self.ui_manager.display_message(f"\nDialogue with {npc_name} ended.", "info")
        # Ensure state is reverted if loop somehow exited while still NPC_DIALOGUE
        if self.current_game_state == "NPC_DIALOGUE":
            self.current_game_state = "AWAITING_PLAYER_ACTION"

    def handle_npc_dialogue(self, npc_id: str, initial_player_input: str = None):
        original_game_state = self.current_game_state
        self.current_game_state = "NPC_DIALOGUE"
        self.ui_manager.display_message(f"\nStarting dialogue with NPC ID: {npc_id}...", "info")

        # Ensure GWHR.data_store['npcs'] exists and npc_id is in it.
        # GWHR.get_data_store() returns a deepcopy, so we need to fetch, modify, and then save back.
        # For a long dialogue, repeatedly deepcopying the entire GWHR store is inefficient.
        # A better approach for frequent updates to a specific NPC might be a more direct access or specific GWHR methods.
        # For now, we'll work with copies and full updates as per current GWHR design for player_state.

        all_npcs_data = self.gwhr.get_data_store().get('npcs', {})
        npc_data_snapshot = copy.deepcopy(all_npcs_data.get(npc_id)) # Get a mutable copy for this dialogue session

        if not npc_data_snapshot:
            self.ui_manager.display_message(f"Error: NPC with ID '{npc_id}' not found in GWHR.", "error")
            self.current_game_state = original_game_state # Revert
            return

        npc_name = npc_data_snapshot.get('name', npc_id)
        player_input_for_llm = initial_player_input if initial_player_input is not None else "..." # Default if no initial input

        while self.current_game_state == "NPC_DIALOGUE":
            gwhr_snapshot = self.gwhr.get_current_context() # Get full context for prompt

            # Construct NPC-specific context for the prompt (limited fields)
            npc_specific_context = {
                "id": npc_data_snapshot.get('id'), "name": npc_name,
                "description": npc_data_snapshot.get('description', '')[:100] + "...", # Snippet
                "role": npc_data_snapshot.get('role'),
                "attributes": npc_data_snapshot.get('attributes'),
                "status": npc_data_snapshot.get('status'), # Current short-term status
                "knowledge_preview": [k.get('topic_id', k) for k in npc_data_snapshot.get('knowledge', [])[:3]], # Show only a few topic IDs
                "dialogue_log_with_player_preview": npc_data_snapshot.get('dialogue_log', [])[-2:] # Last 2 exchanges
            }

            prompt_context_for_llm = {
                "player_state_summary": {
                    "attributes": gwhr_snapshot.get('player_state',{}).get('attributes'),
                    "current_location_id": gwhr_snapshot.get('player_state',{}).get('current_location_id')
                },
                "current_scene_summary": {
                    "scene_id": gwhr_snapshot.get('current_scene_data',{}).get('scene_id'),
                    "narrative_snippet": gwhr_snapshot.get('current_scene_data',{}).get('narrative', '')[:100] + "..."
                },
                "game_time": gwhr_snapshot.get('current_game_time')
            }

            llm_prompt = (
                f"You are roleplaying as {npc_name} (ID: {npc_id}).\n"
                f"Your Character Details (NPC): {json.dumps(npc_specific_context, indent=2)}\n"
                f"Overall Game Context: {json.dumps(prompt_context_for_llm, indent=2)}\n"
                f"Player says/does to you: '{player_input_for_llm}'\n\n"
                f"Task: Generate {npc_name}'s dialogue response. Your response must be a single valid JSON object including fields: "
                f"'dialogue_text' (string, what you, {npc_name}, say), "
                f"'new_npc_status' (string, your updated short-term status, e.g., 'intrigued', 'annoyed', 'helpful'), "
                f"'attitude_towards_player_change' (string, e.g., '+5', '-2', or '0', reflecting change in your disposition), "
                f"'knowledge_revealed' (list of new knowledge topic objects with 'topic_id' and 'summary' if you reveal something new), "
                f"and optional 'dialogue_options_for_player' (list of 2-4 objects with 'id' and 'name' for player choices to continue talking to you). "
                f"If the player says '/bye' or '/end', or if the conversation naturally concludes, make 'dialogue_text' a polite closing and set 'new_npc_status' to 'ending_dialogue'."
            )

            model_id = self.model_selector.get_selected_model()
            if not model_id:
                self.ui_manager.display_message("GameController: CRITICAL Error - No model selected for LLM call in dialogue.", "error")
                self.current_game_state = "GAME_OVER"
                break

            response_json_str = self.llm_interface.generate(llm_prompt, model_id, expected_response_type='npc_dialogue_response')

            if not response_json_str:
                self.ui_manager.display_message(f"Error: {npc_name} seems lost for words (LLM failed to respond). Try again or type '/bye'.", "error")
                # Get new player input to decide next step
                player_input_for_llm = self.ui_manager.get_free_text_input(f"Your reply to {npc_name} (or /bye to end): ")
                if player_input_for_llm.lower() in ["/bye", "/end"]:
                    self.current_game_state = original_game_state # Revert to pre-dialogue state
                # Loop continues with new player_input_for_llm or exits if state changed
                continue

            try:
                dialogue_data = json.loads(response_json_str)
            except json.JSONDecodeError as e:
                self.ui_manager.display_message(f"Error: Received garbled response from {npc_name} (JSON Error: {e}). Snippet: {response_json_str[:100]}...", "error")
                player_input_for_llm = self.ui_manager.get_free_text_input(f"Your reply to {npc_name} (or /bye to end): ")
                if player_input_for_llm.lower() in ["/bye", "/end"]:
                    self.current_game_state = original_game_state
                continue

            npc_actual_response_text = dialogue_data.get('dialogue_text', f"({npc_name} seems unresponsive.)")
            player_reply_options = dialogue_data.get('dialogue_options_for_player')

            self.ui_manager.display_npc_dialogue(npc_name, npc_actual_response_text, player_reply_options)

            # Update NPC state within our npc_data_snapshot for this session
            npc_data_snapshot['status'] = dialogue_data.get('new_npc_status', npc_data_snapshot.get('status'))
            dialogue_log_entry = {'player': player_input_for_llm, 'npc': npc_actual_response_text, 'time': self.gwhr.data_store.get('current_game_time')}
            npc_data_snapshot.setdefault('dialogue_log', []).append(dialogue_log_entry)
            npc_data_snapshot['last_interaction_time'] = self.gwhr.data_store.get('current_game_time')

            attitude_change_str = dialogue_data.get('attitude_towards_player_change', '0')
            try:
                attitude_change = int(attitude_change_str) # Handles "+5", "-2", "0"
                npc_data_snapshot.setdefault('attributes', {}).setdefault('disposition_towards_player', 0)
                npc_data_snapshot['attributes']['disposition_towards_player'] += attitude_change
            except ValueError:
                self.ui_manager.display_message(f"Warning: Invalid attitude_towards_player_change format: {attitude_change_str}", "warning")

            # TODO: Process 'knowledge_revealed' and update NPC/world knowledge in GWHR

            # Persist the updated npc_data_snapshot back to GWHR's main NPC store
            # This requires GWHR.update_state to handle nested updates to its 'npcs' dict correctly
            # or a new GWHR method like update_npc_data(npc_id, npc_data_snapshot)
            current_npcs_in_gwhr = self.gwhr.get_data_store().get('npcs', {})
            current_npcs_in_gwhr[npc_id] = npc_data_snapshot # Update the specific NPC
            self.gwhr.update_state({'npcs': current_npcs_in_gwhr}) # This will deepcopy the entire npcs dict again.
                                                              # More efficient would be a targeted update.

            self.gwhr.log_event(
                f"Dialogue: Player: '{player_input_for_llm}', {npc_name}: '{npc_actual_response_text[:50]}...'. Attitude change: {attitude_change_str}.",
                event_type="dialogue_exchange",
                causal_factors=[f"npc:{npc_id}"]
            )

            if npc_data_snapshot.get('status') == 'ending_dialogue':
                self.current_game_state = original_game_state
                break

            if player_reply_options:
                self.ui_manager.display_message("You can choose an option or type your own reply (or /bye to end).", "info")
                raw_next_input = self.ui_manager.get_free_text_input(f"Your response to {npc_name}: ")

                processed_choice = False
                try: # Try to process as a number first
                    choice_num = int(raw_next_input)
                    if 1 <= choice_num <= len(player_reply_options):
                        selected_option = player_reply_options[choice_num-1]
                        player_input_for_llm = selected_option.get('name', selected_option.get('id'))
                        # Here, we might want to send the ID or a specific command related to the ID to LLM
                        # For now, sending the display name as the next input.
                        self.gwhr.log_event(f"Player selected dialogue option: '{player_input_for_llm}' (ID: {selected_option.get('id')})", event_type="player_dialogue_choice")
                        processed_choice = True
                except ValueError:
                    pass # Not a number, treat as free text

                if not processed_choice:
                    player_input_for_llm = raw_next_input # Use the raw text
            else:
                player_input_for_llm = self.ui_manager.get_free_text_input(f"Your reply to {npc_name} (or /bye to end): ")

            if player_input_for_llm.lower() in ["/bye", "/end"]:
                self.current_game_state = original_game_state # Exit dialogue

        self.ui_manager.display_message(f"\nDialogue with {npc_name} ended.", "info")
        if self.current_game_state == "NPC_DIALOGUE": # If loop exited for reasons other than /bye or status='ending_dialogue'
            self.current_game_state = original_game_state

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

    def validate_and_get_action_id(self, command: str, choices: list) -> str | None:
        try:
            choice_num = int(command)
            if 1 <= choice_num <= len(choices):
                selected_0_based_index = choice_num - 1
                # Ensure the choice dictionary itself and its 'id' key exist
                if isinstance(choices[selected_0_based_index], dict) and 'id' in choices[selected_0_based_index]:
                    return choices[selected_0_based_index].get('id')
                else:
                    # This case should ideally not happen if choices are well-formed by LLM
                    self.ui_manager.display_message(f"Error: Choice format incorrect for command '{command}'. No ID found.", "error")
                    return None
            else:
                # Error message for out-of-range will be handled by the calling context (game_loop)
                return None
        except ValueError:
            # Error message for non-numeric will be handled by the calling context (game_loop)
            return None

    def handle_game_menu(self):
        player_state = self.gwhr.get_data_store().get('player_state', {})
        while True:
            menu_action_result = self.ui_manager.show_game_systems_menu(player_state)
            if menu_action_result == 'close_menu':
                break
            # elif menu_action_result == 'show_menu_again':
            #     continue # Loop continues by default
            # No other actions from this menu result in direct game state changes yet

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

                # --- Image Generation for new scene ---
                narrative_for_prompt = scene_data.get('narrative', '')
                npcs_for_prompt = ", ".join([npc.get('name', 'N/A') for npc in scene_data.get('npcs_in_scene', []) if npc.get('name')])
                image_prompt_text = f"Scene: {narrative_for_prompt[:150]}. NPCs: {npcs_for_prompt[:100]}."
                scene_data['image_prompt_elements'] = [image_prompt_text] # Store the generated prompt

                self.ui_manager.show_image_loading_indicator()
                image_url = self.llm_interface.generate_image(image_prompt_text)
                self.ui_manager.hide_image_loading_indicator()

                if image_url:
                    scene_data['background_image_url'] = image_url
                    self.ui_manager.display_message(f"GameController: Image generated for scene '{scene_data.get('scene_id', scene_id)}'. URL: {image_url}", "info")
                else:
                    scene_data['background_image_url'] = None
                    self.ui_manager.display_message(f"GameController: Failed to generate image for scene '{scene_data.get('scene_id', scene_id)}'.", "warning")
                # --- End Image Generation ---

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

        # Check if this action is a dialogue trigger
        current_scene_data_for_action = self.gwhr.get_data_store().get('current_scene_data', {})
        interactive_elements_for_action = current_scene_data_for_action.get('interactive_elements', [])
        chosen_element = next((el for el in interactive_elements_for_action if el.get('id') == action_detail), None)

        if chosen_element and chosen_element.get('type') == 'dialogue' and chosen_element.get('target_id'):
            npc_id_to_talk_to = chosen_element['target_id']
            initial_dialogue_input = f"Selected interaction: '{chosen_element.get('name', action_detail)}'"
            self.handle_npc_dialogue(npc_id_to_talk_to, initial_player_input=initial_dialogue_input)
            return
        elif chosen_element and chosen_element.get('type') == 'combat_trigger' and chosen_element.get('target_id'):
            npc_id_to_engage = chosen_element['target_id']
            # It's good practice to use .get with a fallback for name display
            npc_name_display = chosen_element.get('name', npc_id_to_engage)
            self.ui_manager.display_message(f"You chose to engage {npc_name_display} in combat!", "info")
            self.initiate_combat(npc_ids_to_engage=[npc_id_to_engage])
            return # Combat loop will take over.

        # If not a dialogue or combat_trigger action, proceed with generic action processing:
        context_for_llm = self.gwhr.get_current_context()
        current_scene_id_from_gwhr = context_for_llm.get('current_scene_data', {}).get('scene_id', 'UNKNOWN_SCENE')

        context_json_str = json.dumps(context_for_llm, indent=2)
        truncated_context_str = context_json_str[:1000]
        if len(context_json_str) > 1000:
            truncated_context_str += "\n... (context truncated)"

        # New prompt structure for process_player_action
        current_scene_elements = context_for_llm.get('current_scene_data', {}).get('interactive_elements', [])
        chosen_element_info = next((el for el in current_scene_elements if el.get('id') == action_detail), None)
        chosen_element_name = chosen_element_info.get('name', action_detail) if chosen_element_info else action_detail

        prompt = (
            f"Current Game Context (JSON):\n{truncated_context_str}\n\n"
            f"Player selected the option '{chosen_element_name}' (ID: '{action_detail}') from the interaction menu in scene '{current_scene_id_from_gwhr}'.\n\n"
            f"Task: Generate the outcome of this specific interaction. This might mean updating the current scene (e.g., a narrative update, changed NPC status, modified/new interactive elements) or transitioning to a new scene. "
            f"If transitioning to a new scene, provide the full data for the new scene, including a new 'scene_id' which MUST be different from '{current_scene_id_from_gwhr}'. "
            f"If updating the current scene, the response can omit 'scene_id' or use the current one ('{current_scene_id_from_gwhr}'), but should detail changes, potentially including a 'narrative_update' field. "
            f"Ensure the output is a single valid JSON object structured as scene data."
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


                # --- Image Generation for action outcome scene data ---
                narrative_for_prompt_action = response_data.get('narrative', '')
                npcs_for_prompt_action = ", ".join([npc.get('name', 'N/A') for npc in response_data.get('npcs_in_scene', []) if npc.get('name')])
                image_prompt_text_action = f"Scene after action: {narrative_for_prompt_action[:150]}. NPCs: {npcs_for_prompt_action[:100]}."
                response_data['image_prompt_elements'] = [image_prompt_text_action]

                self.ui_manager.show_image_loading_indicator()
                image_url_action = self.llm_interface.generate_image(image_prompt_text_action)
                self.ui_manager.hide_image_loading_indicator()

                if image_url_action:
                    response_data['background_image_url'] = image_url_action
                    self.ui_manager.display_message(f"GameController: Image updated/generated for scene '{response_data.get('scene_id')}'. URL: {image_url_action}", "info")
                else:
                    response_data['background_image_url'] = None
                    self.ui_manager.display_message(f"GameController: Failed to update/generate image for scene '{response_data.get('scene_id')}'.", "warning")
                # --- End Image Generation for action outcome ---

                if new_scene_id and new_scene_id != current_scene_id_from_gwhr: # LLM decided to change scene
                    self.ui_manager.display_message(f"GameController: Transitioning to new scene: {new_scene_id}", "info")
                    self.gwhr.update_state({'current_scene_data': response_data})
                    self.ui_manager.display_scene(response_data)
                elif new_scene_id == current_scene_id_from_gwhr and response_data.get('narrative'): # Update to current scene (full refresh)
                    self.ui_manager.display_message(f"GameController: Current scene '{current_scene_id_from_gwhr}' updated.", "info")
                    self.gwhr.update_state({'current_scene_data': response_data})
                    self.ui_manager.display_scene(response_data) # Display the updated scene
                elif response_data.get('narrative_update'): # A specific narrative update for current scene
                    # This path might need more fleshing out if LLM is expected to send *only* narrative_update
                    # and not a full scene. The image logic above assumes response_data is the new full scene data.
                    # If it's just a delta, image wouldn't typically change unless also in delta.
                    self.ui_manager.display_narrative(response_data.get('narrative_update',''))
                    # If only narrative_update, current_scene_data in GWHR is not updated with response_data here.
                    # This means the image displayed would be the old one. This might be desired.
                    # For now, we assume LLM sends full scene data if image is to change.
                else: # Fallback or unrecognized partial update
                    self.ui_manager.display_message("GameController: Action resulted in a minor or unclear update. Re-displaying current scene context.", "info")
                    self.ui_manager.display_scene(self.gwhr.get_data_store().get('current_scene_data', {}))

                # --- Player Growth/Update Processing ---
                if 'player_updates' in response_data:
                    updates_to_log = []
                    # Get a mutable copy of player_state from GWHR to modify
                    # Note: get_data_store() returns a deepcopy, so we're modifying a copy.
                    # We need to explicitly save it back to GWHR if changes are made.
                    # A more direct approach might be: player_state_ref = self.gwhr.data_store['player_state']
                    # But to respect GWHR's interface providing copies, let's get, modify, then update.
                    current_player_state_copy = self.gwhr.get_data_store().get('player_state', {})
                    player_state_modified = False

                    # Process attribute updates
                    if 'attributes' in response_data['player_updates']:
                        attributes_updates = response_data['player_updates']['attributes']
                        if isinstance(attributes_updates, dict):
                            player_attributes = current_player_state_copy.setdefault('attributes', {})
                            for attr, change in attributes_updates.items():
                                if attr in player_attributes: # Only update existing attributes
                                    current_value = player_attributes[attr]
                                    try:
                                        new_value = current_value # Default if change is invalid
                                        if isinstance(change, str):
                                            if change.startswith('+'):
                                                new_value = current_value + int(change[1:])
                                            elif change.startswith('-'):
                                                new_value = current_value - int(change[1:])
                                            else: # Absolute value
                                                new_value = int(change)
                                        elif isinstance(change, (int, float)): # Absolute value
                                            new_value = int(change) # cast to int just in case
                                        else:
                                            self.ui_manager.display_message(f"Warning: Unrecognized attribute change format for {attr}: {change}", "warning")
                                            continue

                                        player_attributes[attr] = new_value
                                        player_state_modified = True
                                        update_msg = f"Attribute {attr} changed from {current_value} to {new_value}."
                                        self.ui_manager.display_message(update_msg, "growth")
                                        updates_to_log.append(update_msg)
                                    except ValueError:
                                        self.ui_manager.display_message(f"Warning: Invalid value for attribute change {attr}: {change}", "warning")
                                else:
                                    self.ui_manager.display_message(f"Warning: Attempt to update unknown attribute {attr}.", "warning")
                        else:
                            self.ui_manager.display_message(f"Warning: Malformed 'attributes' in player_updates (not a dict): {attributes_updates}", "warning")

                    # Process skill updates
                    if 'skills_learned' in response_data['player_updates']:
                        skills_to_learn_list = response_data['player_updates']['skills_learned']
                        if isinstance(skills_to_learn_list, list):
                            player_skills = current_player_state_copy.setdefault('skills', [])
                            for skill_to_learn in skills_to_learn_list:
                                if isinstance(skill_to_learn, dict) and 'name' in skill_to_learn:
                                    existing_skill = next((s for s in player_skills if s.get('name') == skill_to_learn['name']), None)
                                    if not existing_skill:
                                        # Ensure default level if not provided
                                        skill_to_learn.setdefault('level', 1)
                                        player_skills.append(skill_to_learn) # skill_to_learn is a dict
                                        player_state_modified = True
                                        update_msg = f"New skill learned: {skill_to_learn['name']} (Level {skill_to_learn.get('level', 1)})!"
                                        self.ui_manager.display_message(update_msg, "growth")
                                        updates_to_log.append(update_msg)
                                else:
                                    self.ui_manager.display_message(f"Warning: Malformed skill_learned entry: {skill_to_learn}", "warning")
                        else:
                             self.ui_manager.display_message(f"Warning: Malformed 'skills_learned' in player_updates (not a list): {skills_to_learn_list}", "warning")

                    # Process inventory updates
                    if 'inventory_updates' in response_data['player_updates']:
                        inventory_changes = response_data['player_updates']['inventory_updates']
                        if isinstance(inventory_changes, dict):
                            player_inventory = current_player_state_copy.setdefault('inventory', [])
                            if 'add' in inventory_changes and isinstance(inventory_changes['add'], list):
                                for item_to_add in inventory_changes['add']:
                                    if isinstance(item_to_add, dict) and 'id' in item_to_add and 'name' in item_to_add and 'quantity' in item_to_add:
                                        existing_item = next((item for item in player_inventory if item.get('id') == item_to_add['id']), None)
                                        if existing_item:
                                            existing_item['quantity'] = existing_item.get('quantity', 0) + item_to_add['quantity']
                                        else:
                                            player_inventory.append(item_to_add) # item_to_add is a dict
                                        player_state_modified = True
                                        update_msg = f"Obtained: {item_to_add['name']} (x{item_to_add['quantity']})."
                                        self.ui_manager.display_message(update_msg, "growth")
                                        updates_to_log.append(update_msg)
                                    else:
                                        self.ui_manager.display_message(f"Warning: Malformed item_to_add entry: {item_to_add}", "warning")
                            # TODO: Implement 'remove' logic similarly if needed
                            # if 'remove' in inventory_changes ...
                        else:
                            self.ui_manager.display_message(f"Warning: Malformed 'inventory_updates' in player_updates (not a dict): {inventory_changes}", "warning")

                    if player_state_modified and updates_to_log: # Only update GWHR if actual changes happened
                        self.gwhr.update_state({'player_state': current_player_state_copy})
                        self.gwhr.log_event(f"Player growth/update: {'; '.join(updates_to_log)}", event_type="player_update")
                # --- End Player Growth/Update Processing ---

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
                interactive_choices = current_scene_data.get('interactive_elements', [])

                # Display scene first, which now includes the (M) Game Menu hint
                self.ui_manager.display_scene(current_scene_data)

                if not interactive_choices: # Check after display_scene, as scene might say "no actions"
                    self.ui_manager.display_message("No interactive actions presented by the scene. The story might require a different approach or this path ends here.", "info")
                    self.current_game_state = "GAME_OVER" # Or some other state if game can continue without choices
                    self.gwhr.log_event("Game ended: No interactive choices available in scene.", event_type="game_flow_end")
                    break

                raw_command = input("Your command (e.g., 1, 2, ..., or M for Menu): ").strip().lower()

                if raw_command == 'm':
                    self.handle_game_menu()
                    self.ui_manager.display_message("\n--- Returning to game ---", "info")
                    # Re-display current scene after menu closes to refresh context for player
                    refreshed_scene_data = self.gwhr.get_data_store().get('current_scene_data', {})
                    # self.ui_manager.display_scene(refreshed_scene_data) # This would re-print the menu hint.
                    # The loop will re-enter AWAITING_PLAYER_ACTION and call display_scene.
                    # So, no explicit re-display here is needed, just let the loop continue.
                    continue # Continue to next iteration of game_loop to re-evaluate state and display scene
                else:
                    action_id = self.validate_and_get_action_id(raw_command, interactive_choices)
                    if action_id:
                        self.process_player_action(action_type="interact_element", action_detail=action_id)
                    else:
                        self.ui_manager.display_message(f"Invalid command: '{raw_command}'. Please enter a valid action number or 'M' for the menu.", "error")
                        # Game state remains AWAITING_PLAYER_ACTION, loop will re-prompt after re-displaying scene.

            elif self.current_game_state == "GAME_OVER":
                break

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
