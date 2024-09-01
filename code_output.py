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

# Function to move the snake
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
        if new_head == st.session_state.food:
            st.session_state.score += 1
            st.session_state.food = (random.randint(0, WIDTH - 1), random.randint(0, HEIGHT - 1))
        else:
            st.session_state.snake.pop()

# Streamlit app
st.title("Snake Game")

# Game controls
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("↑"):
        st.session_state.direction = 'UP'
with col2:
    if st.button("↓"):
        st.session_state.direction = 'DOWN'
with col1:
    if st.button("←"):
        st.session_state.direction = 'LEFT'
with col3:
    if st.button("→"):
        st.session_state.direction = 'RIGHT'

# Reset button
if st.button("Reset Game"):
    st.session_state.snake = [(WIDTH // 2, HEIGHT // 2)]
    st.session_state.food = (random.randint(0, WIDTH - 1), random.randint(0, HEIGHT - 1))
    st.session_state.direction = 'RIGHT'
    st.session_state.game_over = False
    st.session_state.score = 0

# Display score
st.write(f"Score: {st.session_state.score}")

# Game loop
if not st.session_state.game_over:
    move_snake()
    
    # Create game board
    board = [['⬜' for _ in range(WIDTH)] for _ in range(HEIGHT)]
    for segment in st.session_state.snake:
        board[segment[1]][segment[0]] = '🟩'
    board[st.session_state.food[1]][st.session_state.food[0]] = '🍎'
    
    # Display game board
    st.text('\n'.join([''.join(row) for row in board]))
    
    time.sleep(SPEED)
    st.experimental_rerun()
else:
    st.write("Game Over!")

# CSS to make the game board more compact
st.markdown("""
<style>
    .stTextInput > div > div > input {
        font-family: monospace;
    }
</style>
""", unsafe_allow_html=True)
