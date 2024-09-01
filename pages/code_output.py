import streamlit as st
import random
import time

# Game constants
WIDTH = 20
HEIGHT = 20
CELL_SIZE = 20
SPEED = 0.2

# Initialize game state
if 'snake' not in st.session_state:
    st.session_state.snake = [(WIDTH // 2, HEIGHT // 2)]
if 'food' not in st.session_state:
    st.session_state.food = (random.randint(0, WIDTH - 1), random.randint(0, HEIGHT - 1))
if 'direction' not in st.session_state:
    st.session_state.direction = 'RIGHT'
if 'game_over' not in st.session_state:
    st.session_state.game_over = False
if 'score' not in st.session_state:
    st.session_state.score = 0

# Set up the game board
st.set_page_config(page_title="Snake Game", layout="wide")
st.title("Snake Game")

# Create a placeholder for the game board
game_board = st.empty()

# Game logic
def move_snake():
    head = st.session_state.snake[0]
    if st.session_state.direction == 'UP':
        new_head = (head[0], (head[1] - 1) % HEIGHT)
    elif st.session_state.direction == 'DOWN':
        new_head = (head[0], (head[1] + 1) % HEIGHT)
    elif st.session_state.direction == 'LEFT':
        new_head = ((head[0] - 1) % WIDTH, head[1])
    else:  # RIGHT
        new_head = ((head[0] + 1) % WIDTH, head[1])
    
    # Check if snake hits itself
    if new_head in st.session_state.snake:
        st.session_state.game_over = True
    else:
        st.session_state.snake.insert(0, new_head)
        
        # Check if snake eats food
        if new_head == st.session_state.food:
            st.session_state.score += 1
            st.session_state.food = (random.randint(0, WIDTH - 1), random.randint(0, HEIGHT - 1))
        else:
            st.session_state.snake.pop()

# Main game loop
if not st.session_state.game_over:
    move_snake()
    
    # Draw game board
    board = [['⬛' for _ in range(WIDTH)] for _ in range(HEIGHT)]
    for segment in st.session_state.snake:
        board[segment[1]][segment[0]] = '🟩'
    board[st.session_state.food[1]][st.session_state.food[0]] = '🍎'
    
    game_board.text('\n'.join([''.join(row) for row in board]))
    st.text(f"Score: {st.session_state.score}")
    
    # Create buttons for controls in a more compact layout
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        if st.button("↑"):
            if st.session_state.direction != 'DOWN':
                st.session_state.direction = 'UP'
        col_left, col_right = st.columns(2)
        with col_left:
            if st.button("←"):
                if st.session_state.direction != 'RIGHT':
                    st.session_state.direction = 'LEFT'
        with col_right:
            if st.button("→"):
                if st.session_state.direction != 'LEFT':
                    st.session_state.direction = 'RIGHT'
        if st.button("↓"):
            if st.session_state.direction != 'UP':
                st.session_state.direction = 'DOWN'
    
    time.sleep(SPEED)
    st.rerun()
else:
    st.text("Game Over!")
    if st.button("Restart"):
        st.session_state.snake = [(WIDTH // 2, HEIGHT // 2)]
        st.session_state.food = (random.randint(0, WIDTH - 1), random.randint(0, HEIGHT - 1))
        st.session_state.direction = 'RIGHT'
        st.session_state.game_over = False
        st.session_state.score = 0
        st.rerun()