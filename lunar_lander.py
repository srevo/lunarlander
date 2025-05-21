import pygame
import sys
import math
import random
import time

# Initialize Pygame
pygame.init()

# --- Constants ---
SCREEN_WIDTH = 800  # Width of the game window in pixels
SCREEN_HEIGHT = 600 # Height of the game window in pixels
GRAVITY = 0.05      # Strength of gravity affecting the lander
THRUST_POWER = 0.1  # Power of the lander's thruster
ROTATION_SPEED = 3  # Speed at which the lander rotates (degrees per frame)
INITIAL_FUEL = 1000 # Starting amount of fuel for the lander
FPS = 60            # Frames per second for the game loop

# Colors (RGB tuples)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0) # Color for the thrust flame
GRAY = (150, 150, 150)   # Color for the terrain

# --- Lander Class ---
# Represents the player-controlled lunar lander.
class Lander:
    def __init__(self, x, y):
        """
        Initialize the Lander object.
        Args:
            x (int): Initial x-coordinate of the lander.
            y (int): Initial y-coordinate of the lander.
        """
        self.x = x  # Current x-coordinate
        self.y = y  # Current y-coordinate
        self.vel_x = 0  # Horizontal velocity
        self.vel_y = 0  # Vertical velocity
        self.angle = 0  # In degrees, 0 means pointing upwards (Pygame's y-axis is inverted)
        self.fuel = INITIAL_FUEL
        self.thrusting = False # True if thruster is currently active
        self.width = 20   # Width of the lander model
        self.height = 30  # Height of the lander model
        
        # Define the lander's shape as a list of points relative to its center.
        # This is a simple triangle. (0,0) is the center of the lander.
        self.points = [
            (0, -self.height/2),            # Top point
            (-self.width/2, self.height/2), # Bottom-left point
            (self.width/2, self.height/2)   # Bottom-right point
        ]
        
    def rotate(self, direction):
        """
        Rotate the lander.
        Args:
            direction (int): +1 for clockwise, -1 for counter-clockwise.
        """
        self.angle += direction * ROTATION_SPEED
        
    def apply_thrust(self):
        """Apply thrust in the direction the lander is pointing."""
        if self.fuel > 0:
            # Convert angle to radians.
            # Angle is adjusted by -90 degrees because in Pygame, 0 degrees is typically to the right,
            # but our lander's 0 degrees is upwards.
            angle_rad = math.radians(self.angle - 90)
            
            # Calculate thrust components based on the angle.
            self.vel_x += THRUST_POWER * math.cos(angle_rad)
            self.vel_y += THRUST_POWER * math.sin(angle_rad) # Sin is used for y due to angle adjustment.
            
            self.fuel -= 1  # Consume fuel
            self.thrusting = True
        else:
            self.thrusting = False # No fuel, no thrust
            
    def update(self):
        """Update lander's position and velocity based on game physics."""
        # Apply gravity (acts downwards, increasing y-velocity)
        self.vel_y += GRAVITY
        
        # Update position based on current velocity
        self.x += self.vel_x
        self.y += self.vel_y
        
        # Screen boundary conditions: wrap around horizontally.
        if self.x < 0:
            self.x = SCREEN_WIDTH
        elif self.x > SCREEN_WIDTH:
            self.x = 0
            
        # Screen boundary conditions: prevent going off the top of the screen.
        # Bottom boundary (collision with terrain) is handled separately.
        if self.y < 0:
            self.y = 0
            self.vel_y = 0 # Stop vertical movement if it hits the top
    
    def get_transformed_points(self):
        """
        Calculate the lander's current screen coordinates for its points
        after rotation and translation (positioning).
        Returns:
            list: A list of (x, y) tuples representing the lander's vertices on the screen.
        """
        transformed_points = []
        angle_rad = math.radians(self.angle) # Convert current angle to radians for math functions
        
        for point_x_rel, point_y_rel in self.points: # Iterate through the lander's local points
            # Standard 2D rotation formulas
            rotated_x = point_x_rel * math.cos(angle_rad) - point_y_rel * math.sin(angle_rad)
            rotated_y = point_x_rel * math.sin(angle_rad) + point_y_rel * math.cos(angle_rad)
            
            # Translate the rotated points to the lander's current position on screen
            transformed_points.append((rotated_x + self.x, rotated_y + self.y))
            
        return transformed_points
    
    def draw(self, screen):
        """
        Draw the lander on the provided Pygame screen.
        Args:
            screen (pygame.Surface): The screen to draw on.
        """
        # Get the current screen coordinates of the lander's vertices
        points_on_screen = self.get_transformed_points()
        
        # Draw the lander's body (polygon)
        pygame.draw.polygon(screen, WHITE, points_on_screen)
        
        # Draw thrust flame if the thruster is active and there's fuel
        if self.thrusting and self.fuel > 0:
            # Find the bottom-most point of the lander to draw the flame from
            bottom_center_local = (0, self.height / 2) # Relative bottom center of the lander model

            # Rotate this bottom point similar to other points
            angle_rad_flame_base = math.radians(self.angle)
            rotated_flame_base_x = bottom_center_local[0] * math.cos(angle_rad_flame_base) - bottom_center_local[1] * math.sin(angle_rad_flame_base)
            rotated_flame_base_y = bottom_center_local[0] * math.sin(angle_rad_flame_base) + bottom_center_local[1] * math.cos(angle_rad_flame_base)
            
            # Translate to screen position
            flame_start_x = rotated_flame_base_x + self.x
            flame_start_y = rotated_flame_base_y + self.y
            flame_start_point = (flame_start_x, flame_start_y)

            # Calculate the direction of the flame (opposite to lander's orientation)
            # Angle is adjusted by -90 degrees (same as in apply_thrust)
            flame_angle_rad = math.radians(self.angle - 90)
            flame_length = random.randint(10, 20) # Flame has a random length for visual effect
            
            # Calculate the end point of the flame
            flame_end_x = flame_start_x - flame_length * math.cos(flame_angle_rad) # Subtract because flame goes "out"
            flame_end_y = flame_start_y - flame_length * math.sin(flame_angle_rad)
            
            pygame.draw.line(screen, YELLOW, flame_start_point, (flame_end_x, flame_end_y), 3) # Draw the flame as a line
    
    def get_bottom_point(self):
        """
        Return the screen coordinates of the lander's bottom-most point.
        Useful for simple collision detection or reference.
        """
        points = self.get_transformed_points()
        # Find the point with the largest y-coordinate (bottom-most on screen)
        # Note: This might not be the geometric "bottom" if the lander is very tilted.
        # For more accurate collision, using all points or bounding box is better.
        if not points: return (self.x, self.y) # Should not happen if points are defined
        bottom_point = max(points, key=lambda p: p[1])
        return bottom_point
    
    def get_bounding_box(self):
        """
        Return the AABB (Axis-Aligned Bounding Box) of the lander.
        Returns:
            tuple: (min_x, min_y, max_x, max_y)
        """
        points = self.get_transformed_points()
        if not points: # Should not happen
            return (self.x - self.width/2, self.y - self.height/2, 
                    self.x + self.width/2, self.y + self.height/2)

        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        
        return (min(xs), min(ys), max(xs), max(ys)) # (left, top, right, bottom)

