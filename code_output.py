import streamlit as st
import pygame
import random

# Initialize Pygame
pygame.init()

# Constants
WIDTH = 400
HEIGHT = 400
GRID_SIZE = 20
GRID_WIDTH = WIDTH // GRID_SIZE
GRID_HEIGHT = HEIGHT // GRID_SIZE

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)

# Snake class
class Snake:
    def __init__(self):
        self.body = [(GRID_WIDTH // 2, GRID_HEIGHT // 2)]
        self.direction = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])

    def move(self):
        head = self.body[0]
        new_head = ((head[0] + self.direction[0]) % GRID_WIDTH, 
                    (head[1] + self.direction[1]) % GRID_HEIGHT)
        self.body.insert(0, new_head)

    def grow(self):
        self.body.append(self.body[-1])

    def check_collision(self):
        return len(self.body) != len(set(self.body))

# Food class
class Food:
    def __init__(self):
        self.position = self.random_position()

    def random_position(self):
        return (random.randint(0, GRID_WIDTH - 1), 
                random.randint(0, GRID_HEIGHT - 1))

# Game state
snake = Snake()
food = Food()
score = 0
game_over = False

# Streamlit app
st.title("Snake Game")

# Create a Pygame surface
surface = pygame.Surface((WIDTH, HEIGHT))

# Game loop
def game_loop():
    global snake, food, score, game_over

    if not game_over:
        # Move snake
        snake.move()

        # Check for food collision
        if snake.body[0] == food.position:
            snake.grow()
            food = Food()
            score += 1

        # Check for self-collision
        if snake.check_collision():
            game_over = True

        # Draw everything
        surface.fill(BLACK)
        for segment in snake.body:
            pygame.draw.rect(surface, GREEN, (segment[0] * GRID_SIZE, segment[1] * GRID_SIZE, GRID_SIZE, GRID_SIZE))
        pygame.draw.rect(surface, RED, (food.position[0] * GRID_SIZE, food.position[1] * GRID_SIZE, GRID_SIZE, GRID_SIZE))

    # Convert Pygame surface to an image
    return pygame.surfarray.array3d(surface).swapaxes(0, 1)

# Streamlit elements
col1, col2 = st.columns(2)

with col1:
    st.write(f"Score: {score}")
    if game_over:
        st.write("Game Over!")
        if st.button("Restart"):
            snake = Snake()
            food = Food()
            score = 0
            game_over = False

with col2:
    # Controls
    if not game_over:
        if st.button("↑"):
            snake.direction = (0, -1)
        if st.button("↓"):
            snake.direction = (0, 1)
        if st.button("←"):
            snake.direction = (-1, 0)
        if st.button("→"):
            snake.direction = (1, 0)

# Main game display
game_display = st.empty()

# Game loop
while True:
    frame = game_loop()
    game_display.image(frame, use_column_width=True)
    st.rerun()