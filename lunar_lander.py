import pygame
import sys
import math
import random
import time

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
GRAVITY = 0.05
THRUST_POWER = 0.1
ROTATION_SPEED = 3
INITIAL_FUEL = 1000
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
GRAY = (150, 150, 150)

class Lander:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vel_x = 0
        self.vel_y = 0
        self.angle = 0  # In degrees, 0 means pointing upwards
        self.fuel = INITIAL_FUEL
        self.thrusting = False
        self.width = 20
        self.height = 30
        
        # Create a simple triangular lander shape
        self.points = [
            (0, -self.height/2),  # Top
            (-self.width/2, self.height/2),  # Bottom left
            (self.width/2, self.height/2)  # Bottom right
        ]
        
    def rotate(self, direction):
        """Rotate the lander (direction: +1 clockwise, -1 counterclockwise)"""
        self.angle += direction * ROTATION_SPEED
        
    def apply_thrust(self):
        """Apply thrust in the direction the lander is pointing"""
        if self.fuel > 0:
            # Convert angle to radians and calculate thrust components
            angle_rad = math.radians(self.angle - 90)  # -90 because 0 degrees is pointing up
            self.vel_x += THRUST_POWER * math.cos(angle_rad)
            self.vel_y += THRUST_POWER * math.sin(angle_rad)
            self.fuel -= 1
            self.thrusting = True
        else:
            self.thrusting = False
            
    def update(self):
        """Update lander position and velocity"""
        # Apply gravity
        self.vel_y += GRAVITY
        
        # Update position based on velocity
        self.x += self.vel_x
        self.y += self.vel_y
        
        # Boundary conditions (wrap around the screen)
        if self.x < 0:
            self.x = SCREEN_WIDTH
        elif self.x > SCREEN_WIDTH:
            self.x = 0
            
        # Keep the lander in the screen vertically
        if self.y < 0:
            self.y = 0
            self.vel_y = 0
    
    def get_transformed_points(self):
        """Return the lander's points transformed by position and rotation"""
        transformed_points = []
        angle_rad = math.radians(self.angle)
        
        for point in self.points:
            # Rotate
            rotated_x = point[0] * math.cos(angle_rad) - point[1] * math.sin(angle_rad)
            rotated_y = point[0] * math.sin(angle_rad) + point[1] * math.cos(angle_rad)
            
            # Translate
            transformed_points.append((rotated_x + self.x, rotated_y + self.y))
            
        return transformed_points
    
    def draw(self, screen):
        """Draw the lander on the screen"""
        points = self.get_transformed_points()
        
        # Draw the lander body
        pygame.draw.polygon(screen, WHITE, points)
        
        # Draw thrust flame if thrusting
        if self.thrusting and self.fuel > 0:
            # Get the bottom middle point of the lander
            bottom_point = self.get_bottom_point()
            
            # Draw a simple flame
            angle_rad = math.radians(self.angle - 90)
            flame_length = random.randint(10, 20)
            flame_end_x = bottom_point[0] - flame_length * math.cos(angle_rad)
            flame_end_y = bottom_point[1] - flame_length * math.sin(angle_rad)
            
            pygame.draw.line(screen, YELLOW, bottom_point, (flame_end_x, flame_end_y), 3)
    
    def get_bottom_point(self):
        """Return the bottom point of the lander for collision detection and thrust display"""
        points = self.get_transformed_points()
        # Find the point with the largest y value (bottom-most point)
        bottom_point = max(points, key=lambda p: p[1])
        return bottom_point
    
    def get_bounding_box(self):
        """Return the bounding box of the lander for collision detection"""
        points = self.get_transformed_points()
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        
        return (min(xs), min(ys), max(xs), max(ys))

