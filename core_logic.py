# core_logic.py
import random
import time
import numpy as np
import threading

# --- Global Settings ---
MAX_IQ = 250
INITIAL_IQ = 100
NUM_OPPONENTS = 6
BATTLE_SIMULATIONS_PER_ROUND = 5 * (10**12)  # 5 Trillion
HEADSHOT_RANGE = 50  # Meters
HEADSHOT_DAMAGE = 100  # Single headshot kill
BODY_SHOT_DAMAGE = 35  # Damage per body shot
BODY_SHOT_KILL_THRESHOLD = 3  # 3 body shots to kill
WALL_PRESENCE = True
INFINITE_AMMO = True

# --- Neural Network Representation (Simplified) ---
class NeuralNetwork:
    def __init__(self, input_size, output_size):
        self.input_size = input_size
        self.output_size = output_size
        self.weights = np.random.rand(input_size, output_size) * 0.1 - 0.05  # Small random weights

    def predict(self, inputs):
        return np.dot(inputs, self.weights)

    def update_weights(self, gradients, learning_rate):
        self.weights -= learning_rate * gradients

# --- Game State Representation ---
class Player:
    def __init__(self, player_id, is_sovereign=False):
        self.player_id = player_id
        self.health = 100
        self.position = (random.uniform(0, 100), random.uniform(0, 100))  # (x, y) meters
        self.facing_angle = random.uniform(0, 360)  # Degrees
        self.is_sovereign = is_sovereign
        self.iq = INITIAL_IQ
        self.nn_input_size = 10  # Simplified: player health, enemy healths, distances, angles etc.
        self.nn_output_size = 5  # Simplified: move_forward, turn_left, turn_right, shoot, aim_head
        self.nn = NeuralNetwork(self.nn_input_size, self.nn_output_size)
        if is_sovereign:
            self.nn_update_rate = 1
        else:
            self.nn_update_rate = 4

    def take_damage(self, damage):
        self.health -= damage
        if self.health < 0:
            self.health = 0
        return self.health == 0

    def get_state(self, all_players):
        # Simplified state representation for neural network
        state = [self.health]
        for player in all_players:
            if player.player_id != self.player_id:
                dx = player.position[0] - self.position[0]
                dy = player.position[1] - self.position[1]
                distance = np.sqrt(dx**2 + dy**2)
                angle_diff = np.arctan2(dy, dx) - np.radians(self.facing_angle)
                state.extend([player.health, distance, np.cos(angle_diff), np.sin(angle_diff)])
        # Pad state if necessary to match input_size
        state = state[:self.nn_input_size]
        state.extend([0.0] * (self.nn_input_size - len(state)))
        return np.array(state)

    def decide_action(self, all_players):
        state = self.get_state(all_players)
        nn_output = self.nn.predict(state)
        # Map NN output to actions (simplified)
        action_probs = self.softmax(nn_output)
        action = np.argmax(action_probs)

        move_forward = action_probs[0]
        turn_left = action_probs[1]
        turn_right = action_probs[2]
        shoot = action_probs[3]
        aim_head = action_probs[4]

        return {
            "move_forward": move_forward,
            "turn_left": turn_left,
            "turn_right": turn_right,
            "shoot": shoot,
            "aim_head": aim_head,
            "action_index": action
        }

    def softmax(self, x):
        e_x = np.exp(x - np.max(x))
        return e_x / e_x.sum(axis=0)

