import pygame
import random
import math
from dqn_trainer import DQNTrainer, TARGET_UPDATE
import numpy as np
import torch

# init pygame
pygame.init()

# the size of screen
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Golden Miner")

# background
background_image = pygame.image.load('images/background2.jpg').convert_alpha()
# the size of background
background_image = pygame.transform.scale(background_image, (WIDTH, HEIGHT))

# each items' images
small_golden_image = pygame.image.load('images/small_golden2.png').convert_alpha()
small_golden_image = pygame.transform.scale(small_golden_image, (150, 150))

large_golden_image = pygame.image.load('images/large_golden2.png').convert_alpha()
large_golden_image = pygame.transform.scale(large_golden_image, (200, 200))

diamond_image = pygame.image.load('images/diamond3.png').convert_alpha()
diamond_image = pygame.transform.scale(diamond_image, (100, 100))

bomb_image = pygame.image.load('images/bomb2.png').convert_alpha()
bomb_image = pygame.transform.scale(bomb_image, (120, 120))

stone_image = pygame.image.load('images/stone2.png').convert_alpha()

explosion_image = pygame.image.load('images/baozha.jpg').convert_alpha()
explosion_image = pygame.transform.scale(explosion_image, (60, 60))

hook_head_image = pygame.image.load('images/hook2.png').convert_alpha()
hook_head_image = pygame.transform.scale(hook_head_image, (100, 100))

# images dictionary
object_images = {
    "small_gold": small_golden_image,
    "large_gold": large_golden_image,
    "diamond": diamond_image,
    "bomb": bomb_image,
    "stone": stone_image
}


# color (used for testing)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
GRAY = (150, 150, 150)
ORANGE = (255, 165, 0)

# font
font = pygame.font.SysFont("Arial", 36)

# State Space
clock = pygame.time.Clock()
score = 0
time_left = 30  # the time of the game
game_over = False
game_stopped = False  # if the game is over

total_reward = 0  # total reward for each game