class Terrain:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.landing_pad_width = 50
        self.landing_pad_position = random.randint(100, width - 100 - self.landing_pad_width)
        self.landing_pad_height = height - 100
        self.generate_terrain()
        
    def generate_terrain(self):
        """Generate a random terrain with a flat landing pad"""
        self.points = []
        num_points = 20
        
        # Divide the screen width into segments
        segment_width = self.width / num_points
        
        for i in range(num_points + 1):
            x = i * segment_width
            
            # Create a flat landing pad
            if self.landing_pad_position <= x <= self.landing_pad_position + self.landing_pad_width:
                y = self.landing_pad_height
            else:
                # Random terrain height
                y = random.randint(self.height - 200, self.height - 50)
            
            self.points.append((x, y))
        
        # Add bottom corners to close the terrain shape
        self.points.append((self.width, self.height))
        self.points.append((0, self.height))
    
    def draw(self, screen):
        """Draw the terrain on the screen"""
        # Draw the main terrain
        pygame.draw.polygon(screen, GRAY, self.points)
        
        # Draw the landing pad in a different color
        pad_left = self.landing_pad_position
        pad_right = self.landing_pad_position + self.landing_pad_width
        pygame.draw.line(screen, GREEN, (pad_left, self.landing_pad_height), 
                         (pad_right, self.landing_pad_height), 3)
    
    def check_collision(self, lander):
        """Check if the lander has collided with the terrain"""
        lander_box = lander.get_bounding_box()
        bottom_point = lander.get_bottom_point()
        
        # Check if the lander's bottom point is below any terrain point
        for i in range(len(self.points) - 3):  # Exclude the last 2 points (bottom corners)
            x1, y1 = self.points[i]
            x2, y2 = self.points[i + 1]
            
            # Check if the bottom point is within this terrain segment horizontally
            if x1 <= bottom_point[0] <= x2 or x2 <= bottom_point[0] <= x1:
                # Calculate the y value of the terrain at this x position using linear interpolation
                terrain_y = y1 + (y2 - y1) * (bottom_point[0] - x1) / (x2 - x1)
                
                # Check if the lander's bottom point is below the terrain
                if bottom_point[1] >= terrain_y:
                    # Check if it's a landing pad
                    is_landing_pad = (self.landing_pad_position <= bottom_point[0] <= 
                                     self.landing_pad_position + self.landing_pad_width and
                                     abs(terrain_y - self.landing_pad_height) < 1)
                    
                    return True, is_landing_pad
        
        return False, False
                    
    def get_landing_pad_center(self):
        """Return the center coordinates of the landing pad"""
        return (self.landing_pad_position + self.landing_pad_width / 2, self.landing_pad_height)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Lunar Lander")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('Arial', 20)
        self.reset_game()
    
    def reset_game(self):
        """Reset the game to initial state"""
        self.lander = Lander(SCREEN_WIDTH / 2, 50)
        self.terrain = Terrain(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.game_over = False
        self.landed = False
        self.score = 0
        self.time_started = time.time()
    
    def handle_input(self):
        """Handle user input"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and self.game_over:
                    self.reset_game()
        
        if not self.game_over:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT]:
                self.lander.rotate(-1)
            if keys[pygame.K_RIGHT]:
                self.lander.rotate(1)
            if keys[pygame.K_UP]:
                self.lander.apply_thrust()
            else:
                self.lander.thrusting = False
    
    def update(self):
        """Update game state"""
        if self.game_over:
            return
        
        self.lander.update()
        
        # Check for collision with terrain
        collision, is_landing_pad = self.terrain.check_collision(self.lander)
        
        if collision:
            self.game_over = True
            
            if is_landing_pad:
                # Check landing conditions
                safe_landing_speed = 1.0
                upright_angle_threshold = 15
                
                # Check if the landing was successful (slow enough and upright)
                if (abs(self.lander.vel_y) < safe_landing_speed and 
                    abs(self.lander.vel_x) < safe_landing_speed and
                    abs(self.lander.angle % 360) < upright_angle_threshold):
                    self.landed = True
                    
                    # Calculate score based on remaining fuel, landing position accuracy, and time
                    fuel_bonus = self.lander.fuel
                    
                    # Position accuracy (distance from center of landing pad)
                    landing_pad_center = self.terrain.get_landing_pad_center()
                    distance = abs(self.lander.x - landing_pad_center[0])
                    max_distance = self.terrain.landing_pad_width / 2
                    position_score = int(100 * (1 - min(1, distance / max_distance)))
                    
                    # Time bonus (faster landing gets more points)
                    time_taken = time.time() - self.time_started
                    time_score = max(0, int(500 - time_taken * 10))
                    
                    self.score = fuel_bonus + position_score + time_score
    
    def draw(self):
        """Draw everything to the screen"""
        # Clear the screen
        self.screen.fill(BLACK)
        
        # Draw stars in the background
        for _ in range(100):
            pos = (random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT))
            self.screen.set_at(pos, WHITE)
        
        # Draw the terrain
        self.terrain.draw(self.screen)
        
        # Draw the lander
        self.lander.draw(self.screen)
        
        # Draw HUD
        self.draw_hud()
        
        # Draw game over message if applicable
        if self.game_over:
            self.draw_game_over()
        
        pygame.display.flip()
    
    def draw_hud(self):
        """Draw the heads-up display with game information"""
        # Display fuel
        fuel_text = self.font.render(f"Fuel: {self.lander.fuel}", True, WHITE)
        self.screen.blit(fuel_text, (10, 10))
        
        # Display velocity
        vel_magnitude = math.sqrt(self.lander.vel_x**2 + self.lander.vel_y**2)
        vel_text = self.font.render(f"Velocity: {vel_magnitude:.2f}", True, WHITE)
        self.screen.blit(vel_text, (10, 40))
        
        # Display angle
        angle_text = self.font.render(f"Angle: {self.lander.angle % 360:.1f}°", True, WHITE)
        self.screen.blit(angle_text, (10, 70))
        
        # Display score if game is over and landed successfully
        if self.game_over and self.landed:
            score_text = self.font.render(f"Score: {self.score}", True, GREEN)
            self.screen.blit(score_text, (10, 100))
    
    def draw_game_over(self):
        """Draw game over or landing successful message"""
        if self.landed:
            message = "Landing Successful! Press R to restart"
            color = GREEN
        else:
            message = "Crash! Press R to restart"
            color = RED
        
        text = self.font.render(message, True, color)
        text_rect = text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))
        self.screen.blit(text, text_rect)
    
    def run(self):
        """Main game loop"""
        while True:
            self.handle_input()
            self.update()
            self.draw()
            self.clock.tick(FPS)

# Run the game
if __name__ == "__main__":
    game = Game()
    game.run()

