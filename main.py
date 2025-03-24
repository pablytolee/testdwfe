import pygame
import random
import math
import sys
import os
from pygame import mixer
from PIL import Image, ImageSequence

# Initialize Pygame and mixer
try:
    pygame.init()
    mixer.init()
    print("Pygame and mixer initialized successfully")
except Exception as e:
    print(f"Error initializing Pygame/mixer: {e}")
    sys.exit(1)

# Set up the display
WIDTH = 800
HEIGHT = 600
try:
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Debt Blaster")
    print("Display set up successfully")
except Exception as e:
    print(f"Error setting up display: {e}")
    sys.exit(1)

# Colors (for fallbacks)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
GRAY = (150, 150, 150)
PURPLE = (128, 0, 128)

# Load images with fallbacks
def load_image(path, fallback_color, fallback_size):
    try:
        if os.path.exists(path):
            img = pygame.image.load(path).convert_alpha()
            print(f"Loaded {path} successfully")
            return img, img.get_width(), img.get_height()
        else:
            print(f"File {path} not found, using fallback")
            return None, fallback_size[0], fallback_size[1]
    except Exception as e:
        print(f"Error loading {path}: {e}, using fallback")
        return None, fallback_size[0], fallback_size[1]

# Load GIF frames and pre-scale them
def load_gif(path, target_size):
    try:
        if os.path.exists(path):
            gif = Image.open(path)
            frames = []
            for frame in ImageSequence.Iterator(gif):
                frame = frame.convert('RGBA')
                mode = frame.mode
                size = frame.size
                data = frame.tobytes()
                pygame_frame = pygame.image.fromstring(data, size, mode)
                # Pre-scale the frame to the target size
                scaled_frame = pygame.transform.scale(pygame_frame, target_size)
                frames.append(scaled_frame)
            print(f"Loaded GIF {path} with {len(frames)} frames")
            return frames
        else:
            print(f"File {path} not found, using fallback")
            return None
    except Exception as e:
        print(f"Error loading GIF {path}: {e}, using fallback")
        return None

# Load sounds with fallbacks
def load_sound(path):
    try:
        if os.path.exists(path):
            sound = mixer.Sound(path)
            print(f"Loaded {path} successfully")
            return sound
        else:
            print(f"File {path} not found, no sound")
            return None
    except Exception as e:
        print(f"Error loading {path}: {e}, no sound")
        return None

# Load music with fallbacks
def load_music(path):
    try:
        if os.path.exists(path):
            mixer.music.load(path)
            print(f"Loaded music {path} successfully")
            return True
        else:
            print(f"File {path} not found, no music")
            return False
    except Exception as e:
        print(f"Error loading music {path}: {e}, no music")
        return False

# Asset loading
assets_folder = "assets"
player_img, player_width, player_height = load_image(os.path.join(assets_folder, "spaceship.png"), GREEN, (60, 40))
enemy_img, enemy_width, enemy_height = load_image(os.path.join(assets_folder, "moneybag.png"), RED, (40, 40))
superseed_img, superseed_width, superseed_height = load_image(os.path.join(assets_folder, "superseed.png"), YELLOW, (30, 30))
loanshark_img, loanshark_width, loanshark_height = load_image(os.path.join(assets_folder, "loanshark.png"), GRAY, (50, 50))
bullet_img, bullet_width, bullet_height = load_image(os.path.join(assets_folder, "bullet.png"), WHITE, (5, 10))
por_img, por_width, por_height = load_image(os.path.join(assets_folder, "por.png"), PURPLE, (35, 35))
background_img, bg_width, bg_height = load_image(os.path.join(assets_folder, "background.png"), BLACK, (WIDTH, HEIGHT))
intro_gif_frames = load_gif(os.path.join(assets_folder, "intro_background.gif"), (WIDTH, HEIGHT))
end_bg, end_width, end_height = load_image(os.path.join(assets_folder, "end_background.png"), BLACK, (WIDTH, HEIGHT))

# Audio loading
background_music = os.path.join(assets_folder, "background_music.mp3")
intro_narration = os.path.join(assets_folder, "intro_narration.mp3")
bullet_sound = load_sound(os.path.join(assets_folder, "bullet_shot.wav"))
hit_sound = load_sound(os.path.join(assets_folder, "hit.wav"))
powerup_sound = load_sound(os.path.join(assets_folder, "powerup.wav"))
penalty_sound = load_sound(os.path.join(assets_folder, "penalty.wav"))
por_sound = load_sound(os.path.join(assets_folder, "por_collect.wav"))

