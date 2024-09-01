import streamlit as st
import pygame
import random
import numpy as np
from PIL import Image

pygame.init()

WIDTH = 400
HEIGHT = 400
GRID_SIZE = 20
GRID_WIDTH = WIDTH // GRID_SIZE
GRID_HEIGHT = HEIGHT // GRID_SIZE

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)

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

class Food:
    def __init__(self):
        self.position = self.random_position()

    def random_position(self):
        return (random.randint(0, GRID_WIDTH - 1), 
                random.randint(0, GRID_HEIGHT - 1))

@st.cache_resource
def init_game():
    return Snake(), Food(), 0, False

snake, food, score, game_over = init_game()

st.title("Snake Game")

surface = pygame.Surface((WIDTH, HEIGHT))

def game_loop():
    global snake, food, score, game_over

    if not game_over:
        snake.move()

        if snake.body[0] == food.position:
            snake.grow()
            food = Food()
            score += 1

        if snake.check_collision():
            game_over = True

        surface.fill(BLACK)
        for segment in snake.body:
            pygame.draw.rect(surface, GREEN, (segment[0] * GRID_SIZE, segment[1] * GRID_SIZE, GRID_SIZE, GRID_SIZE))
        pygame.draw.rect(surface, RED, (food.position[0] * GRID_SIZE, food.position[1] * GRID_SIZE, GRID_SIZE, GRID_SIZE))

    frame = pygame.surfarray.array3d(surface).swapaxes(0, 1)
    return Image.fromarray(frame)

col1, col2 = st.columns(2)

with col1:
    st.write(f"Score: {score}")
    if game_over:
        st.write("Game Over!")
        if st.button("Restart"):
            snake, food, score, game_over = init_game()

with col2:
    if not game_over:
        direction = st.radio("Direction", ["↑", "↓", "←", "→"], horizontal=True)
        if direction == "↑":
            snake.direction = (0, -1)
        elif direction == "↓":
            snake.direction = (0, 1)
        elif direction == "←":
            snake.direction = (-1, 0)
        elif direction == "→":
            snake.direction = (1, 0)

game_display = st.empty()

if not game_over:
    frame = game_loop()
    game_display.image(frame, use_column_width=True)

st.button("Next Frame")