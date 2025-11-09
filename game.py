import pygame
import random
import math
import os

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 600
FPS = 60

# Colors - vibrant and playful palette
BACKGROUND = (20, 25, 40)
PLAYER_COLOR = (100, 200, 255)
STAR_COLORS = [
    (255, 215, 0),  # Gold
    (255, 105, 180),  # Hot Pink
    (138, 43, 226),  # Blue Violet
    (50, 205, 50),  # Lime Green
    (255, 165, 0),  # Orange
    (255, 20, 147),  # Deep Pink
    (0, 191, 255),  # Deep Sky Blue
]
OBSTACLE_COLOR = (220, 20, 60)  # Old red color, keeping for reference
COMET_BASE_COLOR = (128, 0, 128)  # Purple base
COMET_DARK = (80, 0, 80)  # Dark purple for shadows
COMET_LIGHT = (180, 50, 180)  # Light purple for highlights
CRATER_COLOR = (60, 0, 60)  # Dark purple for craters
TEXT_COLOR = (255, 255, 255)
PARTICLE_COLORS = [(255, 255, 0), (255, 200, 0), (255, 150, 0)]

# Game settings
PLAYER_SIZE = 30
PLAYER_SPEED = 5
STAR_SIZE = 20
OBSTACLE_SIZE = 25
STAR_SPAWN_RATE = 0.02
OBSTACLE_SPAWN_RATE = 0.01
PARTICLE_COUNT = 15
PROJECTILE_SPEED = 8
PROJECTILE_SIZE = 5
PROJECTILE_COLOR = (255, 255, 0)

# High score file
HIGH_SCORE_FILE = "highscore.txt"