# Load background music (but don't play yet)
background_music_loaded = load_music(background_music)

# Load intro narration
intro_narration_loaded = load_music(intro_narration)

# Player
player_x = WIDTH // 2 - player_width // 2
player_y = HEIGHT - player_height - 20
player_speed = 5

# Game variables
debt = 10000
game_active = False
start_time = 0
player_name = ""
por_active = False
por_timer = 0

# Enemy settings
enemy_speed = 2
enemy_spawn_rate = 60
enemy_timer = 0

# Lists for game objects
enemies = []
bullets = []
superseeds = []
loansharks = []
pors = []

# Notification system
notifications = []
class Notification:
    def __init__(self, text, duration=3000):
        self.text = text
        self.duration = duration
        self.start_time = pygame.time.get_ticks()

    def is_expired(self):
        return (pygame.time.get_ticks() - self.start_time) > self.duration

# Font (using bold system font)
try:
    font = pygame.font.SysFont("Arial", 36, bold=True)
    print("Font initialized successfully")
except Exception as e:
    print(f"Error initializing font: {e}")
    sys.exit(1)

# Function to render text with outline
def render_text_with_outline(text, font, color, outline_color, pos):
    text_surface = font.render(text, True, color)
    outline_surface = font.render(text, True, outline_color)
    for offset in [(-2, -2), (-2, 2), (2, -2), (2, 2), (0, -2), (0, 2), (-2, 0), (2, 0)]:
        screen.blit(outline_surface, (pos[0] + offset[0], pos[1] + offset[1]))
    screen.blit(text_surface, pos)

# Reset game state for play again
def reset_game():
    global debt, game_active, start_time, player_name, por_active, por_timer, enemy_speed, enemy_spawn_rate, enemy_timer
    global enemies, bullets, superseeds, loansharks, pors, player_x, notifications
    debt = 10000
    game_active = False
    start_time = 0
    player_name = ""
    por_active = False
    por_timer = 0
    enemy_speed = 2
    enemy_spawn_rate = 60
    enemy_timer = 0
    enemies = []
    bullets = []
    superseeds = []
    loansharks = []
    pors = []
    notifications = []
    player_x = WIDTH // 2 - player_width // 2

class Enemy:
    def __init__(self):
        self.x = random.randint(0, WIDTH - enemy_width)
        self.y = -enemy_height
        self.speed = enemy_speed

class Bullet:
    def __init__(self, x, y, angle=0):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = 10
        self.vx = math.sin(math.radians(self.angle)) * self.speed
        self.vy = -math.cos(math.radians(self.angle)) * self.speed

    def update(self):
        self.x += self.vx
        self.y += self.vy

class SuperSeed:
    def __init__(self):
        self.x = random.randint(0, WIDTH - superseed_width)
        self.y = -superseed_height
        self.speed = 3

class LoanShark:
    def __init__(self):
        self.x = random.randint(0, WIDTH - loanshark_width)
        self.y = -loanshark_height
        self.speed = enemy_speed * 1.5

class POR:
    def __init__(self):
        self.x = random.randint(0, WIDTH - por_width)
        self.y = -por_height
        self.speed = 2.5

