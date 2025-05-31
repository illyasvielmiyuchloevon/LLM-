class GameEngine:
    def __init__(self):
        self.world_state = {}
        self.game_loop_running = False

    def start_game_loop(self):
        self.game_loop_running = True
        print("GameEngine: Game loop started.")