class Projectile:
    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = PROJECTILE_SPEED
        self.size = PROJECTILE_SIZE
        self.color = PROJECTILE_COLOR
        
    def update(self):
        self.x += self.speed * math.cos(self.angle)
        self.y += self.speed * math.sin(self.angle)
    
    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.size)
        pygame.draw.circle(screen, (255, 255, 255), (int(self.x), int(self.y)), self.size, 1)
    
    def is_off_screen(self):
        return (self.x < 0 or self.x > WIDTH or self.y < 0 or self.y > HEIGHT)
    
    def get_rect(self):
        return pygame.Rect(self.x - self.size, self.y - self.size, 
                          self.size * 2, self.size * 2)

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = PLAYER_SIZE
        self.speed = PLAYER_SPEED
        self.color = PLAYER_COLOR
        self.jetpack_flame = 0
        self.flame_trail = []  # List of (x, y, life) tuples for flame trail
        self.last_x = x
        self.last_y = y
        self.angle = 0  # Direction player is facing (in radians, 0 = right)
        self.shoot_cooldown = 0
        
    def move(self, dx, dy):
        self.last_x = self.x
        self.last_y = self.y
        
        # Update angle based on movement direction
        # Map directions to specific angles as requested:
        # Right = 90° (from 0° upright, turn 90° right)
        # Left = -90° or 270° (from 0° upright, turn 90° left)  
        # Down = 180° (from 0° upright, turn 180°)
        # Up = 0° (upright, default)
        if dx != 0 or dy != 0:
            # Prioritize the primary direction pressed
            if dy < 0:  # Up key
                self.angle = -math.pi / 2  # 0 degrees upright (pointing up, -90° in math coords)
            elif dx > 0:  # Right key
                self.angle = 0  # 90 degrees from upright (pointing right, 0° in math coords)
            elif dx < 0:  # Left key
                self.angle = math.pi  # -90 degrees from upright (pointing left, 180° in math coords)
            elif dy > 0:  # Down key
                self.angle = math.pi / 2  # 180 degrees from upright (pointing down, 90° in math coords)
            # Handle diagonal movement - prioritize based on which key was pressed
            if dx != 0 and dy != 0:
                # For diagonal, use the dominant direction
                if abs(dx) >= abs(dy):
                    if dx > 0:
                        self.angle = 0  # Right
                    else:
                        self.angle = math.pi  # Left
                else:
                    if dy > 0:
                        self.angle = math.pi / 2  # Down
                    else:
                        self.angle = -math.pi / 2  # Up
            self.jetpack_flame += 0.3
            # Add flame trail particles when moving
            # Calculate normalized direction vector
            distance = math.sqrt(dx*dx + dy*dy) if (dx != 0 or dy != 0) else 1
            dir_x = dx / distance if distance > 0 else 0
            dir_y = dy / distance if distance > 0 else 0
            
            # Add flame particles behind the player (opposite of movement direction)
            for i in range(3):
                # Position flames behind the player (opposite of movement direction)
                offset_x = -dir_x * (i + 1) * 8
                offset_y = -dir_y * (i + 1) * 8
                self.flame_trail.append({
                    'x': self.x + offset_x,
                    'y': self.y + offset_y,  # Position behind player
                    'life': 25 - i * 4,  # Different life for each particle
                    'max_life': 25
                })
        else:
            self.jetpack_flame += 0.1
        
        self.x = max(self.size, min(WIDTH - self.size, self.x + dx))
        self.y = max(self.size, min(HEIGHT - self.size, self.y + dy))
        
        # Update flame trail
        for flame in self.flame_trail[:]:
            flame['life'] -= 1
            if flame['life'] <= 0:
                self.flame_trail.remove(flame)
        
        # Update shoot cooldown
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
    
    def shoot(self):
        """Create a projectile in the direction the player is facing"""
        if self.shoot_cooldown <= 0:
            self.shoot_cooldown = 15  # Cooldown between shots (slightly slower)
            # Projectile starts from the front of the player (head)
            start_x = self.x + math.cos(self.angle) * 20
            start_y = self.y + math.sin(self.angle) * 20
            return Projectile(start_x, start_y, self.angle)
        return None
    
    def rotate_point(self, px, py, cx, cy, angle):
        """Rotate a point around a center point by an angle"""
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        dx = px - cx
        dy = py - cy
        return (cx + dx * cos_a - dy * sin_a, cy + dx * sin_a + dy * cos_a)
    
    def draw(self, screen):
        x, y = int(self.x), int(self.y)
        # Add π/2 offset so that when angle is 0° (right), the head (which is at -15y by default) points right
        # This aligns the sprite's default "up" orientation with the movement direction
        draw_angle = self.angle + math.pi / 2
        cos_a = math.cos(draw_angle)
        sin_a = math.sin(draw_angle)
        
        # Helper to rotate a point relative to player center
        def rot(px, py):
            return (x + px * cos_a - py * sin_a, y + px * sin_a + py * cos_a)
        
        # Draw flame trail (behind the player)
        for flame in self.flame_trail:
            life_ratio = flame['life'] / flame['max_life']
            # Yellow and orange flames
            flame_colors = [
                (255, int(200 * life_ratio), int(100 * life_ratio)),  # Orange
                (255, int(255 * life_ratio), int(150 * life_ratio)),  # Yellow-orange
                (255, int(255 * life_ratio), int(200 * life_ratio)),  # Yellow
            ]
            flame_size = int(6 + 4 * life_ratio)
            for i, color in enumerate(flame_colors):
                size_offset = i * 1.5
                pygame.draw.circle(screen, color, 
                                  (int(flame['x']), int(flame['y'])), 
                                  int(flame_size - size_offset))
        
        # Draw jetpack flames (behind player, opposite of facing direction)
        flame_size = int(8 + math.sin(self.jetpack_flame) * 4)
        flame_colors = [(255, 100, 0), (255, 200, 0), (255, 255, 100)]
        flame_x, flame_y = rot(-10, 8)  # Behind and below player
        for i, color in enumerate(flame_colors):
            offset = i * 2
            pygame.draw.ellipse(screen, color, 
                               (flame_x - flame_size//2 + offset, flame_y, 
                                flame_size - offset*2, flame_size))
        
        # Draw jetpack (backpack) - behind player
        jetpack_points = [
            rot(-8, 5), rot(8, 5), rot(8, 25), rot(-8, 25)
        ]
        pygame.draw.polygon(screen, (60, 60, 60), jetpack_points)
        pygame.draw.polygon(screen, (100, 100, 100), jetpack_points, 2)
        # Jetpack details
        detail1_x, detail1_y = rot(-4, 12)
        detail2_x, detail2_y = rot(4, 12)
        pygame.draw.circle(screen, (200, 200, 200), (int(detail1_x), int(detail1_y)), 3)
        pygame.draw.circle(screen, (200, 200, 200), (int(detail2_x), int(detail2_y)), 3)
        
        # Draw space suit body (torso)
        body_points = [
            rot(-10, -5), rot(10, -5), rot(10, 20), rot(-10, 20)
        ]
        pygame.draw.polygon(screen, (255, 255, 255), body_points)
        pygame.draw.polygon(screen, (200, 200, 200), body_points, 2)
        
        # Draw space suit details - chest panel
        panel_points = [
            rot(-6, 0), rot(6, 0), rot(6, 8), rot(-6, 8)
        ]
        pygame.draw.polygon(screen, (100, 150, 255), panel_points)
        center_x, center_y = rot(0, 4)
        pygame.draw.circle(screen, (255, 0, 0), (int(center_x), int(center_y)), 2)
        
        # Draw helmet (head) - at front of player
        helmet_x, helmet_y = rot(0, -15)
        helmet_radius = 12
        pygame.draw.circle(screen, (255, 255, 255), (int(helmet_x), int(helmet_y)), helmet_radius)
        pygame.draw.circle(screen, (200, 200, 200), (int(helmet_x), int(helmet_y)), helmet_radius, 2)
        
        # Draw visor
        visor_x, visor_y = rot(0, -20)
        visor_rect = pygame.Rect(int(visor_x - 8), int(visor_y - 4), 16, 8)
        pygame.draw.ellipse(screen, (100, 200, 255), visor_rect)
        pygame.draw.ellipse(screen, (50, 150, 255), visor_rect, 2)
        # Visor reflection
        pygame.draw.ellipse(screen, (150, 220, 255), (int(visor_x - 4), int(visor_y - 2), 6, 4))
        
        # Draw arms
        # Left arm (relative to player)
        left_arm_points = [
            rot(-15, 0), rot(-7, 0), rot(-7, 18), rot(-15, 18)
        ]
        pygame.draw.polygon(screen, (255, 255, 255), left_arm_points)
        hand1_x, hand1_y = rot(-11, 18)
        pygame.draw.circle(screen, (255, 255, 255), (int(hand1_x), int(hand1_y)), 6)
        
        # Right arm
        right_arm_points = [
            rot(7, 0), rot(15, 0), rot(15, 18), rot(7, 18)
        ]
        pygame.draw.polygon(screen, (255, 255, 255), right_arm_points)
        hand2_x, hand2_y = rot(11, 18)
        pygame.draw.circle(screen, (255, 255, 255), (int(hand2_x), int(hand2_y)), 6)
        
        # Draw legs
        # Left leg
        left_leg_points = [
            rot(-8, 20), rot(-1, 20), rot(-1, 35), rot(-8, 35)
        ]
        pygame.draw.polygon(screen, (255, 255, 255), left_leg_points)
        boot1_x, boot1_y = rot(-5, 35)
        pygame.draw.circle(screen, (100, 100, 100), (int(boot1_x), int(boot1_y)), 5)
        
        # Right leg
        right_leg_points = [
            rot(1, 20), rot(8, 20), rot(8, 35), rot(1, 35)
        ]
        pygame.draw.polygon(screen, (255, 255, 255), right_leg_points)
        boot2_x, boot2_y = rot(4, 35)
        pygame.draw.circle(screen, (100, 100, 100), (int(boot2_x), int(boot2_y)), 5)
    
    def get_rect(self):
        # Smaller collision box - only the body/torso, not including flames or extended parts
        # This ensures flames don't trigger collisions with obstacles
        body_width = 20
        body_height = 30
        return pygame.Rect(self.x - body_width // 2, self.y - 5, 
                          body_width, body_height)