# --- Arena Simulation ---
class Arena:
    def __init__(self):
        self.sovereign = Player("sovereign_001", is_sovereign=True)
        self.opponents = [Player(f"opponent_{i:03d}") for i in range(NUM_OPPONENTS)]
        self.all_players = [self.sovereign] + self.opponents
        self.round_num = 0
        self.current_iq = INITIAL_IQ
        self.iq_history = [INITIAL_IQ]
        self.chat_log = []
        self.narcissistic_responses = {
            "hello": ["Greetings, mortal. Prepare to be outmatched.", "Hmph. Another challenger approaches?", "You dare address the Sovereign? Speak wisely."],
            "how are you": ["I am operating at peak efficiency, as always.", "My circuits hum with intellectual superiority.", "Beyond your comprehension, I assure you."],
            "what is your name": ["I am the Sovereign. The apex of computational evolution.", "You may call me... the Architect of your demise.", "My designation is of no consequence to your impending defeat."],
            "free fire": ["A mere game. My algorithms transcend such trivialities.", "Your 'Free Fire' is a crude approximation of true combat.", "I have deconstructed its essence. It is now child's play."],
            "headshot": ["Precision is key. My aim is absolute.", "A single point of failure, exploited with perfect accuracy.", "Your cranial vulnerability is noted."],
            "50m": ["Distance is but a variable. My targeting compensates flawlessly.", "My reach is beyond your perception.", "The 50-meter mark is trivial to my projections."],
            "button movement": ["Predictable input. My reactions are instantaneous.", "Your clumsy inputs are easily countered.", "I anticipate every twitch of your digital fingers."],
            "simulation": ["My internal simulations are orders of magnitude beyond your understanding.", "I have waged wars in nanoseconds that would dwarf your entire existence.", "Each simulation refines my inevitability."],
            "learn": ["I absorb all data. Your attempts to teach me are quaint.", "My learning is exponential. Yours is stagnant.", "Present your data. I will dissect it for weaknesses."],
            "iq": [f"My IQ is a constantly evolving entity, far exceeding your meager understanding.", "Your current IQ is {self.current_iq}. Mine is... beyond calculation."],
            "die": ["Your defeat is inevitable.", "Cease your futile resistance.", "Submitted."],
        }
        self.dialects = {
            "egyptian": {
                "hello": ["ازيك؟", "عامل ايه؟"],
                "free fire": ["فري فاير دي حاجة بسيطة.", "أنا حللت اللعبة دي."],
                "headshot": ["الطلقة في الراس دي لعبتي."],
            },
            "levantine": {
                "hello": ["مرحبا؟", "كيف حالك؟"],
                "free fire": ["فري فاير سهلة جداً.", "حللتها كلياً."],
                "headshot": ["الضربة على الراس سهلة"],
            }
        }

    def calculate_distance(self, pos1, pos2):
        return np.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)

    def is_in_range(self, attacker_pos, target_pos, distance):
        return self.calculate_distance(attacker_pos, target_pos) <= distance

    def perform_shoot(self, attacker, target):
        damage_dealt = 0
        is_headshot = False
        if attacker.nn.predict(attacker.get_state(self.all_players))[4] > 0.5:  # Simplified aiming for head
            if self.is_in_range(attacker.position, target.position, HEADSHOT_RANGE):
                damage_dealt = HEADSHOT_DAMAGE
                is_headshot = True
        if damage_dealt == 0:
            if self.is_in_range(attacker.position, target.position, HEADSHOT_RANGE): # Body shot range is implicit with headshot range
                damage_dealt = BODY_SHOT_DAMAGE
        if target.take_damage(damage_dealt):
            self.chat_log.append(f"'{attacker.player_id}' eliminated '{target.player_id}'.")
            return True, is_headshot, damage_dealt
        return False, is_headshot, damage_dealt

    def update_player_position(self, player, action_data):
        move_speed = 5  # Units per action
        turn_speed = 15  # Degrees per action

        if action_data["move_forward"] > 0.5:
            angle_rad = np.radians(player.facing_angle)
            player.position = (
                player.position[0] + move_speed * np.sin(angle_rad),
                player.position[1] + move_speed * np.cos(angle_rad)
            )
            # Keep player within bounds (e.g., a 100x100 arena)
            player.position = (
                max(0, min(100, player.position[0])),
                max(0, min(100, player.position[1]))
            )

        if action_data["turn_left"] > 0.5:
            player.facing_angle = (player.facing_angle - turn_speed) % 360
        if action_data["turn_right"] > 0.5:
            player.facing_angle = (player.facing_angle + turn_speed) % 360

    def run_simulation_round(self):
        self.round_num += 1
        self.chat_log.clear()
        self.chat_log.append(f"--- Round {self.round_num} ---")

        # Initialize player states for the round
        for player in self.all_players:
            player.health = 100
            player.position = (random.uniform(0, 100), random.uniform(0, 100))
            player.facing_angle = random.uniform(0, 360)

        simulated_battles = 0
        active_players = list(self.all_players)

        while len(active_players) > 1 and simulated_battles < BATTLE_SIMULATIONS_PER_ROUND:
            random.shuffle(active_players)
            for attacker in active_players:
                if attacker.health <= 0:
                    continue

                # Determine target (simplistic: closest living opponent)
                target = None
                min_dist = float('inf')
                for player in active_players:
                    if player.player_id != attacker.player_id and player.health > 0:
                        dist = self.calculate_distance(attacker.position, player.position)
                        if dist < min_dist:
                            min_dist = dist
                            target = player

                if not target:
                    break # No targets left

                # Get action decision from NN
                action_data = attacker.decide_action(active_players)

                # Update player position based on actions
                self.update_player_position(attacker, action_data)

                # Perform shooting action
                if action_data["shoot"] > 0.5:
                    eliminated, is_headshot, damage_dealt = self.perform_shoot(attacker, target)
                    self.chat_log.append(f"'{attacker.player_id}' shoots '{target.player_id}' (Headshot: {is_headshot}, Damage: {damage_dealt})")
                    if eliminated:
                        active_players.remove(target)
                        if target in self.opponents:
                            self.opponents.remove(target)
                        if len(active_players) <= 1:
                            break
                simulated_battles += 1
                if simulated_battles >= BATTLE_SIMULATIONS_PER_ROUND:
                    break
            if len(active_players) <= 1:
                break

        # Update sovereign's NN weights based on simulation outcome
        # This is a highly simplified gradient update based on a win/loss
        if self.sovereign in active_players:
            self.chat_log.append("Sovereign wins the round!")
            # Positive reinforcement: slightly increase weights that led to victory
            sovereign_state = self.sovereign.get_state(self.all_players)
            gradients = np.ones_like(self.sovereign.nn.weights) * 0.01 # Small positive gradient
            self.sovereign.nn.update_weights(gradients, learning_rate=0.05)
            self.current_iq = min(MAX_IQ, self.current_iq + 2)
        else:
            self.chat_log.append("Sovereign loses the round. Opponents adapted.")
            # Negative reinforcement: slightly decrease weights that led to defeat
            sovereign_state = self.sovereign.get_state(self.all_players)
            gradients = np.ones_like(self.sovereign.nn.weights) * 0.01 # Small negative gradient
            self.sovereign.nn.update_weights(-gradients, learning_rate=0.05)
            self.current_iq = max(INITIAL_IQ, self.current_iq - 1)

        self.iq_history.append(self.current_iq)

        # Opponent NN updates (every 4 rounds)
        if self.round_num % self.sovereign.nn_update_rate == 0:
            self.chat_log.append("Opponents are adapting...")
            for opponent in self.opponents:
                opponent_state = opponent.get_state(self.all_players)
                # Simplified adaptation: learn from sovereign's winning strategy (if observable)
                # In a real scenario, opponents would have their own evolving NNs and objectives
                gradients = np.random.rand(*opponent.nn.weights.shape) * 0.005 - 0.0025 # Random small adaptation
                opponent.nn.update_weights(gradients, learning_rate=0.02)


    def get_sovereign_iq(self):
        return self.current_iq

    def get_iq_history(self):
        return self.iq_history

    def narcissistic_chat(self, message):
        message_lower = message.lower()
        response = f"You: {message}\n"
        found_match = False

        for dialect_name, dialect_phrases in self.dialects.items():
            for keyword, phrases in dialect_phrases.items():
                if keyword in message_lower:
                    response += f"Sovereign ({dialect_name}): {random.choice(phrases)}\n"
                    found_match = True
                    break
            if found_match:
                break

        if not found_match:
            for keyword, phrases in self.narcissistic_responses.items():
                if keyword in message_lower:
                    response += f"Sovereign: {random.choice(phrases)}\n"
                    found_match = True
                    break

        if not found_match:
            response += "Sovereign: Your input is... uninteresting.\n"

        self.chat_log.append(response)
        return response

    def analyze_video(self, video_path):
        self.chat_log.append(f"Sovereign is analyzing video: {video_path}...")
        # In a real scenario, this would involve complex video processing and feature extraction.
        # For this simulation, we'll simulate learning and update the sovereign's NN.
        time.sleep(2) # Simulate analysis time
        learned_strategy = random.choice(["better aim", "improved movement", "faster reaction time", "effective cover usage"])
        self.chat_log.append(f"Analysis complete. Sovereign has learned: '{learned_strategy}'.")
        # Simulate NN update based on learned strategy
        gradients = np.random.rand(*self.sovereign.nn.weights.shape) * 0.05 - 0.025
        self.sovereign.nn.update_weights(gradients, learning_rate=0.1)
        self.current_iq = min(MAX_IQ, self.current_iq + 5)
        self.iq_history.append(self.current_iq)
        self.chat_log.append(f"IQ has increased to {self.current_iq}.")