def show_intro():
    if intro_narration_loaded:
        mixer.music.play()
        print("Intro narration started")
    
    intro_duration = 30000
    start_time = pygame.time.get_ticks()
    skipped = False
    frame_index = 0
    frame_delay = 100
    last_frame_time = start_time
    clock = pygame.time.Clock()
    
    while pygame.time.get_ticks() - start_time < intro_duration:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN and not skipped:
                if event.key == pygame.K_SPACE:
                    skipped = True
                    print("Intro screen skipped")
        
        screen.fill(BLACK)
        if intro_gif_frames:
            if pygame.time.get_ticks() - last_frame_time >= frame_delay:
                frame_index = (frame_index + 1) % len(intro_gif_frames)
                last_frame_time = pygame.time.get_ticks()
            screen.blit(intro_gif_frames[frame_index], (0, 0))
        else:
            screen.fill(BLACK)
        
        if not skipped:
            skip_text = font.render("Press Space to Skip", True, WHITE)
            screen.blit(skip_text, (WIDTH//2 - skip_text.get_width()//2, HEIGHT - 50))
        else:
            prompt = font.render("Enter your name, Seedizen:", True, WHITE)
            screen.blit(prompt, (WIDTH//2 - prompt.get_width()//2, HEIGHT//2 - 40))
        
        pygame.display.flip()
        clock.tick(60)
    
    print("Intro narration should have ended")
    return True

def get_player_name():
    global player_name
    input_active = True
    player_name = ""
    frame_index = 0
    frame_delay = 100
    last_frame_time = pygame.time.get_ticks()
    clock = pygame.time.Clock()
    
    while input_active:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    input_active = False
                elif event.key == pygame.K_BACKSPACE:
                    player_name = player_name[:-1]
                else:
                    player_name += event.unicode
        
        screen.fill(BLACK)
        if intro_gif_frames:
            if pygame.time.get_ticks() - last_frame_time >= frame_delay:
                frame_index = (frame_index + 1) % len(intro_gif_frames)
                last_frame_time = pygame.time.get_ticks()
            screen.blit(intro_gif_frames[frame_index], (0, 0))
        else:
            screen.fill(BLACK)
        prompt = font.render("Enter your name, Seedizen:", True, WHITE)
        name_text = font.render(player_name, True, WHITE)
        screen.blit(prompt, (WIDTH//2 - prompt.get_width()//2, HEIGHT//2 - 40))
        screen.blit(name_text, (WIDTH//2 - name_text.get_width()//2, HEIGHT//2))
        pygame.display.flip()
        clock.tick(60)
    return True

def show_end_screen(game_time):
    play_again = False
    clock = pygame.time.Clock()
    
    while not play_again:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    play_again = True
                    break
        
        screen.fill(BLACK)
        if end_bg:
            scaled_end = pygame.transform.scale(end_bg, (WIDTH, HEIGHT))
            screen.blit(scaled_end, (0, 0))
        time_text = font.render(f"Time: {game_time:.2f}s", True, WHITE)
        win_text = font.render(f"Congratulations, {player_name}! WAGMI!", True, WHITE)
        play_again_text = font.render("Press Space to Play Again", True, WHITE)
        screen.blit(time_text, (WIDTH//2 - time_text.get_width()//2, HEIGHT//2 - 40))
        screen.blit(win_text, (WIDTH//2 - win_text.get_width()//2, HEIGHT//2))
        screen.blit(play_again_text, (WIDTH//2 - play_again_text.get_width()//2, HEIGHT//2 + 40))
        pygame.display.flip()
        clock.tick(60)
    return True

# Main game loop
clock = pygame.time.Clock()
running = True

while running:
    reset_game()
    show_intro_screen = True
    game_over = False

    while running and not game_over:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and game_active:
                    if por_active:
                        bullets.append(Bullet(player_x + player_width//2 - bullet_width//2, player_y, 0))
                        bullets.append(Bullet(player_x + player_width//2 - bullet_width//2, player_y, -30))
                        bullets.append(Bullet(player_x + player_width//2 - bullet_width//2, player_y, 30))
                    else:
                        bullets.append(Bullet(player_x + player_width//2 - bullet_width//2, player_y))
                    if bullet_sound:
                        bullet_sound.play()
                    if not start_time:
                        start_time = pygame.time.get_ticks()

        if show_intro_screen:
            try:
                if not show_intro():
                    running = False
                if not get_player_name():
                    running = False
                show_intro_screen = False
                game_active = True
                if background_music_loaded:
                    mixer.music.load(background_music)
                    mixer.music.set_volume(0.5)
                    mixer.music.play(-1)
                print("Intro completed")
            except Exception as e:
                print(f"Error in intro: {e}")
                running = False

        if game_active and not game_over:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] and player_x > 0:
                player_x -= player_speed
            if keys[pygame.K_RIGHT] and player_x < WIDTH - player_width:
                player_x += player_speed

            enemy_timer += 1
            if enemy_timer >= enemy_spawn_rate:
                enemies.append(Enemy())
                if random.random() < 0.1:
                    superseeds.append(SuperSeed())
                if random.random() < 0.15:
                    loansharks.append(LoanShark())
                if random.random() < 0.05:
                    pors.append(POR())
                enemy_timer = 0

            if por_active:
                current_time = pygame.time.get_ticks()
                if (current_time - por_timer) >= 30000:
                    por_active = False
                    print("POR power-up expired")

            for bullet in bullets[:]:
                bullet.update()
                if bullet.y < -bullet_height or bullet.x < 0 or bullet.x > WIDTH:
                    bullets.remove(bullet)

            for enemy in enemies[:]:
                enemy.y += enemy.speed
                if enemy.y > HEIGHT:
                    enemies.remove(enemy)

            for seed in superseeds[:]:
                seed.y += seed.speed
                if seed.y > HEIGHT:
                    superseeds.remove(seed)

            for shark in loansharks[:]:
                shark.y += shark.speed
                if shark.y > HEIGHT:
                    loansharks.remove(shark)

            for por in pors[:]:
                por.y += por.speed
                if por.y > HEIGHT:
                    pors.remove(por)

            for notification in notifications[:]:
                if notification.is_expired():
                    notifications.remove(notification)

            for bullet in bullets[:]:
                bullet_rect = pygame.Rect(bullet.x, bullet.y, bullet_width, bullet_height)
                
                for enemy in enemies[:]:
                    enemy_rect = pygame.Rect(enemy.x, enemy.y, enemy_width, enemy_height)
                    if bullet_rect.colliderect(enemy_rect):
                        debt -= 10
                        enemies.remove(enemy)
                        bullets.remove(bullet)
                        if hit_sound:
                            hit_sound.play()
                        break

                for seed in superseeds[:]:
                    seed_rect = pygame.Rect(seed.x, seed.y, superseed_width, superseed_height)
                    if bullet_rect.colliderect(seed_rect):
                        debt = math.ceil(debt * 0.99)
                        superseeds.remove(seed)
                        bullets.remove(bullet)
                        if powerup_sound:
                            powerup_sound.play()
                        break

                for shark in loansharks[:]:
                    shark_rect = pygame.Rect(shark.x, shark.y, loanshark_width, loanshark_height)
                    if bullet_rect.colliderect(shark_rect):
                        debt = math.ceil(debt * 1.10)
                        loansharks.remove(shark)
                        bullets.remove(bullet)
                        notifications.append(Notification("Loan shark increased your debt by 10%"))
                        if penalty_sound:
                            penalty_sound.play()
                        break

                for por in pors[:]:
                    por_rect = pygame.Rect(por.x, por.y, por_width, por_height)
                    if bullet_rect.colliderect(por_rect):
                        debt = math.ceil(debt * 0.98)
                        por_active = True
                        por_timer = pygame.time.get_ticks()
                        pors.remove(por)
                        bullets.remove(bullet)
                        notifications.append(Notification("2% of your debt has been paid with POR"))
                        if por_sound:
                            por_sound.play()
                        print("POR power-up collected!")
                        break

            if debt < 8000:
                enemy_speed = 2.5
            if debt < 5000:
                enemy_speed = 3
                enemy_spawn_rate = 50

            if debt <= 0:
                debt = 0
                game_over = True
                end_time = pygame.time.get_ticks()
                game_time = (end_time - start_time) / 1000
                if background_music_loaded:
                    mixer.music.stop()

        screen.fill(BLACK)
        if background_img:
            scaled_bg = pygame.transform.scale(background_img, (WIDTH, HEIGHT))
            screen.blit(scaled_bg, (0, 0))
        
        if game_active:
            if player_img:
                screen.blit(player_img, (player_x, player_y))
            else:
                pygame.draw.rect(screen, GREEN, (player_x, player_y, player_width, player_height))
            
            for bullet in bullets:
                if bullet_img:
                    screen.blit(bullet_img, (bullet.x, bullet.y))
                else:
                    pygame.draw.rect(screen, WHITE, (bullet.x, bullet.y, bullet_width, bullet_height))
            
            for enemy in enemies:
                if enemy_img:
                    screen.blit(enemy_img, (enemy.x, enemy.y))
                else:
                    pygame.draw.rect(screen, RED, (enemy.x, enemy.y, enemy_width, enemy_height))
            
            for seed in superseeds:
                if superseed_img:
                    screen.blit(superseed_img, (seed.x, seed.y))
                else:
                    pygame.draw.rect(screen, YELLOW, (seed.x, seed.y, superseed_width, superseed_height))
            
            for shark in loansharks:
                if loanshark_img:
                    screen.blit(loanshark_img, (shark.x, shark.y))
                else:
                    pygame.draw.rect(screen, GRAY, (shark.x, shark.y, loanshark_width, loanshark_height))
            
            for por in pors:
                if por_img:
                    screen.blit(por_img, (por.x, por.y))
                else:
                    pygame.draw.rect(screen, PURPLE, (por.x, por.y, por_width, por_height))
            
            render_text_with_outline(f"Debt: ${debt}", font, WHITE, BLACK, (10, 10))
            
            for i, notification in enumerate(notifications):
                render_text_with_outline(notification.text, font, WHITE, BLACK, (WIDTH//2 - len(notification.text)*10, HEIGHT//2 + i*40))
            
            if game_over:
                if not show_end_screen(game_time):
                    running = False
                else:
                    reset_game()
                    show_intro_screen = True
                    game_over = False
        
        pygame.display.flip()
        clock.tick(60)

pygame.quit()
print("Game closed normally")
sys.exit(0)