# --- Terrain Class ---
# Represents the game terrain, including the landing pad.
class Terrain:
    def __init__(self, width, height):
        """
        Initialize the Terrain object.
        Args:
            width (int): The width of the terrain (screen width).
            height (int): The height of the terrain (screen height).
        """
        self.width = width
        self.height = height
        self.landing_pad_width = 50  # Width of the flat landing area
        # Randomly position the landing pad horizontally
        self.landing_pad_position = random.randint(100, width - 100 - self.landing_pad_width)
        self.landing_pad_height = height - 100 # Y-coordinate of the landing pad surface
        self.generate_terrain()
        
    def generate_terrain(self):
        """Generate a random terrain profile with a flat landing pad."""
        self.points = [] # List to store (x,y) points of the terrain surface
        num_points = 20  # Number of segments to divide the terrain into
        
        segment_width = self.width / num_points
        
        # Generate terrain points
        for i in range(num_points + 1):
            x = i * segment_width
            
            # If current x is within the landing pad's horizontal range, make it flat
            if self.landing_pad_position <= x <= self.landing_pad_position + self.landing_pad_width:
                y = self.landing_pad_height
            else:
                # Otherwise, generate a random height for rugged terrain
                y = random.randint(self.height - 200, self.height - 50)
            
            self.points.append((x, y))
        
        # Add bottom corners to close the polygon shape for drawing
        self.points.append((self.width, self.height)) # Bottom-right screen corner
        self.points.append((0, self.height))          # Bottom-left screen corner
    
    def draw(self, screen):
        """
        Draw the terrain on the provided Pygame screen.
        Args:
            screen (pygame.Surface): The screen to draw on.
        """
        # Draw the main terrain polygon
        pygame.draw.polygon(screen, GRAY, self.points)
        
        # Highlight the landing pad with a different color line
        pad_left_x = self.landing_pad_position
        pad_right_x = self.landing_pad_position + self.landing_pad_width
        pygame.draw.line(screen, GREEN, (pad_left_x, self.landing_pad_height), 
                         (pad_right_x, self.landing_pad_height), 3) # Line thickness 3
    
    def check_collision(self, lander):
        """
        Check if the lander has collided with the terrain.
        Args:
            lander (Lander): The lander object.
        Returns:
            tuple: (collided (bool), is_on_landing_pad (bool))
        """
        # Get the lander's transformed points (vertices on screen)
        lander_points = lander.get_transformed_points()

        # Iterate over each edge of the lander polygon
        for i in range(len(lander_points)):
            p1_lander = lander_points[i]
            p2_lander = lander_points[(i + 1) % len(lander_points)] # Next point, wraps around

            # Iterate over each segment of the terrain surface
            # We go up to len(self.points) - 3 because the last two points are screen corners for closing the polygon
            # and are not part of the actual interactable surface.
            for j in range(len(self.points) - 3):
                p1_terrain = self.points[j]
                p2_terrain = self.points[j+1]

                # Basic line segment intersection check (simplified for this context)
                # A more robust method would be Separating Axis Theorem for polygon-polygon collision.
                # This simplified check primarily looks at the lander's bottom points against terrain segments.

                # Let's use the lander's bottom-most point for a simpler collision check here.
                # This isn't perfectly accurate for all orientations but is common in simpler lander games.
                bottom_lander_point = lander.get_bottom_point() # The lander's lowest point

                # Check if this bottom point is below any terrain segment
                # We need to check if the bottom_lander_point.x is within the terrain segment's x range
                terrain_segment_x_coords = sorted([p1_terrain[0], p2_terrain[0]])
                if terrain_segment_x_coords[0] <= bottom_lander_point[0] <= terrain_segment_x_coords[1]:
                    # Linearly interpolate the terrain's y-height at the lander's bottom point x-coordinate
                    # (y - y1) / (x - x1) = (y2 - y1) / (x2 - x1)  => y = y1 + ...
                    # Avoid division by zero if terrain segment is vertical (should not happen with current generation)
                    if (p2_terrain[0] - p1_terrain[0]) == 0:
                        terrain_y_at_lander_x = min(p1_terrain[1], p2_terrain[1]) if bottom_lander_point[0] == p1_terrain[0] else float('inf')
                    else:
                        terrain_y_at_lander_x = p1_terrain[1] + (p2_terrain[1] - p1_terrain[1]) * \
                                               (bottom_lander_point[0] - p1_terrain[0]) / (p2_terrain[0] - p1_terrain[0])
                    
                    # If lander's bottom point's y is greater than or equal to terrain's y at that x, it's a collision.
                    if bottom_lander_point[1] >= terrain_y_at_lander_x:
                        # Collision detected. Now check if it's on the landing pad.
                        is_on_pad = (self.landing_pad_position <= bottom_lander_point[0] <=
                                     self.landing_pad_position + self.landing_pad_width and
                                     abs(terrain_y_at_lander_x - self.landing_pad_height) < 5) # Tolerance for y-match
                        
                        return True, is_on_pad
        
        return False, False # No collision detected
                    
    def get_landing_pad_center(self):
        """Return the center (x, y) coordinates of the landing pad."""
        center_x = self.landing_pad_position + self.landing_pad_width / 2
        return (center_x, self.landing_pad_height)