class Star:
    def __init__(self):
        self.x = random.randint(STAR_SIZE, WIDTH - STAR_SIZE)
        self.y = random.randint(STAR_SIZE, HEIGHT - STAR_SIZE)
        self.size = STAR_SIZE
        self.color = random.choice(STAR_COLORS)
        self.rotation = 0
        self.pulse = 0
        
    def update(self):
        self.rotation += 5
        self.pulse += 0.2
        
    def draw(self, screen):
        # Draw a star shape
        size = self.size + int(math.sin(self.pulse) * 3)
        points = []
        center_x, center_y = int(self.x), int(self.y)
        
        for i in range(10):
            angle = (self.rotation + i * 36) * math.pi / 180
            if i % 2 == 0:
                radius = size
            else:
                radius = size // 2
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            points.append((x, y))
        
        pygame.draw.polygon(screen, self.color, points)
        pygame.draw.polygon(screen, (255, 255, 255), points, 2)
    
    def get_rect(self):
        return pygame.Rect(self.x - self.size, self.y - self.size, 
                          self.size * 2, self.size * 2)

class Obstacle:
    def __init__(self):
        self.x = random.randint(OBSTACLE_SIZE, WIDTH - OBSTACLE_SIZE)
        self.y = random.randint(OBSTACLE_SIZE, HEIGHT - OBSTACLE_SIZE)
        self.size = OBSTACLE_SIZE
        self.rotation = 0
        self.speed = random.uniform(1, 3)
        self.angle = random.uniform(0, 2 * math.pi)
        # Generate random shape points for comet (more circular)
        self.shape_points = []
        num_points = 16  # More points for smoother circle
        for i in range(num_points):
            angle = (i * 360 / num_points) * math.pi / 180
            # Less randomness for more circular shape
            radius_variation = random.uniform(0.90, 1.0)  # Very small variation
            self.shape_points.append((angle, radius_variation))
        # Generate random crater positions
        self.craters = []
        num_craters = random.randint(2, 4)
        for _ in range(num_craters):
            self.craters.append({
                'x': random.uniform(-0.6, 0.6),
                'y': random.uniform(-0.6, 0.6),
                'size': random.uniform(0.15, 0.3)
            })
        
    def update(self):
        self.rotation += 3
        self.x += self.speed * math.cos(self.angle)
        self.y += self.speed * math.sin(self.angle)
        
        # Bounce off walls
        if self.x <= OBSTACLE_SIZE or self.x >= WIDTH - OBSTACLE_SIZE:
            self.angle = math.pi - self.angle
        if self.y <= OBSTACLE_SIZE or self.y >= HEIGHT - OBSTACLE_SIZE:
            self.angle = -self.angle
            
        self.x = max(OBSTACLE_SIZE, min(WIDTH - OBSTACLE_SIZE, self.x))
        self.y = max(OBSTACLE_SIZE, min(HEIGHT - OBSTACLE_SIZE, self.y))
    
    def draw(self, screen):
        center_x, center_y = int(self.x), int(self.y)
        
        # Draw the comet body with irregular shape
        outer_points = []
        
        for angle_offset, radius_var in self.shape_points:
            angle = angle_offset + self.rotation * math.pi / 180
            radius = self.size * radius_var
            outer_points.append((
                center_x + radius * math.cos(angle),
                center_y + radius * math.sin(angle)
            ))
        
        # Draw base comet shape
        if len(outer_points) > 2:
            pygame.draw.polygon(screen, COMET_BASE_COLOR, outer_points)
        
        # Draw shading based on light direction (from top-left)
        light_x = center_x - self.size * 0.3
        light_y = center_y - self.size * 0.3
        
        # Draw shadow side (darker purple on the right/bottom)
        shadow_points = []
        highlight_points = []
        for px, py in outer_points:
            # Calculate distance from light source
            dx_light = px - light_x
            dy_light = py - light_y
            dist_from_light = math.sqrt(dx_light*dx_light + dy_light*dy_light)
            
            # Points further from light are darker
            if dist_from_light > self.size * 0.8:
                shadow_points.append((px, py))
            else:
                highlight_points.append((px, py))
        
        # Draw shadow regions
        if len(shadow_points) >= 2:
            # Create shadow polygon
            shadow_poly = shadow_points.copy()
            # Add center point to create a fan shape
            shadow_poly.append((center_x, center_y))
            if len(shadow_poly) > 2:
                pygame.draw.polygon(screen, COMET_DARK, shadow_poly)
        
        # Draw highlight regions (lighter purple on the light side)
        if len(highlight_points) >= 2:
            highlight_poly = highlight_points.copy()
            highlight_poly.append((center_x, center_y))
            if len(highlight_poly) > 2:
                pygame.draw.polygon(screen, COMET_LIGHT, highlight_poly)
        
        # Add a bright highlight spot on the light side
        highlight_spot_x = center_x - self.size * 0.4
        highlight_spot_y = center_y - self.size * 0.4
        pygame.draw.circle(screen, (220, 100, 220), 
                         (int(highlight_spot_x), int(highlight_spot_y)), 
                         int(self.size * 0.3))
        
        # Draw craters (dark holes)
        for crater in self.craters:
            crater_x = center_x + crater['x'] * self.size
            crater_y = center_y + crater['y'] * self.size
            crater_size = self.size * crater['size']
            
            # Draw crater shadow (dark center)
            pygame.draw.circle(screen, CRATER_COLOR, 
                             (int(crater_x), int(crater_y)), 
                             int(crater_size))
            # Draw crater rim (slightly lighter)
            pygame.draw.circle(screen, COMET_DARK, 
                             (int(crater_x), int(crater_y)), 
                             int(crater_size), 1)
            # Draw inner shadow
            pygame.draw.circle(screen, (40, 0, 40), 
                             (int(crater_x), int(crater_y)), 
                             int(crater_size * 0.6))
        
        # Draw outline for definition
        if len(outer_points) > 2:
            pygame.draw.polygon(screen, (100, 0, 100), outer_points, 2)
    
    def get_rect(self):
        return pygame.Rect(self.x - self.size, self.y - self.size, 
                          self.size * 2, self.size * 2)

