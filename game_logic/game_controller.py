from api.api_key_manager import ApiKeyManager
from ui.ui_manager import UIManager
import json # For LLM response parsing
import time # For game loop delay
# from api.api_key_manager import ApiKeyManager # Redundant
# from ui.ui_manager import UIManager # Redundant
from engine.model_selector import ModelSelector
from engine.adventure_setup import AdventureSetup
from engine.gwhr import GWHR 
from api.llm_interface import LLMInterface 
import copy # For deepcopying NPC data for dialogue session

# GameEngine will be imported here later when needed

class GameController:
    def __init__(self, api_key_manager: ApiKeyManager, ui_manager: UIManager, 
                 model_selector: ModelSelector, adventure_setup: AdventureSetup, 
                 gwhr: GWHR, llm_interface: LLMInterface): 
        self.api_key_manager = api_key_manager
        self.ui_manager = ui_manager
        self.model_selector = model_selector
        self.adventure_setup = adventure_setup
        self.gwhr = gwhr 
        self.llm_interface = llm_interface 
        self.current_game_state: str = "INIT" 
        self.active_combat_data: dict = {} 
        # self.game_engine will be initialized later

    def request_and_validate_api_key(self) -> bool:
        self.ui_manager.show_api_key_screen()
        key_input = input() 
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
        preference_text = self.adventure_setup.request_adventure_preference()
        if preference_text:
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
            self.gwhr.initialize(world_data_dict)
            retrieved_title = self.gwhr.get_data_store().get('world_title', 'N/A')
            self.ui_manager.display_message(f"GameController: GWHR has been initialized. World Title from GWHR: '{retrieved_title}'.", "info")
            return True
        else:
            self.ui_manager.display_message("GameController: Failed to generate or parse World Conception Document. GWHR not initialized.", "error")
            return False

    def unlock_knowledge_entry(self, source_type: str, source_detail: str, context_prompt_hint: str):
        self.ui_manager.display_message(f"Attempting to unlock knowledge based on: {context_prompt_hint}...", "info")
        llm_prompt = (
            f"Context Hint: {context_prompt_hint}\n"
            f"Source Type: {source_type}\n"
            f"Source Detail: {source_detail}\n"
            f"Task: Generate a new Knowledge Codex entry based on this discovery. The entry should be factual and expand on the hint. "
            f"Output JSON with fields: 'knowledge_id' (string, unique, derived from context_prompt_hint, e.g., 'ancient_runes_translation_codex'), "
            f"'title' (string, concise title for the codex entry), "
            f"'content' (string, detailed textual content of the codex entry, 2-3 sentences), "
            f"'source_type' (string, echo back the provided source_type), "
            f"'source_detail' (string, echo back the provided source_detail)."
        )
        model_id = self.model_selector.get_selected_model()
        if not model_id:
            self.ui_manager.display_message("GameController: Error - No model selected for codex generation.", "error")
            return
        json_str = self.llm_interface.generate(llm_prompt, model_id, 'codex_entry_generation')
        if json_str:
            try:
                entry_data = json.loads(json_str)
                kid = entry_data.get('knowledge_id')
                if not kid:
                    self.ui_manager.display_message("GameController: Error - Codex entry from LLM missing ID.", "error")
                    return
                all_codex_entries = copy.deepcopy(self.gwhr.get_data_store().get('knowledge_codex', {}))
                if kid in all_codex_entries:
                    self.ui_manager.display_message(f"Note: Knowledge '{entry_data.get('title', kid)}' already discovered.", "info")
                    return
                entry_data.setdefault('title', 'Untitled Discovery')
                entry_data.setdefault('content', 'Further details are yet to be understood.')
                entry_data.setdefault('source_type', source_type)
                entry_data.setdefault('source_detail', source_detail)
                all_codex_entries[kid] = entry_data
                self.gwhr.update_state({'knowledge_codex': all_codex_entries})
                self.ui_manager.display_message(f"New Knowledge Unlocked: {entry_data.get('title', kid)}!", "growth")
                self.gwhr.log_event(
                    f"Knowledge unlocked: {entry_data.get('title', kid)} (ID: {kid})", 
                    event_type="knowledge_unlock", payload=entry_data)
            except json.JSONDecodeError as e:
                self.ui_manager.display_message(f"GameController: Error parsing codex entry from LLM: {e}", "error")
        else:
            self.ui_manager.display_message("GameController: Failed to generate codex entry from LLM.", "error")

    def initiate_combat(self, npc_ids_to_engage: list):
        self.current_game_state = "IN_COMBAT"
        self.ui_manager.display_message("Combat initiated!", "info")
        player_gwhr_state = self.gwhr.get_data_store().get('player_state', {})
        player_attrs = player_gwhr_state.get('attributes', {})
        self.active_combat_data = {
            'turn': 0,
            'player': {
                'id': 'player', 'name': 'Player',
                'current_hp': player_attrs.get('current_hp', 100), 'max_hp': player_attrs.get('max_hp', 100),
                'attack_power': player_attrs.get('attack_power', 10), 'defense_power': player_attrs.get('defense_power', 5),
                'evasion_chance': player_attrs.get('evasion_chance', 0.1), 'hit_chance': player_attrs.get('hit_chance', 0.8)
            },
            'npcs': [],
            'last_turn_player_strategies': [
                {"id": "standard_attack", "name": "Standard Attack"}, 
                {"id": "power_attack", "name": "Power Attack (Low Hit, High Dmg)"},
                {"id": "quick_attack", "name": "Quick Attack (High Hit, Low Dmg)"},
                {"id": "defend", "name": "Defend"}, 
                {"id": "try_flee", "name": "Attempt to Flee"}
            ], 
            'combat_ended': False, 'victor': None, 'final_summary_narrative': ''
        }
        all_gwhr_npcs = self.gwhr.get_data_store().get('npcs', {})
        for npc_id in npc_ids_to_engage:
            npc_gwhr_data = all_gwhr_npcs.get(npc_id)
            if not npc_gwhr_data:
                self.ui_manager.display_message(f"Warning: NPC {npc_id} not found for combat.", "warning"); continue
            npc_attrs = npc_gwhr_data.get('attributes', {})
            self.active_combat_data['npcs'].append({
                'id': npc_id, 'name': npc_gwhr_data.get('name', npc_id),
                'current_hp': npc_attrs.get('current_hp', 50), 'max_hp': npc_attrs.get('max_hp', 50),
                'attack_power': npc_attrs.get('attack_power', 8), 'defense_power': npc_attrs.get('defense_power', 3),
                'evasion_chance': npc_attrs.get('evasion_chance', 0.05), 'hit_chance': npc_attrs.get('hit_chance', 0.7),
                'original_gwhr_data_snapshot': copy.deepcopy(npc_gwhr_data)
            })
        if not self.active_combat_data['npcs']:
            self.ui_manager.display_message("No valid opponents found to engage in combat.", "error"); self.current_game_state = "AWAITING_PLAYER_ACTION"; self.active_combat_data = {}; return
        self.gwhr.log_event(f"Combat started against: {[npc['name'] for npc in self.active_combat_data['npcs']]}", event_type="combat_start")
        self.combat_loop()

    def combat_loop(self):
        while self.current_game_state == "IN_COMBAT":
            self.active_combat_data['turn'] += 1
            self.ui_manager.display_message(f"\n--- Combat Turn {self.active_combat_data['turn']} ---", "info")
            player_combat_data = self.active_combat_data['player']
            active_npc_combatants = [npc for npc in self.active_combat_data['npcs'] if npc.get('current_hp', 0) > 0]
            npc_combatants_info_for_ui = [{'name': n['name'], 'hp': n['current_hp'], 'max_hp': n['max_hp'], 'id': n['id']} for n in active_npc_combatants]
            if not npc_combatants_info_for_ui and not self.active_combat_data.get('combat_ended'):
                 self.ui_manager.display_message("All opponents appear to be defeated!", "info")
                 self.active_combat_data['combat_ended'] = True; self.active_combat_data['victor'] = 'player'
                 self.active_combat_data.setdefault('final_summary_narrative', "With no more foes standing, the battle ends.")
            self.ui_manager.show_combat_interface(player_combat_data['current_hp'], player_combat_data['max_hp'], npc_combatants_info_for_ui)
            if self.active_combat_data.get('combat_ended'):
                self.ui_manager.show_combat_results(self.active_combat_data.get('final_summary_narrative', "The dust settles."), self.active_combat_data.get('victor'))
                final_player_hp = self.active_combat_data['player']['current_hp']
                player_state_gwhr = copy.deepcopy(self.gwhr.get_data_store().get('player_state', {}))
                player_state_gwhr.setdefault('attributes', {})['current_hp'] = final_player_hp
                self.gwhr.update_state({'player_state': player_state_gwhr})
                npcs_gwhr_full_update = copy.deepcopy(self.gwhr.get_data_store().get('npcs', {}))
                for npc_combat_data in self.active_combat_data['npcs']:
                    npc_id_to_update = npc_combat_data['id']
                    if npc_id_to_update in npcs_gwhr_full_update:
                        restored_npc_data = copy.deepcopy(npc_combat_data['original_gwhr_data_snapshot'])
                        restored_npc_data.setdefault('attributes', {})['current_hp'] = npc_combat_data['current_hp']
                        if npc_combat_data['current_hp'] <= 0: restored_npc_data['status'] = 'defeated'
                        npcs_gwhr_full_update[npc_id_to_update] = restored_npc_data
                    else: 
                         npcs_gwhr_full_update[npc_id_to_update] = npc_combat_data['original_gwhr_data_snapshot']
                         npcs_gwhr_full_update[npc_id_to_update].setdefault('attributes',{})['current_hp'] = npc_combat_data['current_hp']
                         if npc_combat_data['current_hp'] <= 0: npcs_gwhr_full_update[npc_id_to_update]['status'] = 'defeated'
                if npcs_gwhr_full_update: self.gwhr.update_state({'npcs': npcs_gwhr_full_update})
                self.gwhr.log_event(f"Combat ended. Victor: {self.active_combat_data.get('victor', 'Unknown')}. Summary: {self.active_combat_data.get('final_summary_narrative', '')}", event_type="combat_end", payload={'summary': self.active_combat_data.get('final_summary_narrative')})
                self.current_game_state = "AWAITING_PLAYER_ACTION"; self.active_combat_data = {}
                current_scene_data_after_combat = self.gwhr.get_data_store().get('current_scene_data', {})
                self.ui_manager.display_scene(current_scene_data_after_combat); break
            available_strategies = self.active_combat_data.get('last_turn_player_strategies', [{"id": "standard_attack", "name": "Standard Attack"}])
            player_chosen_strategy_id = self.ui_manager.present_combat_strategies(available_strategies)
            if not player_chosen_strategy_id: player_chosen_strategy_id = "defend"
            self.process_combat_turn(player_chosen_strategy_id)
            time.sleep(0.1)

    def process_combat_turn(self, player_strategy_id: str):
        self.ui_manager.display_message(f"Processing your strategy: {player_strategy_id}...", "info")
        active_npcs_for_prompt = [npc for npc in self.active_combat_data.get('npcs', []) if npc.get('current_hp', 0) > 0]
        prompt_combatants_state = [{'id': 'player', 'hp': self.active_combat_data['player']['current_hp'], **{k:v for k,v in self.active_combat_data['player'].items() if k in ['attack_power','defense_power','evasion_chance','hit_chance']}}]
        for npc_data in active_npcs_for_prompt:
            prompt_combatants_state.append({'id': npc_data['id'], 'name': npc_data['name'], 'hp': npc_data['current_hp'], **{k:v for k,v in npc_data.items() if k in ['attack_power','defense_power','evasion_chance','hit_chance']}})
        llm_prompt = (
            f"Combat Turn: {self.active_combat_data['turn']}\nPlayer chose strategy: '{player_strategy_id}'.\n"
            f"Current Combatants State (active ones): {json.dumps(prompt_combatants_state)}\n\n"
            f"Task: Based on player's chosen strategy and current combatant states, determine the detailed outcome of this combat turn. Narrate the action and its results. Calculate HP changes for all affected combatants. Decide if the combat has ended (e.g., player defeated, or all NPCs defeated). Provide feedback on the player's strategy if appropriate. Suggest 3-4 available strategies for the player's next turn if combat continues. Output a single valid JSON object with fields: 'turn_summary_narrative' (string), 'player_hp_change' (int), 'npc_hp_changes' (list of {{'npc_id': string, 'hp_change': int}}), 'combat_ended' (boolean), 'victor' (string: 'player', 'npc', 'draw', or null), 'player_strategy_feedback' (optional string), and 'available_player_strategies' (list of {{'id': string, 'name': string}} objects for next turn if combat is not ended).")
        model_id = self.model_selector.get_selected_model()
        if not model_id:
            self.ui_manager.display_message("GameController: CRITICAL - No model selected for LLM call in combat!", "error")
            self.active_combat_data.update({'combat_ended': True, 'victor': 'error_no_model', 'final_summary_narrative': 'Critical Error: No LLM model available for combat simulation.'}); return
        outcome_json_str = self.llm_interface.generate(llm_prompt, model_id, expected_response_type='combat_turn_outcome')
        outcome_data = {}
        if not outcome_json_str:
            self.ui_manager.display_message("GameController: LLM failed to provide combat outcome. Assuming a glancing blow...", "error")
            outcome_data = {"turn_summary_narrative": "The combatants eye each other warily; a tense moment passes.", "player_hp_change": 0, "npc_hp_changes": [], "combat_ended": False, "available_player_strategies": self.active_combat_data.get('last_turn_player_strategies')}
        else:
            try: outcome_data = json.loads(outcome_json_str)
            except json.JSONDecodeError as e:
                self.ui_manager.display_message(f"GameController: Error parsing combat outcome JSON: {e}. Assuming glancing blows.", "error")
                outcome_data = {"turn_summary_narrative": f"Confusion (LLM Error: {e}). No clear result.", "player_hp_change": 0, "npc_hp_changes": [], "combat_ended": False, "available_player_strategies": self.active_combat_data.get('last_turn_player_strategies')}
        player_c_data = self.active_combat_data['player']
        player_c_data['current_hp'] = max(0, player_c_data['current_hp'] + outcome_data.get('player_hp_change', 0))
        for npc_hp_update in outcome_data.get('npc_hp_changes', []):
            for npc_combatant in self.active_combat_data['npcs']:
                if npc_combatant['id'] == npc_hp_update.get('npc_id'):
                    npc_combatant['current_hp'] = max(0, npc_combatant['current_hp'] + npc_hp_update.get('hp_change', 0)); break
        self.active_combat_data.update({
            'last_turn_player_strategies': outcome_data.get('available_player_strategies', self.active_combat_data.get('last_turn_player_strategies')),
            'combat_ended': outcome_data.get('combat_ended', False), 'victor': outcome_data.get('victor'),
            'final_summary_narrative': outcome_data.get('turn_summary_narrative', "The turn ends.")
        })
        self.gwhr.log_event(f"Combat Turn {self.active_combat_data['turn']} Details: {outcome_data.get('turn_summary_narrative','')}", event_type="combat_turn_detail", payload=copy.deepcopy(outcome_data))
        self.ui_manager.display_combat_narrative(outcome_data.get('turn_summary_narrative', "No narrative for turn."))
        if outcome_data.get('player_strategy_feedback'): self.ui_manager.display_message(f"Feedback: {outcome_data.get('player_strategy_feedback')}", "info")
        if not self.active_combat_data['combat_ended']:
            if player_c_data['current_hp'] <= 0:
                self.active_combat_data.update({'combat_ended': True, 'victor': 'npc', 'final_summary_narrative': self.active_combat_data.get('final_summary_narrative','') + " Player has fallen!"})
                self.gwhr.log_event("Player defeated by HP loss.", event_type="combat_end_condition")
            current_live_npcs = [n for n in self.active_combat_data['npcs'] if n['current_hp'] > 0]
            if not current_live_npcs and self.active_combat_data['npcs']:
                self.active_combat_data.update({'combat_ended': True, 'victor': 'player', 'final_summary_narrative': self.active_combat_data.get('final_summary_narrative','') + " All opponents defeated!"})
                self.gwhr.log_event("All NPCs defeated by HP loss.", event_type="combat_end_condition")

    def evaluate_environmental_puzzle_action(self, puzzle_id: str, element_id_acted_on: str, item_id_used: str = None):
        self.current_game_state = "PROCESSING_ACTION" 
        self.ui_manager.display_message(f"Interacting with puzzle: '{puzzle_id}', element: '{element_id_acted_on}'...", "info")
        self.gwhr.log_event(f"Player interacts with puzzle '{puzzle_id}', element '{element_id_acted_on}'" + (f" using item '{item_id_used}'" if item_id_used else ""), event_type="puzzle_interaction")
    
        all_puzzle_states = self.gwhr.get_data_store().get('environmental_puzzle_log', {})
        current_puzzle_specific_state = copy.deepcopy(all_puzzle_states.get(puzzle_id, {})) 
    
        current_scene_data = self.gwhr.get_data_store().get('current_scene_data', {})
        scene_context_for_prompt = {
            "scene_id": current_scene_data.get('scene_id'),
            "narrative_snippet": current_scene_data.get('narrative', '')[:150],
            "relevant_elements_in_scene_names": [el.get('name') for el in current_scene_data.get('interactive_elements', []) if el.get('puzzle_id') == puzzle_id]
        }
        llm_prompt = (
            f"Context: Player is interacting with an environmental puzzle.\n"
            f"Puzzle ID: {puzzle_id}\n"
            f"Element Acted Upon ID: {element_id_acted_on}\n" 
            f"Item Used ID: {item_id_used if item_id_used else 'None'}\n"
            f"Current Known State of this Puzzle (elements_state, clues_found, status): {json.dumps(current_puzzle_specific_state)}\n"
            f"Relevant Scene Context: {json.dumps(scene_context_for_prompt)}\n\n"
            f"Task: Evaluate this puzzle interaction. Output a single valid JSON object with fields: "
            f"'puzzle_id' (string, echo back the puzzle_id), 'action_feedback_narrative' (string, immediate result of action), "
            f"'puzzle_state_changed' (boolean), 'updated_puzzle_elements_state' (optional dictionary of specific element state changes, e.g., {{'element_X': 'new_value'}}), "
            f"'new_clues_revealed' (optional list of strings or clue_ids representing new information gained), 'puzzle_solved' (boolean), "
            f"and 'solution_narrative' (optional string if solved)."
        )
        model_id = self.model_selector.get_selected_model()
        if not model_id: 
            self.ui_manager.display_message("GameController: CRITICAL: No model selected for puzzle evaluation!", "error"); self.current_game_state = "AWAITING_PLAYER_ACTION"; return
        eval_json_str = self.llm_interface.generate(llm_prompt, model_id, 'environmental_puzzle_solution_eval')
        eval_data = {}
        if not eval_json_str:
            self.ui_manager.display_message("The puzzle doesn't seem to react (LLM error).", "error")
            eval_data = {"action_feedback_narrative": "You interact, but nothing definitive happens this time."}
        else:
            try: eval_data = json.loads(eval_json_str)
            except json.JSONDecodeError as e:
                self.ui_manager.display_message(f"The puzzle's reaction is confusing (JSON Error: {e}).", "error")
                eval_data = {"action_feedback_narrative": "A strange energy crackles, but the effect is unclear."}
        feedback_narrative = eval_data.get('action_feedback_narrative', "You interact with the puzzle element.")
        self.ui_manager.display_narrative(feedback_narrative) 
        puzzle_state_changed_by_action = eval_data.get('puzzle_state_changed', False)
        if puzzle_state_changed_by_action:
            updated_elements_from_llm = eval_data.get('updated_puzzle_elements_state', {})
            if not isinstance(current_puzzle_specific_state.get('elements_state'), dict): current_puzzle_specific_state['elements_state'] = {}
            current_puzzle_specific_state['elements_state'].update(updated_elements_from_llm)
            new_clues_from_llm = eval_data.get('new_clues_revealed', [])
            if new_clues_from_llm: 
                current_clues = current_puzzle_specific_state.setdefault('clues_found', [])
                for clue in new_clues_from_llm:
                    if clue not in current_clues: current_clues.append(clue)
                self.ui_manager.display_message(f"New clues found for puzzle '{puzzle_id}': {', '.join(new_clues_from_llm)}", "info")
            all_puzzle_states[puzzle_id] = current_puzzle_specific_state 
            self.gwhr.update_state({'environmental_puzzle_log': all_puzzle_states})
            self.gwhr.log_event(f"Puzzle '{puzzle_id}' state changed. Elements: {updated_elements_from_llm}. Clues: {new_clues_from_llm}.", event_type="puzzle_update", payload=eval_data)
            # TODO: Conceptual hookup for knowledge from puzzle clues
            # if new_clues_from_llm:
            #    for clue_item in new_clues_from_llm:
            #        if isinstance(clue_item, dict) and 'topic_id' in clue_item:
            #             self.unlock_knowledge_entry("puzzle_clue", f"Puzzle {puzzle_id}", clue_item.get('summary', clue_item.get('topic_id')))
            #        elif isinstance(clue_item, str):
            #             self.unlock_knowledge_entry("puzzle_clue_text", f"Puzzle {puzzle_id}", clue_item)

        if eval_data.get('puzzle_solved', False):
            current_puzzle_specific_state['status'] = 'solved'
            all_puzzle_states[puzzle_id] = current_puzzle_specific_state
            self.gwhr.update_state({'environmental_puzzle_log': all_puzzle_states})
            solution_narrative_text = eval_data.get('solution_narrative', f"The puzzle '{puzzle_id}' has been solved!")
            self.ui_manager.display_narrative(solution_narrative_text)
            self.gwhr.log_event(f"Puzzle '{puzzle_id}' solved! Narrative: {solution_narrative_text}", event_type="puzzle_solved", payload=eval_data)
            # TODO: Conceptual hookup for knowledge from puzzle solution
            # if isinstance(eval_data.get('knowledge_from_solution'), list):
            #    for knowledge_item in eval_data.get('knowledge_from_solution'):
            #        self.unlock_knowledge_entry("puzzle_solution", f"Puzzle {puzzle_id}", knowledge_item.get('summary', knowledge_item.get('topic_id')))
        
        self.advance_time(1) 
        self.current_game_state = "AWAITING_PLAYER_ACTION"
        self.ui_manager.display_scene(self.gwhr.get_data_store().get('current_scene_data', {}))

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
            
            # Example conceptual hookup:
            if isinstance(dialogue_data.get('knowledge_revealed'), list):
                for knowledge_item in dialogue_data.get('knowledge_revealed'):
                    if isinstance(knowledge_item, dict) and 'topic_id' in knowledge_item and 'summary' in knowledge_item:
                        self.unlock_knowledge_entry(
                            source_type="dialogue", 
                            source_detail=f"NPC {npc_name} (ID: {npc_id})", 
                            context_prompt_hint=knowledge_item.get('summary', knowledge_item.get('topic_id'))
                        )

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

    def advance_time(self, duration: int = 1):
        current_time = self.gwhr.get_data_store().get('current_game_time', 0)
        new_time = current_time + duration
        self.gwhr.update_state({'current_game_time': new_time})
        self.gwhr.log_event(f"Time advanced by {duration} unit(s). New game time is {new_time}.", event_type="time_passage")
        
        self.check_and_update_time_based_events() # Call the new method

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
        # Fetch all necessary data ONCE before the loop for menu display
        gwhr_data = self.gwhr.get_data_store()
        player_state_for_menu = copy.deepcopy(gwhr_data.get('player_state', {}))
        codex_for_menu = copy.deepcopy(gwhr_data.get('knowledge_codex', {}))
        
        # UIManager.show_game_systems_menu expects player_state_data to potentially contain codex for UI
        # Let's prepare a combined dict for it, or adjust UIManager if direct passing is better.
        # Plan for UIManager (subtask 33) was: player_state_data.get('knowledge_codex_for_ui', {})
        # So, GameController must put it there.
        menu_display_data = player_state_for_menu # Start with player state
        menu_display_data['knowledge_codex_for_ui'] = codex_for_menu # Add codex under the expected key

        while True:
            # Pass the combined data structure
            # UIManager.display_knowledge_codex_ui returns a tuple (action_type, data) or None
            menu_result_tuple = self.ui_manager.show_game_systems_menu(menu_display_data)
            
            action_type = None
            # selected_data = None # Not used yet from codex UI return in this controller

            if isinstance(menu_result_tuple, tuple) and len(menu_result_tuple) == 2:
                # This was for display_knowledge_codex_ui, show_game_systems_menu returns simple string
                # menu_action_result, selected_data = menu_result_tuple
                pass # Not used for now as show_game_systems_menu returns simple string

            # show_game_systems_menu currently returns a simple string: 'close_menu' or 'show_menu_again'
            menu_action_result = menu_result_tuple 

            if menu_action_result == 'close_menu':
                break
            elif menu_action_result == 'show_menu_again':
                # Refresh data in case a sub-screen changed something (though current ones don't)
                # This is not strictly necessary if sub-screens are read-only.
                # player_state_for_menu = copy.deepcopy(self.gwhr.get_data_store().get('player_state', {}))
                # codex_for_menu = copy.deepcopy(self.gwhr.get_data_store().get('knowledge_codex', {}))
                # menu_display_data['player_state'] = player_state_for_menu # This key is not standard for UIManager
                # menu_display_data['knowledge_codex_for_ui'] = codex_for_menu
                # Actually, display_character_status etc. take player_state directly.
                # show_game_systems_menu takes the dict (player_state_data) and passes it to sub-screens.
                # The sub-screens like display_character_status_screen expect the *root* of this dict to be player_data.
                # So menu_display_data should BE player_state, augmented with knowledge_codex_for_ui.
                # Let's reconstruct it properly before each call to show_game_systems_menu if data can change within sub-screens.
                # For now, assuming sub-screens are read-only displays.
                continue 
            # No other actions from this menu result in direct game state changes yet handled here.

    def trigger_dynamic_event(self, event_id_hint: str, is_npc_driven: bool = False):
        self.ui_manager.display_message(f"A dynamic event '{event_id_hint}' is being triggered...", "info")
        
        current_time = self.gwhr.get_data_store().get('current_game_time', 0)
        llm_prompt = (
            f"Event Hint: {event_id_hint}\n"
            f"NPC Driven: {is_npc_driven}\n"
            f"Game Time: {current_time}\n"
            f"Task: Generate the outcome for this dynamic world event. The outcome should be surprising yet plausible. "
            f"Output JSON with fields: 'event_id' (string, can be a more specific ID derived from the hint), "
            f"'description' (string, narrative of what happens), "
            f"'effects_on_world' (list of strings, describing changes to game state, environment, or NPC status; these are for logging and potential future state changes), "
            f"'new_scene_id' (optional string, if the event forces an immediate scene change)."
        )
        
        model_id = self.model_selector.get_selected_model()
        if not model_id:
            self.ui_manager.display_message("GameController: Error - No model selected for dynamic event generation.", "error")
            return

        json_str = self.llm_interface.generate(llm_prompt, model_id, 'dynamic_event_outcome')

        if json_str:
            try:
                event_data = json.loads(json_str)
                description = event_data.get('description', 'An unexpected event occurred, but its nature is unclear.')
                
                self.ui_manager.display_dynamic_event_notification(description)
                
                # Log the full event data to dynamic_world_events_log in GWHR
                # GWHR's __init__ ensures dynamic_world_events_log is a list
                log_entry = {'timestamp': current_time, **event_data} # Add timestamp to the event data
                
                # Get a copy, append, then update_state to ensure deepcopy and proper handling by GWHR
                current_dwel = copy.deepcopy(self.gwhr.get_data_store().get('dynamic_world_events_log', []))
                current_dwel.append(log_entry)
                self.gwhr.update_state({'dynamic_world_events_log': current_dwel})
                
                self.gwhr.log_event(
                    f"Dynamic event: {event_data.get('event_id', event_id_hint)}. Outcome: {description}", 
                    event_type="dynamic_event", 
                    payload=event_data
                )

                # TODO: Advanced: Implement actual changes to game state based on event_data.get('effects_on_world')
                # e.g., modify GWHR's world_state, npcs, or environmental_puzzle_log.
                # For now, these effects are just logged.
        # TODO: Conceptual hookup for knowledge from dynamic events
        # if isinstance(event_data.get('knowledge_revealed_by_event'), list):
        #     for knowledge_item in event_data.get('knowledge_revealed_by_event'):
        #         self.unlock_knowledge_entry(
        #             source_type="dynamic_event",
        #             source_detail=event_data.get('event_id', event_id_hint),
        #             context_prompt_hint=knowledge_item.get('summary', knowledge_item.get('topic_id'))
        #         )

                new_scene_id_from_event = event_data.get('new_scene_id')
                if new_scene_id_from_event:
                    self.ui_manager.display_message(f"The event transitions to a new scene: {new_scene_id_from_event}", "info")
                    self.initiate_scene(new_scene_id_from_event) 
                else:
                    pass # State handling as before

            except json.JSONDecodeError as e:
                self.ui_manager.display_message(f"GameController: Error parsing dynamic event outcome from LLM: {e}", "error")
        else:
            self.ui_manager.display_message("GameController: Failed to generate dynamic event outcome from LLM.", "error")

    def check_and_update_time_based_events(self):
        current_time = self.gwhr.get_data_store().get('current_game_time', 0)
        
        # Example: Every 10 turns, chance of weather change
        if current_time > 0 and current_time % 10 == 0: # Trigger on turns 10, 20, 30...
            self.ui_manager.display_message("The air shifts... the weather might be changing.", "info")
            
            current_world_state = self.gwhr.get_data_store().get('world_state', {})
            current_weather = current_world_state.get('current_weather', {"condition":"unknown"}) # Get current weather
            
            llm_prompt = (
                f"Old Condition: {current_weather.get('condition','clear')}\n"
                f"Current Game Time: {current_time}\n" # Provide game time for context
                f"Task: Describe a plausible weather change based on the old condition. "
                f"Output JSON with fields: 'new_weather_condition' (e.g., 'rainy', 'foggy', 'sunny'), "
                f"'new_weather_intensity' (e.g., 'light', 'moderate', 'heavy'), "
                f"and 'weather_effects_description' (a narrative string for the player)."
            )
            model_id = self.model_selector.get_selected_model()
            if not model_id:
                self.ui_manager.display_message("GameController: Error - No model selected for weather update generation.", "error")
                return

            json_str = self.llm_interface.generate(llm_prompt, model_id, 'weather_update_description')
            
            if json_str:
                try:
                    weather_data = json.loads(json_str)
                    # Update GWHR: get a copy of world_state, update weather, then set it back
                    updated_world_state = copy.deepcopy(current_world_state) # Make a copy to modify
                    updated_world_state['current_weather'] = { # Replace with new weather data
                        "condition": weather_data.get('new_weather_condition', 'unchanged'),
                        "intensity": weather_data.get('new_weather_intensity', 'mild'),
                        "effects_description": weather_data.get('weather_effects_description', 'The weather remains difficult to discern.')
                    }
                    self.gwhr.update_state({'world_state': updated_world_state})
                    
                    self.ui_manager.display_dynamic_event_notification(
                        f"Weather changes: {weather_data.get('weather_effects_description', 'The atmosphere shifts.')}"
                    )
                    self.gwhr.log_event(
                        f"Weather changed to {weather_data.get('new_weather_condition', 'unknown')}, intensity {weather_data.get('new_weather_intensity', 'unknown')}.",
                        event_type="weather_change", 
                        payload=weather_data
                    )
                except json.JSONDecodeError as e:
                    self.ui_manager.display_message(f"GameController: Error parsing weather data from LLM: {e}", "error")
            else:
                self.ui_manager.display_message("GameController: LLM failed to describe weather change.", "error")
        
        # TODO: Add more time-based event triggers here if needed.

    def evaluate_environmental_puzzle_action(self, puzzle_id: str, element_id_acted_on: str, item_id_used: str = None):
        self.current_game_state = "PROCESSING_ACTION" 
        self.ui_manager.display_message(f"Interacting with puzzle: '{puzzle_id}', element: '{element_id_acted_on}'...", "info")
        self.gwhr.log_event(f"Player interacts with puzzle '{puzzle_id}', element '{element_id_acted_on}'" + (f" using item '{item_id_used}'" if item_id_used else ""), event_type="puzzle_interaction")
    
        all_puzzle_states = self.gwhr.get_data_store().get('environmental_puzzle_log', {})
        current_puzzle_specific_state = copy.deepcopy(all_puzzle_states.get(puzzle_id, {})) 
    
        current_scene_data = self.gwhr.get_data_store().get('current_scene_data', {})
        scene_context_for_prompt = {
            "scene_id": current_scene_data.get('scene_id'),
            "narrative_snippet": current_scene_data.get('narrative', '')[:150],
            "relevant_elements_in_scene_names": [el.get('name') for el in current_scene_data.get('interactive_elements', []) if el.get('puzzle_id') == puzzle_id]
        }
        llm_prompt = (
            f"Context: Player is interacting with an environmental puzzle.\n"
            f"Puzzle ID: {puzzle_id}\n"
            f"Element Acted Upon ID: {element_id_acted_on}\n" 
            f"Item Used ID: {item_id_used if item_id_used else 'None'}\n"
            f"Current Known State of this Puzzle (elements_state, clues_found, status): {json.dumps(current_puzzle_specific_state)}\n"
            f"Relevant Scene Context: {json.dumps(scene_context_for_prompt)}\n\n"
            f"Task: Evaluate this puzzle interaction. Output a single valid JSON object with fields: "
            f"'puzzle_id' (string, echo back the puzzle_id), 'action_feedback_narrative' (string, immediate result of action), "
            f"'puzzle_state_changed' (boolean), 'updated_puzzle_elements_state' (optional dictionary of specific element state changes, e.g., {{'element_X': 'new_value'}}), "
            f"'new_clues_revealed' (optional list of strings or clue_ids representing new information gained), 'puzzle_solved' (boolean), "
            f"and 'solution_narrative' (optional string if solved)."
        )
        model_id = self.model_selector.get_selected_model()
        if not model_id: 
            self.ui_manager.display_message("GameController: CRITICAL: No model selected for puzzle evaluation!", "error"); self.current_game_state = "AWAITING_PLAYER_ACTION"; return
        eval_json_str = self.llm_interface.generate(llm_prompt, model_id, 'environmental_puzzle_solution_eval')
        eval_data = {}
        if not eval_json_str:
            self.ui_manager.display_message("The puzzle doesn't seem to react (LLM error).", "error")
            eval_data = {"action_feedback_narrative": "You interact, but nothing definitive happens this time."}
        else:
            try: eval_data = json.loads(eval_json_str)
            except json.JSONDecodeError as e:
                self.ui_manager.display_message(f"The puzzle's reaction is confusing (JSON Error: {e}).", "error")
                eval_data = {"action_feedback_narrative": "A strange energy crackles, but the effect is unclear."}
        feedback_narrative = eval_data.get('action_feedback_narrative', "You interact with the puzzle element.")
        self.ui_manager.display_narrative(feedback_narrative) 
        puzzle_state_changed_by_action = eval_data.get('puzzle_state_changed', False)
        if puzzle_state_changed_by_action:
            updated_elements_from_llm = eval_data.get('updated_puzzle_elements_state', {})
            if not isinstance(current_puzzle_specific_state.get('elements_state'), dict): current_puzzle_specific_state['elements_state'] = {}
            current_puzzle_specific_state['elements_state'].update(updated_elements_from_llm)
            new_clues_from_llm = eval_data.get('new_clues_revealed', [])
            if new_clues_from_llm: 
                current_clues = current_puzzle_specific_state.setdefault('clues_found', [])
                for clue in new_clues_from_llm:
                    if clue not in current_clues: current_clues.append(clue)
                self.ui_manager.display_message(f"New clues found for puzzle '{puzzle_id}': {', '.join(new_clues_from_llm)}", "info")
            all_puzzle_states[puzzle_id] = current_puzzle_specific_state 
            self.gwhr.update_state({'environmental_puzzle_log': all_puzzle_states})
            self.gwhr.log_event(f"Puzzle '{puzzle_id}' state changed. Elements: {updated_elements_from_llm}. Clues: {new_clues_from_llm}.", event_type="puzzle_update", payload=eval_data)
            # TODO: Conceptual hookup for knowledge from puzzle clues
            # if new_clues_from_llm:
            #    for clue_item in new_clues_from_llm:
            #        if isinstance(clue_item, dict) and 'topic_id' in clue_item:
            #             self.unlock_knowledge_entry("puzzle_clue", f"Puzzle {puzzle_id}", clue_item.get('summary', clue_item.get('topic_id')))
            #        elif isinstance(clue_item, str):
            #             self.unlock_knowledge_entry("puzzle_clue_text", f"Puzzle {puzzle_id}", clue_item)

        if eval_data.get('puzzle_solved', False):
            current_puzzle_specific_state['status'] = 'solved'
            all_puzzle_states[puzzle_id] = current_puzzle_specific_state
            self.gwhr.update_state({'environmental_puzzle_log': all_puzzle_states})
            solution_narrative_text = eval_data.get('solution_narrative', f"The puzzle '{puzzle_id}' has been solved!")
            self.ui_manager.display_narrative(solution_narrative_text)
            self.gwhr.log_event(f"Puzzle '{puzzle_id}' solved! Narrative: {solution_narrative_text}", event_type="puzzle_solved", payload=eval_data)
            # TODO: Conceptual hookup for knowledge from puzzle solution
            # if isinstance(eval_data.get('knowledge_from_solution'), list):
            #    for knowledge_item in eval_data.get('knowledge_from_solution'):
            #        self.unlock_knowledge_entry("puzzle_solution", f"Puzzle {puzzle_id}", knowledge_item.get('summary', knowledge_item.get('topic_id')))
        
        self.advance_time(1) 
        self.current_game_state = "AWAITING_PLAYER_ACTION"
        self.ui_manager.display_scene(self.gwhr.get_data_store().get('current_scene_data', {}))

    # --- End of evaluate_environmental_puzzle_action ---
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

                # Add current weather to scene_data for display
                current_weather = self.gwhr.get_data_store().get('world_state', {}).get('current_weather', {})
                scene_data['current_weather_in_scene'] = copy.deepcopy(current_weather)

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
        elif chosen_element and chosen_element.get('type') == 'puzzle_element':
            puzzle_id = chosen_element.get('puzzle_id')
            element_acted_on_id = chosen_element.get('id') 
            item_used_id = None # Placeholder for now
            if puzzle_id and element_acted_on_id:
                self.evaluate_environmental_puzzle_action(puzzle_id, element_acted_on_id, item_used_id)
                return 
            else: 
                self.ui_manager.display_message("Error: Puzzle element data is incomplete for processing.", "error")
                self.current_game_state = "AWAITING_PLAYER_ACTION" 
                return
        
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

                # Add current weather to response_data before updating GWHR and displaying
                current_weather_for_action_outcome = self.gwhr.get_data_store().get('world_state', {}).get('current_weather', {})
                response_data['current_weather_in_scene'] = copy.deepcopy(current_weather_for_action_outcome)

                if new_scene_id and new_scene_id != current_scene_id_from_gwhr: # LLM decided to change scene
                    self.ui_manager.display_message(f"GameController: Transitioning to new scene: {new_scene_id}", "info")
                    self.gwhr.update_state({'current_scene_data': response_data}) # response_data now includes weather
                    self.ui_manager.display_scene(response_data)
                elif new_scene_id == current_scene_id_from_gwhr and response_data.get('narrative'): # Update to current scene (full refresh)
                    self.ui_manager.display_message(f"GameController: Current scene '{current_scene_id_from_gwhr}' updated.", "info")
                    self.gwhr.update_state({'current_scene_data': response_data}) # response_data now includes weather
                    self.ui_manager.display_scene(response_data) 
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
                # TODO: Conceptual hookup for knowledge from generic actions
                # if isinstance(response_data.get('knowledge_revealed_by_action'), list):
                #    for knowledge_item in response_data.get('knowledge_revealed_by_action'):
                #        self.unlock_knowledge_entry(
                #            source_type="action_outcome", 
                #            source_detail=f"Action on element {action_detail} in scene {current_scene_id_from_gwhr}", 
                #            context_prompt_hint=knowledge_item.get('summary', knowledge_item.get('topic_id'))
                #        )


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

[end of game_logic/game_controller.py]