# --- Game Class ---
# Manages the main game loop, game states, and interactions between objects.
class Game:
    def __init__(self):
        """Initialize the game environment and objects."""
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Lunar Lander") # Window title
        self.clock = pygame.time.Clock() # Clock for controlling FPS
        self.font = pygame.font.SysFont('Arial', 20) # Font for displaying text
        self.reset_game() # Initialize game state
    
    def reset_game(self):
        """Reset the game to its initial state for a new playthrough."""
        # Create a new lander instance, positioned at the top-center of the screen.
        self.lander = Lander(SCREEN_WIDTH / 2, 50)
        # Generate a new terrain.
        self.terrain = Terrain(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.game_over = False  # True if the lander has crashed or landed
        self.landed = False     # True if the lander has landed successfully
        self.score = 0          # Player's score
        self.time_started = time.time() # Record the start time for scoring
    
    def handle_input(self):
        """Handle user input events (keyboard, window close)."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT: # User clicked the window close button
                pygame.quit() # Uninitialize Pygame modules
                sys.exit()    # Exit the program
            elif event.type == pygame.KEYDOWN:
                # If the game is over, allow restarting by pressing 'R'
                if event.key == pygame.K_r and self.game_over:
                    self.reset_game()
        
        # Handle continuous key presses for lander controls (only if game is not over)
        if not self.game_over:
            keys = pygame.key.get_pressed() # Get the state of all keyboard buttons
            if keys[pygame.K_LEFT]: # Left arrow key
                self.lander.rotate(-1) # Rotate counter-clockwise
            if keys[pygame.K_RIGHT]: # Right arrow key
                self.lander.rotate(1)  # Rotate clockwise
            if keys[pygame.K_UP]:    # Up arrow key
                self.lander.apply_thrust()
            else:
                # If up arrow is not pressed, ensure thrusting flag is false
                # (for correctly drawing the flame)
                self.lander.thrusting = False
    
    def update(self):
        """Update the state of all game objects."""
        if self.game_over: # If game is over, no more updates needed
            return
        
        self.lander.update() # Update lander's physics and position
        
        # Check for collision between the lander and the terrain
        collision, is_landing_pad = self.terrain.check_collision(self.lander)
        
        if collision:
            self.game_over = True # Game ends on any collision
            
            if is_landing_pad:
                # Conditions for a safe landing:
                safe_landing_speed_vertical = 1.0  # Max vertical speed for safe landing
                safe_landing_speed_horizontal = 1.0 # Max horizontal speed
                upright_angle_threshold = 15 # Max deviation from vertical (0 or 360 degrees)
                
                current_angle = self.lander.angle % 360
                is_upright = (current_angle < upright_angle_threshold or \
                              current_angle > (360 - upright_angle_threshold))

                # Check if the landing was successful based on speed and orientation
                if (abs(self.lander.vel_y) < safe_landing_speed_vertical and 
                    abs(self.lander.vel_x) < safe_landing_speed_horizontal and
                    is_upright):
                    self.landed = True # Mark as a successful landing
                    
                    # Calculate score:
                    fuel_bonus = self.lander.fuel # Points for remaining fuel
                    
                    # Position accuracy bonus:
                    # Closer to the center of the pad means more points.
                    landing_pad_center_x, _ = self.terrain.get_landing_pad_center()
                    distance_from_center = abs(self.lander.x - landing_pad_center_x)
                    # Max distance for scoring is half the pad width. Further than that gives 0 position points.
                    max_distance_for_bonus = self.terrain.landing_pad_width / 2
                    position_factor = max(0, 1 - (distance_from_center / max_distance_for_bonus))
                    position_score = int(100 * position_factor) # Max 100 points for position
                    
                    # Time bonus: faster landing gets more points.
                    time_taken = time.time() - self.time_started
                    time_score = max(0, int(500 - time_taken * 5)) # Arbitrary calculation for time bonus
                    
                    self.score = fuel_bonus + position_score + time_score
                else:
                    self.landed = False # Landed on pad, but too hard or tilted (crash)
            else:
                self.landed = False # Collided with terrain, not on the pad (crash)
    
    def draw(self):
        """Draw all game elements to the screen."""
        # Fill the screen with black (space background)
        self.screen.fill(BLACK)
        
        # Draw some stars for a simple background effect
        # Note: Drawing stars every frame like this can be inefficient.
        # A better approach would be to blit a pre-rendered starfield image.
        for _ in range(100): # Draw 100 stars at random positions
            star_pos = (random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT))
            self.screen.set_at(star_pos, WHITE) # set_at is slow, use sparingly or on a static surface
        
        # Draw the terrain
        self.terrain.draw(self.screen)
        
        # Draw the lander
        self.lander.draw(self.screen)
        
        # Draw the Heads-Up Display (HUD)
        self.draw_hud()
        
        # If the game is over, display a message
        if self.game_over:
            self.draw_game_over()
        
        pygame.display.flip() # Update the full display Surface to the screen
    
    def draw_hud(self):
        """Draw the HUD elements (fuel, velocity, angle, score)."""
        # Display current fuel
        fuel_text = self.font.render(f"Fuel: {self.lander.fuel}", True, WHITE)
        self.screen.blit(fuel_text, (10, 10)) # Position at top-left
        
        # Display current velocity magnitude
        vel_magnitude = math.sqrt(self.lander.vel_x**2 + self.lander.vel_y**2)
        vel_text = self.font.render(f"Velocity: {vel_magnitude:.2f}", True, WHITE)
        self.screen.blit(vel_text, (10, 40))
        
        # Display current angle (0-360 degrees)
        angle_display = self.lander.angle % 360
        angle_text = self.font.render(f"Angle: {angle_display:.1f}°", True, WHITE)
        self.screen.blit(angle_text, (10, 70))
        
        # Display score if the game is over and lander landed successfully
        if self.game_over and self.landed:
            score_text = self.font.render(f"Score: {self.score}", True, GREEN)
            self.screen.blit(score_text, (10, 100))
    
    def draw_game_over(self):
        """Display the game over message or landing successful message."""
        if self.landed:
            message = "Landing Successful! Press R to restart"
            color = GREEN
        else:
            message = "Crash! Press R to restart"
            color = RED
        
        # Render the text
        text_surface = self.font.render(message, True, color)
        # Get the rectangle of the text surface to center it
        text_rect = text_surface.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))
        self.screen.blit(text_surface, text_rect) # Draw the text
    
    def run(self):
        """Main game loop that drives the game."""
        while True: # Loop indefinitely until game exits
            self.handle_input() # Process inputs
            self.update()       # Update game state
            self.draw()         # Render the game
            self.clock.tick(FPS) # Maintain the desired frame rate

# --- Main execution ---
# This block runs if the script is executed directly (not imported as a module).
if __name__ == "__main__":
    game = Game() # Create an instance of the Game
    game.run()    # Start the game loop