# hook
hook_length = 0
hook_speed = 5 * 2  # speed
original_hook_speed = hook_speed  # original speed
hook_angle = 90  # original angle
hook_angle_speed = 1
hook_state = "idle"  # idle, extending, retracting
hook_pos = [WIDTH // 2, 50]  # the start location of hook
hook_end_pos = [0, 0]  # the end of hook
fixed_angle = 90
angle_direction = 1  # the change of hook angle

consecutive_misses = 0  # the num of continuous empty hook

grabbed_object = None

# explosion
explosion_pos = None
explosion_timer = 0

# Object
class Object:
    def __init__(self, x, y, size, value, color, obj_type):
        self.x = x
        self.y = y
        self.size = size
        self.value = value
        self.color = color
        self.obj_type = obj_type  # the type of object

    def draw(self):
        if self.obj_type == "stone":
            # change the image of stone with its size
            scaled_stone_image = pygame.transform.scale(stone_image, (self.size * 2, self.size * 2))
            screen.blit(scaled_stone_image,
                        (self.x - scaled_stone_image.get_width() // 2, self.y - scaled_stone_image.get_height() // 2))
        else:
            image = object_images[self.obj_type]
            screen.blit(image, (self.x - image.get_width() // 2, self.y - image.get_height() // 2))

# if object is overlapping
def is_overlapping(obj1, obj2):
    distance = math.sqrt((obj1.x - obj2.x) ** 2 + (obj1.y - obj2.y) ** 2)
    return distance < (obj1.size + obj2.size)

# create initial objects
def create_initial_objects():
    objects = []
    # small golden(3)
    for _ in range(3):
        while True:
            x = random.randint(100, WIDTH - 100)
            y = random.randint(hook_pos[1] + 100, HEIGHT - 100)
            new_obj = Object(x, y, 25, 20, YELLOW, "small_gold")
            if not any(is_overlapping(new_obj, obj) for obj in objects):
                objects.append(new_obj)
                break

    # large golden(2)
    for _ in range(2):
        while True:
            x = random.randint(100, WIDTH - 100)
            y = random.randint(hook_pos[1] + 100, HEIGHT - 100)
            new_obj = Object(x, y, 40, 35, YELLOW, "large_gold")
            if not any(is_overlapping(new_obj, obj) for obj in objects):
                objects.append(new_obj)
                break

    # diamond(2)
    for _ in range(2):
        while True:
            x = random.randint(100, WIDTH - 100)
            y = random.randint(hook_pos[1] + 100, HEIGHT - 100)
            new_obj = Object(x, y, 15, 50, BLUE, "diamond")
            if not any(is_overlapping(new_obj, obj) for obj in objects):
                objects.append(new_obj)
                break

    # bomb(2)
    for _ in range(2):
        while True:
            x = random.randint(100, WIDTH - 100)
            y = random.randint(hook_pos[1] + 100, HEIGHT - 100)
            new_obj = Object(x, y, random.randint(20, 40), 0, RED, "bomb")
            if not any(is_overlapping(new_obj, obj) for obj in objects):
                objects.append(new_obj)
                break

    # stone(3)
    for _ in range(3):
        while True:
            x = random.randint(100, WIDTH - 100)
            y = random.randint(hook_pos[1] + 100, HEIGHT - 100)
            new_obj = Object(x, y, random.randint(60, 100), 1, GRAY, "stone")
            if not any(is_overlapping(new_obj, obj) for obj in objects):
                objects.append(new_obj)
                break

    return objects

# the max length of the hook
def calculate_max_length(angle):
    x0, y0 = hook_pos

    dx = math.cos(math.radians(angle))
    dy = math.sin(math.radians(angle))

    if dx > 0:
        x_boundary = WIDTH
    else:
        x_boundary = 0
    if dy > 0:
        y_boundary = HEIGHT
    else:
        y_boundary = 0

    t_x = (x_boundary - x0) / dx if dx != 0 else float('inf')
    t_y = (y_boundary - y0) / dy if dy != 0 else float('inf')

    t = min(t_x, t_y)

    return t

# init the objects
objects = create_initial_objects()

# Dimension of state space
STATE_DIM = 64
# Hook position and angle (3)+hook status (1)+object information (10 objects * 5 values)

# Dimension of action space
ACTION_DIM = 2
# IDLE (0) or SPACE (1)

# init dqn trainer
dqn_trainer = DQNTrainer(STATE_DIM, ACTION_DIM)

# try to get the model
model_path = "model_checkpoint.pth"
dqn_trainer.load_model(model_path)
episode = dqn_trainer.episode  # get the num of episode

# 获取当前状态
def get_state():
    state = []
    # the location and angle of hook
    state.extend([hook_pos[0], hook_pos[1], hook_angle])
    # the state of hook （idle: 0, extending: 1, retracting: 2）
    if hook_state == "idle":
        state.append(0)
    elif hook_state == "extending":
        state.append(1)
    elif hook_state == "retracting":
        state.append(2)
    # object information
    for obj in objects:
        # location
        state.extend([obj.x, obj.y])
        # type
        if obj.obj_type == "bomb":
            state.extend([1, 0, 0])  # bomb
        elif obj.obj_type == "stone":
            state.extend([0, 1, 0])  # stone
        else:
            state.extend([0, 0, 1])  # valuable items

    # if the num of items is less than 10, use 0
    while len(state) < 64:
        state.extend([0, 0, 0, 0, 0])
    return np.array(state, dtype=np.float32)
    # Convert to numpy array and specify data type

# The last time the hook was idle
last_idle_frame = 0
# Time interval threshold for continuous hooking (frames)
CONSECUTIVE_HOOK_INTERVAL = 60

EPSILON = 15

def calculate_reward():
    global last_idle_frame
    reward = 0
    # Apply different time penalties based on the hook status
    if hook_state == "idle":
        reward -= 0.002
    # elif hook_state in ["extending", "retracting"]:
    #     reward += 0.001

    # print(f"hook_length: {hook_length}, grabbed_object: {grabbed_object}")
    if grabbed_object:
        # print("grabbed_object: ",{grabbed_object.obj_type})
        # Use error range to determine whether the hook has returned to the origin
        if hook_length <= EPSILON:
            if grabbed_object.obj_type in ["small_gold", "large_gold", "diamond"]:
                # Reward for grabbing valuable items
                reward += grabbed_object.value
            elif grabbed_object.obj_type == "stone":
                # Punishment for grabbing stones
                reward -= 5
            elif grabbed_object.obj_type == "bomb":
                # Punishment for grabbing bombs
                reward -= 20
    else:
        if hook_state == "retracting":
            # Punishment for retrieving the hook but failing to catch the item
            reward -= 3

    # Ignore the impact of invalid actions on rewards
    if hook_state != "idle" and action == 1:
        # Attempting to hook in an inoperable state without additional rewards or punishments
        pass

    return reward


# Game main loop
running = True
max_episodes = 3000  # Maximum number of training epochs
while running and episode < max_episodes:
    screen.blit(background_image, (0, 0))

    # event
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # get the state in the moment
    state = get_state()

    # Determine the hook status and only allow the model to select actions when idle
    if hook_state == "idle" and not game_stopped:
        # The model is only allowed to select actions when the hook is idle
        action = dqn_trainer.select_action(state)
        if action == 1:
            hook_state = "extending"
            fixed_angle = hook_angle
    else:
        # The hook is in an inoperable state, forcing the IDLE action to be selected
        action = 0

    # Update hook status
    if hook_state == "extending":
        max_length = calculate_max_length(fixed_angle)
        hook_length += hook_speed
        if hook_length > max_length:
            hook_state = "retracting"
    elif hook_state == "retracting":
        hook_length -= hook_speed
        if hook_length <= EPSILON:
            hook_length = 0
            hook_state = "idle"

            current_reward = 0

            # After the hook returns to the origin, remove the grasped object and increase the score
            if grabbed_object:

                consecutive_misses = 0

                if grabbed_object.obj_type == "stone":
                    score += 1
                    current_reward -= 1
                elif grabbed_object.obj_type != "bomb":
                    score += grabbed_object.value
                    current_reward += grabbed_object.value

                objects.remove(grabbed_object)
                new_obj = create_initial_objects()[0]  # Generate a new object
                objects.append(new_obj)
                grabbed_object = None
            else:
                consecutive_misses += 1
                base_penalty = -3
                current_reward = base_penalty - consecutive_misses

            total_reward += current_reward

            # Restore the original speed of the hook
            hook_speed = original_hook_speed


    # Update hook angle (automatic rotation)
    if hook_state == "idle" and not game_stopped:
        hook_angle += hook_angle_speed * angle_direction

        # Reverse direction when the angle reaches 180 ° or 0 °
        if hook_angle >= 180:
            angle_direction = -1
        elif hook_angle <= 0:
            angle_direction = 1

    # Calculate the position of the hook end
    if hook_state == "extending" or hook_state == "retracting":
        # Using a fixed angle
        hook_end_pos[0] = hook_pos[0] + hook_length * math.cos(math.radians(fixed_angle))
        hook_end_pos[1] = hook_pos[1] + hook_length * math.sin(math.radians(fixed_angle))
    else:
        # Use current angle
        hook_end_pos[0] = hook_pos[0] + hook_length * math.cos(math.radians(hook_angle))
        hook_end_pos[1] = hook_pos[1] + hook_length * math.sin(math.radians(hook_angle))

    # Draw a preview dashed line (only displayed when the hook is not extended)
    if hook_state == "idle" and not game_stopped:
        max_length = calculate_max_length(hook_angle)
        preview_end_pos = (
            hook_pos[0] + max_length * math.cos(math.radians(hook_angle)),
            hook_pos[1] + max_length * math.sin(math.radians(hook_angle))
        )
        pygame.draw.line(screen, GRAY, hook_pos, preview_end_pos, 2)

    # hook
    pygame.draw.line(screen, WHITE, hook_pos, hook_end_pos, 5)
    # Rotating hook image
    rotated_hook_image = pygame.transform.rotate(hook_head_image,
                                                 90 - hook_angle if hook_state == "idle" else 90 - fixed_angle)
    hook_rect = rotated_hook_image.get_rect(center=(int(hook_end_pos[0]), int(hook_end_pos[1])))

    # Draw a rotated hook image
    screen.blit(rotated_hook_image, hook_rect)

    for obj in objects:
        obj.draw()

        # Check if the hook grabs the object
        if hook_state == "extending" and grabbed_object is None and not game_stopped:
            distance = math.sqrt((obj.x - hook_end_pos[0]) ** 2 + (obj.y - hook_end_pos[1]) ** 2)
            if distance < obj.size + 10:
                grabbed_object = obj  # Record the captured object
                if obj.obj_type == "stone":
                    hook_speed = original_hook_speed / 3
                    # The speed of the hook slows down after grabbing the stone
                elif obj.obj_type == "large_gold":
                    hook_speed = original_hook_speed / 2
                    # After grabbing the large gold nugget, the speed of the hook slows down
                elif obj.obj_type == "bomb":
                    explosion_pos = (obj.x, obj.y)
                    # Record the location of the explosion
                    explosion_timer = 30
                    # Explosion prompt display
                    time_left -= 10
                    hook_state = "idle"
                    # Immediately retract the hook
                    hook_length = 0
                    grabbed_object = None
                    # The bomb does not move with the hook
                    objects.remove(obj)
                    # Remove the bomb
                    new_obj = create_initial_objects()[0]
                    objects.append(new_obj)
                hook_state = "retracting"

    if grabbed_object and grabbed_object.obj_type != "bomb":
        grabbed_object.x = hook_end_pos[0]
        grabbed_object.y = hook_end_pos[1]
        grabbed_object.draw()

    # Rotating hook image
    rotated_hook_image = pygame.transform.rotate(hook_head_image,
                                                 90 - hook_angle if hook_state == "idle" else 90 - fixed_angle)
    hook_rect = rotated_hook_image.get_rect(center=(int(hook_end_pos[0]), int(hook_end_pos[1])))
    screen.blit(rotated_hook_image, hook_rect)

    # Display explosion prompt
    if explosion_timer > 0:
        screen.blit(explosion_image, (explosion_pos[0] - explosion_image.get_width() // 2,
                                      explosion_pos[1] - explosion_image.get_height() // 2))
        explosion_timer -= 1

    # Display score and time
    score_text = font.render(f"Score: {score}", True, (0,0,0))
    time_text = font.render(f"Time: {int(time_left)}", True, (0,0,0))
    screen.blit(score_text, (10, 10))
    screen.blit(time_text, (WIDTH - 150, 10))

    # Display total rewards
    # reward_text = font.render(f"Reward: {total_reward:.2f}", True, (0,0,0))
    # screen.blit(reward_text, (10, 50))

    # update time
    if not game_over and not game_stopped:
        time_left -= 1 / 60
        if time_left <= 0:
            game_over = True

    # game over
    if game_over or game_stopped:
        print(f"Episode {episode}, Total Reward: {score}")
        # Reset game variables
        score = 0
        time_left = 30
        game_over = False
        game_stopped = False
        hook_length = 0
        hook_state = "idle"
        hook_angle = 90
        angle_direction = 1
        grabbed_object = None
        objects = create_initial_objects()
        last_idle_frame = 0
        total_reward = 0
        episode += 1
        dqn_trainer.episode = episode
        # Update training frequency

    # Get the next status and reward
    next_state = get_state()
    reward = calculate_reward()
    total_reward += reward  # Accumulate the reward of the current frame to the total reward
    done = game_over or game_stopped

    # Storage experience
    dqn_trainer.memory.push(state, action, reward, next_state, done)

    # Update Model
    dqn_trainer.update_model()

    # Update target network
    if episode % TARGET_UPDATE == 0:
        dqn_trainer.update_target_net()

    # screen
    pygame.display.flip()
    clock.tick(60)

dqn_trainer.save_model(model_path)

# quit rhe game
pygame.quit()