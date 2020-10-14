# Colors.
WHITE = (255, 255, 255)
LIGHTGRAY = (100, 100, 100)
DARKGRAY =(40, 40, 40)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
SKY = (135, 206, 250)

# Game settings.
SCREEN_WIDTH = 1440
SCREEN_HEIGHT = 900
FPS = 60
TITLE = "Game"
BGCOLOR = SKY

# Display settings.
TILESIZE = 70
GRID_WIDTH = SCREEN_WIDTH / TILESIZE
GRID_HEIGHT = SCREEN_HEIGHT / TILESIZE
OVERLAY_SIZE = 40
TEXT_COLOR = WHITE
THEME_FONT = "Booter.ttf"

# Player settings.
PLAYER_LAYER = 1
# Player size.
PLAYER_HIT_RECT_WIDTH = 35
PLAYER_HIT_RECT_HEIGHT = 35
# Player movement settings.
PLAYER_MOVEMENT = {
    "jump": {
        "friction": -1.5,
        "acc": 600,
        "jump": -1000,
        "gravity": 1500,
        "wall jump": 400,
        "wall slide": 0.6
    },
    "spin": {
        "friction": -2,
        "acc": 450,
        "rot acc": 350,
    }
}

# Data to load.
GAME_IMG = "playerimg.png"
GAME_BG_MUSIC = "grasslands.mp3"
PLAYER_IMGS = ["playerimg.png"]
WALL_IMGS = ["bridge.png", "sky.png"]