class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(-3, 3)
        self.color = random.choice(PARTICLE_COLORS)
        self.life = 30
        self.size = random.randint(3, 6)
        
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        self.vy += 0.2  # Gravity
        
    def draw(self, screen):
        alpha = int(255 * (self.life / 30))
        color = tuple(min(255, c) for c in self.color)
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), self.size)
    
    def is_alive(self):
        return self.life > 0

def load_high_score():
    """Load high score from file, return 0 if file doesn't exist"""
    if os.path.exists(HIGH_SCORE_FILE):
        try:
            with open(HIGH_SCORE_FILE, 'r') as f:
                return int(f.read().strip())
        except (ValueError, IOError):
            return 0
    return 0

def save_high_score(score):
    """Save high score to file"""
    try:
        with open(HIGH_SCORE_FILE, 'w') as f:
            f.write(str(score))
    except IOError:
        pass  # If we can't save, just continue

def main():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("🌟 Star Collector - Use Arrow Keys or WASD!")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 36)
    big_font = pygame.font.Font(None, 72)
    
    # Game state
    player = Player(WIDTH // 2, HEIGHT // 2)
    stars = []
    obstacles = []
    particles = []
    projectiles = []
    score = 0
    high_score = load_high_score()
    game_over = False
    
    # Main game loop
    running = True
    while running:
        clock.tick(FPS)
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and game_over:
                    # Restart game
                    player = Player(WIDTH // 2, HEIGHT // 2)
                    stars = []
                    obstacles = []
                    particles = []
                    projectiles = []
                    score = 0
                    game_over = False
                    high_score = load_high_score()  # Reload high score in case it was updated
        
        if not game_over:
            # Handle input
            keys = pygame.key.get_pressed()
            dx, dy = 0, 0
            
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                dx -= player.speed
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                dx += player.speed
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                dy -= player.speed
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                dy += player.speed
            
            player.move(dx, dy)
            
            # Auto-shoot in the direction player is moving (headfirst)
            if dx != 0 or dy != 0:
                projectile = player.shoot()
                if projectile:
                    projectiles.append(projectile)
            
            # Update projectiles
            for projectile in projectiles[:]:
                projectile.update()
                if projectile.is_off_screen():
                    projectiles.remove(projectile)
                else:
                    # Check collision with obstacles
                    for obstacle in obstacles[:]:
                        if projectile.get_rect().colliderect(obstacle.get_rect()):
                            obstacles.remove(obstacle)
                            projectiles.remove(projectile)
                            score += 5  # Bonus for destroying obstacles
                            # Create particles
                            for _ in range(PARTICLE_COUNT):
                                particles.append(Particle(obstacle.x, obstacle.y))
                            break
            
            # Spawn stars
            if random.random() < STAR_SPAWN_RATE and len(stars) < 10:
                stars.append(Star())
            
            # Spawn obstacles
            if random.random() < OBSTACLE_SPAWN_RATE and len(obstacles) < 5:
                obstacles.append(Obstacle())
            
            # Update stars
            for star in stars[:]:
                star.update()
                if player.get_rect().colliderect(star.get_rect()):
                    # Collect star
                    stars.remove(star)
                    score += 10
                    # Create particles
                    for _ in range(PARTICLE_COUNT):
                        particles.append(Particle(star.x, star.y))
            
            # Update obstacles
            for obstacle in obstacles[:]:
                obstacle.update()
                if player.get_rect().colliderect(obstacle.get_rect()):
                    game_over = True
                    # Update high score if needed
                    if score > high_score:
                        high_score = score
                        save_high_score(high_score)
            
            # Update particles
            for particle in particles[:]:
                particle.update()
                if not particle.is_alive():
                    particles.remove(particle)
        
        # Draw everything
        screen.fill(BACKGROUND)
        
        # Draw stars
        for star in stars:
            star.draw(screen)
        
        # Draw obstacles
        for obstacle in obstacles:
            obstacle.draw(screen)
        
        # Draw particles
        for particle in particles:
            particle.draw(screen)
        
        # Draw projectiles
        for projectile in projectiles:
            projectile.draw(screen)
        
        # Draw player
        player.draw(screen)
        
        # Draw UI
        score_text = font.render(f"Score: {score}", True, TEXT_COLOR)
        high_score_text = font.render(f"High Score: {high_score}", True, TEXT_COLOR)
        screen.blit(score_text, (10, 10))
        screen.blit(high_score_text, (10, 50))
        
        if game_over:
            # Draw game over screen
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(180)
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))
            
            game_over_text = big_font.render("GAME OVER!", True, (255, 50, 50))
            final_score_text = font.render(f"Final Score: {score}", True, TEXT_COLOR)
            restart_text = font.render("Press R to Restart", True, TEXT_COLOR)
            
            screen.blit(game_over_text, 
                       (WIDTH // 2 - game_over_text.get_width() // 2, 
                        HEIGHT // 2 - 100))
            screen.blit(final_score_text, 
                       (WIDTH // 2 - final_score_text.get_width() // 2, 
                        HEIGHT // 2 - 20))
            screen.blit(restart_text, 
                       (WIDTH // 2 - restart_text.get_width() // 2, 
                        HEIGHT // 2 + 40))
        else:
            # Draw instructions
            if score == 0:
                instructions = font.render("Use Arrow Keys or WASD to move!", True, TEXT_COLOR)
                screen.blit(instructions, 
                           (WIDTH // 2 - instructions.get_width() // 2, HEIGHT - 50))
        
        pygame.display.flip()
    
    pygame.quit()

if __name__ == "__main__":
    main()