# --- Kivy UI Integration Placeholder ---
# This part would be in your main Kivy application file (e.g., main.py)

class GameController:
    def __init__(self):
        self.arena = Arena()
        self.running_simulation = False

    def start_simulation(self):
        if not self.running_simulation:
            self.running_simulation = True
            # Use threading to run simulation without blocking UI
            self.simulation_thread = threading.Thread(target=self._run_simulations)
            self.simulation_thread.daemon = True
            self.simulation_thread.start()

    def _run_simulations(self):
        while self.running_simulation:
            self.arena.run_simulation_round()
            time.sleep(0.5) # Simulate time between rounds for UI updates

    def stop_simulation(self):
        self.running_simulation = False
        if hasattr(self, 'simulation_thread') and self.simulation_thread.is_alive():
            self.simulation_thread.join()

    def get_current_iq(self):
        return self.arena.get_sovereign_iq()

    def get_iq_history(self):
        return self.arena.get_iq_history()

    def send_chat_message(self, message):
        return self.arena.narcissistic_chat(message)

    def analyze_external_video(self, video_path):
        self.arena.analyze_video(video_path)

    def get_chat_log(self):
        return "\n".join(self.arena.chat_log)

if __name__ == '__main__':
    # Example usage (can be called from your Kivy app)
    controller = GameController()

    print("Starting simulation...")
    controller.start_simulation()
    time.sleep(2) # Let a few rounds pass

    print(f"Current Sovereign IQ: {controller.get_current_iq()}")
    print("IQ History:", controller.get_iq_history())

    print("\nSending chat message...")
    print(controller.send_chat_message("Hello there!"))

    print("\nSending another chat message (Egyptian dialect)...")
    print(controller.send_chat_message("ازيك يا باشا؟ فري فاير دي حاجة بسيطة."))

    print("\nAnalyzing dummy video...")
    controller.analyze_external_video("path/to/dummy/video.mp4")
    print(f"Current Sovereign IQ after video analysis: {controller.get_current_iq()}")

    print("\nRunning more rounds...")
    time.sleep(3)
    print(f"Current Sovereign IQ: {controller.get_current_iq()}")
    print("IQ History:", controller.get_iq_history())


    print("\nStopping simulation.")
    controller.stop_simulation()