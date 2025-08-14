import pygame
import math
import random
import sys
import time
pygame.joystick.init()
class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = 20
        self.angle = 0
        self.velocity_x = 0
        self.velocity_y = 0
        self.speed = 0
        self.max_speed = 8
        self.acceleration = 0.3
        self.friction = 0.05
        self.turn_speed = 0
        self.max_turn_speed = 5
        self.bounce_offset_y = 0
        self.bounce_speed = 0
    def update(self, gas_input, turn_input, surface_friction):
        self.turn_speed = turn_input * self.max_turn_speed
        self.angle += self.turn_speed
        if gas_input > 0:
            self.speed += self.acceleration * gas_input
        self.speed *= (1 - surface_friction)
        self.speed = min(self.speed, self.max_speed)
        self.velocity_x = math.cos(math.radians(self.angle)) * self.speed
        self.velocity_y = math.sin(math.radians(self.angle)) * self.speed
        self.x += self.velocity_x
        self.y += self.velocity_y
        if self.bounce_speed != 0:
            self.bounce_offset_y += self.bounce_speed
            self.bounce_speed -= 0.5
            if self.bounce_offset_y <= 0:
                self.bounce_offset_y = 0
                self.bounce_speed = 0
    def bounce(self):
        if self.bounce_speed == 0:
            self.bounce_speed = -3
    def draw(self, screen, camera_x, camera_y):
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y + self.bounce_offset_y
        player_surface = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        player_surface.fill((100, 150, 255))
        rotated_surface = pygame.transform.rotate(player_surface, -self.angle)
        rect = rotated_surface.get_rect(center=(screen_x, screen_y))
        screen.blit(rotated_surface, rect)
        front_x = screen_x + math.cos(math.radians(self.angle)) * (self.size // 2 + 5)
        front_y = screen_y + math.sin(math.radians(self.angle)) * (self.size // 2 + 5)
        pygame.draw.circle(screen, (255, 255, 255), (int(front_x), int(front_y)), 3)
class Track:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.surface_types = {
            0: {"color": (50, 50, 50), "name": "black", "friction": 0.02, "vibration": (0, 0)},
            1: {"color": (0, 150, 0), "name": "green", "friction": 0.04, "vibration": (0.3, 0)},
            2: {"color": (200, 200, 0), "name": "yellow", "friction": 0.06, "vibration": (0.5, 0.5)},
            3: {"color": (200, 0, 0), "name": "red", "friction": 0.08, "vibration": (1.0, 1.0)}
        }
        self.generate_track()
    def generate_track(self):
        self.track = []
        for y in range(self.height // 32):
            row = []
            for x in range(self.width // 32):
                if x < 5 or x > (self.width // 32) - 5:
                    surface_type = 0  
                elif y % 10 < 3:
                    surface_type = random.choice([1, 2, 3])  
                else:
                    surface_type = random.choice([0, 0, 0, 1])  
                row.append(surface_type)
            self.track.append(row)
    def get_surface_at(self, x, y):
        grid_x = int(x // 32)
        grid_y = int(y // 32)
        if (0 <= grid_x < len(self.track[0]) and 
            0 <= grid_y < len(self.track)):
            return self.track[grid_y][grid_x]
        return 0
    def draw(self, screen, camera_x, camera_y, screen_width, screen_height):
        start_x = max(0, int(camera_x // 32))
        start_y = max(0, int(camera_y // 32))
        end_x = min(len(self.track[0]), int((camera_x + screen_width) // 32) + 1)
        end_y = min(len(self.track), int((camera_y + screen_height) // 32) + 1)
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                surface_type = self.track[y][x]
                color = self.surface_types[surface_type]["color"]
                rect = pygame.Rect(
                    x * 32 - camera_x,
                    y * 32 - camera_y,
                    32, 32
                )
                pygame.draw.rect(screen, color, rect)
                pygame.draw.rect(screen, (100, 100, 100), rect, 1)
class XboxController:
    def __init__(self):
        self.connected = False
        self.joystick = None
        self.vibration_supported = False
        if pygame.joystick.get_count() > 0:
            try:
                self.joystick = pygame.joystick.Joystick(0)
                self.joystick.init()
                self.connected = True
                try:
                    self.joystick.rumble(0, 0, 100)
                    self.vibration_supported = True
                except:
                    self.vibration_supported = False
            except:
                self.connected = False
    def get_input(self):
        if not self.connected:
            return 0, 0, False
        try:
            pygame.event.pump()  
            gas = 0
            if self.joystick.get_numaxes() >= 6:
                try:
                    right_trigger = (self.joystick.get_axis(5) + 1) / 2  
                    gas = max(0, right_trigger)
                except:
                    pass
            turn = 0
            if self.joystick.get_numaxes() >= 1:
                try:
                    left_stick_x = self.joystick.get_axis(0)
                    if abs(left_stick_x) > 0.1:
                        turn = left_stick_x
                except:
                    pass
            restart = False
            if self.joystick.get_numbuttons() > 0:
                try:
                    restart = self.joystick.get_button(0)
                except:
                    pass
            return gas, turn, restart
        except:
            return 0, 0, False
    def set_vibration(self, left_motor, right_motor):
        if not self.connected or not self.vibration_supported:
            return
        try:
            self.joystick.rumble(left_motor, right_motor, 100)  
        except:
            pass
class Game:
    def __init__(self):
        pygame.init()
        pygame.joystick.init()
        self.screen_width = 1024
        self.screen_height = 768
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Top-Down Racing Game")
        self.clock = pygame.time.Clock()
        self.running = True
        self.player = Player(200, 200)
        self.track = Track(3200, 2400)  
        self.controller = XboxController()
        self.camera_x = 0
        self.camera_y = 0
        self.score = 0
        self.start_time = time.time()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.current_vibration = (0, 0)
        self.last_surface_type = 0
        self.keys_pressed = pygame.key.get_pressed()
    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self.restart_game()
        gas, turn, restart_button = self.controller.get_input()
        if restart_button:
            self.restart_game()
        if not self.controller.connected:
            keys = pygame.key.get_pressed()
            gas = 1.0 if keys[pygame.K_UP] or keys[pygame.K_w] else 0
            turn = 0
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                turn = -1.0
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                turn = 1.0
        return gas, turn
    def update(self):
        gas, turn = self.handle_input()
        surface_type = self.track.get_surface_at(self.player.x, self.player.y)
        surface_info = self.track.surface_types[surface_type]
        if surface_type != self.last_surface_type:
            self.player.bounce()
            self.last_surface_type = surface_type
        self.player.update(gas, turn, surface_info["friction"])
        vibration = surface_info["vibration"]
        if vibration != self.current_vibration:
            self.controller.set_vibration(vibration[0], vibration[1])
            self.current_vibration = vibration
        self.camera_x = self.player.x - self.screen_width // 2
        self.camera_y = self.player.y - self.screen_height // 2
        self.camera_x = max(0, min(self.camera_x, self.track.width - self.screen_width))
        self.camera_y = max(0, min(self.camera_y, self.track.height - self.screen_height))
        distance = math.sqrt(self.player.x**2 + self.player.y**2)
        self.score = int(distance)
    def render(self):
        self.screen.fill((20, 20, 20))
        self.track.draw(self.screen, self.camera_x, self.camera_y, 
                       self.screen_width, self.screen_height)
        self.player.draw(self.screen, self.camera_x, self.camera_y)
        self.draw_ui()
        pygame.display.flip()
    def draw_ui(self):
        legend_y = 10
        legend_texts = [
            ("Черная - обычная", (50, 50, 50)),
            ("Зеленая - легкая вибрация", (0, 150, 0)),
            ("Желтая - средняя вибрация", (200, 200, 0)),
            ("Красная - сильная вибрация", (200, 0, 0))
        ]
        for i, (text, color) in enumerate(legend_texts):
            pygame.draw.rect(self.screen, color, (10, legend_y + i * 25, 15, 15))
            legend_surface = self.small_font.render(text, True, (255, 255, 255))
            self.screen.blit(legend_surface, (30, legend_y + i * 25))
        if self.controller.connected:
            controls_text = [
                "RT - Газ",
                "Левый стик - Поворот",
                "A - Рестарт"
            ]
        else:
            controls_text = [
                "W/↑ - Газ",
                "A/D, ←/→ - Поворот",
                "R - Рестарт"
            ]
        for i, text in enumerate(controls_text):
            control_surface = self.small_font.render(text, True, (200, 200, 200))
            self.screen.blit(control_surface, (10, self.screen_height - 80 + i * 20))
    def restart_game(self):
        self.player = Player(200, 200)
        self.track = Track(3200, 2400)
        self.score = 0
        self.start_time = time.time()
        self.controller.set_vibration(0, 0)
        self.current_vibration = (0, 0)
        self.last_surface_type = 0
    def run(self):
        while self.running:
            self.update()
            self.render()
            self.clock.tick(60)
        self.controller.set_vibration(0, 0)
        pygame.quit()
        sys.exit()
if __name__ == "__main__":
    game = Game()
    game.run()