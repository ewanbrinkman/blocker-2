import os
import pygame as pg
from pygame.locals import *
from settings import *
from tilemap import Camera, TiledMap
from entities import *


class Game:
    def __init__(self):
        # Initialize pygame.
        pg.mixer.pre_init(44100, -16, 1, 2048)
        pg.init()
        pg.mixer.init()

        # Display
        pg.display.set_caption(TITLE)
        self.screen = pg.display.set_mode(
            (SCREEN_WIDTH, SCREEN_HEIGHT), FULLSCREEN)
        self.show_fps = False
        self.debug = False

        # Sprites groups.
        self.all_sprites = pg.sprite.Group()
        self.players = pg.sprite.Group()
        self.visible_sprites = pg.sprite.Group()
        self.walls = pg.sprite.Group()
        self.moving_walls = pg.sprite.Group()

        # Game loop.
        self.clock = pg.time.Clock()
        self.running = True
        self.playing = True

        self.player_pos = []

        self.camera_update = True

        # Load data from files.
        self.load()

    def load(self):
        # Folders.
        game_folder = os.path.dirname(__file__)
        font_folder = os.path.join(game_folder, "fnt")
        img_folder = os.path.join(game_folder, "img")
        snd_folder = os.path.join(game_folder, "snd")
        self.map_folder = os.path.join(game_folder, "map")

        # App icon.
        self.icon = pg.image.load(os.path.join(img_folder, GAME_IMG))
        pg.display.set_icon(self.icon)

        # Sprite images.
        self.player_imgs = {}
        for filename in PLAYER_IMGS:
            new_img = pg.image.load(
                os.path.join(img_folder, filename)).convert_alpha()
            # Rotate so the sprite moves in the direction it is pointing.
            self.player_imgs[filename] = new_img
            # self.player_imgs[filename] = pg.transform.rotate(new_img, 90)

        # Other images.
        self.wall_imgs = {}
        for filename in WALL_IMGS:
            new_img = pg.image.load(
                os.path.join(img_folder, filename)).convert_alpha()
            self.wall_imgs[filename] = new_img

        # Music.
        self.game_music = os.path.join(snd_folder, GAME_BG_MUSIC)

        # Text font.
        self.theme_font = os.path.join(font_folder, THEME_FONT)

    def create_map(self, filename):
        # Basic map background image with data.
        self.map = TiledMap(os.path.join(self.map_folder, filename))
        self.map.make_map()

        # Create the camera with the map dimensions.
        self.camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT,
                             self.map.width, self.map.height)

        movement = {
            "back": True,
            "parts": {
                1: {
                    "vel": 300,
                    "rot": 90,
                    "steps": 80
                },
                # 2: {
                #     "vel": 10,
                #     "rot": 0,
                #     "steps": 100
                # }
            }
            }

        # Map objects.
        for tile_object in self.map.tilemap_data.objects:
            # The center of the tile.
            object_center = Vec(tile_object.x + tile_object.width / 2, tile_object.y + tile_object.height / 2)
            # Obstacles.
            if tile_object.object == "obstacle":
                Obstacle(self, tile_object.x, tile_object.y,
                         tile_object.width, tile_object.height,
                         tile_object.type)
            elif tile_object.object == "moving_obstacle":
                MovingObstacle(self, tile_object.x, tile_object.y,
                               tile_object.width, tile_object.height,
                               tile_object.type, movement)

    def new(self):
        # Create the map.
        self.create_map("map1.tmx")

        # Create the player object.
        self.player = Player(self, 100, 1800, "playerimg.png")

        # Start playing the background music.
        pg.mixer.music.load(self.game_music)
        pg.mixer.music.set_volume(0.1)
        pg.mixer.music.play(loops=-1)

        # Start running the game..
        self.run()

    def run(self):
        # Game loop.
        self.playing = True
        while self.playing:
            # Pause.
            self.dt = self.clock.tick(FPS) / 1000.0
            self.events()
            self.update()
            self.draw()

    def events(self):
        # Game events loop.
        for event in pg.event.get():
            # Check for closing window.
            if event.type == QUIT or event.type == KEYDOWN and event.key == \
                    K_ESCAPE:
                self.playing = False
                self.running = False
            if event.type == KEYDOWN:
                if event.key == K_b:
                    # Toggle debug mode.
                    self.debug = not self.debug
                if event.key == K_f:
                    self.show_fps = not self.show_fps
                if event.key == K_SPACE:
                    self.player.try_jump("push")
                if event.key == K_g:
                    # Change the player gravity up/down.
                    self.player.gravity_orientation *= -1
                if event.key == K_c:
                    # Change the player gravity up/down.
                    self.camera_update = not self.camera_update

    def update(self):
        # Game update loop.
        self.moving_walls.update()
        self.players.update()
        # Make the camera center on the player sprite.
        if self.camera_update:
            self.camera.update(self.player)
        # Update title with information.
        title = TITLE + f" FPS: {round(self.clock.get_fps(), 2)}"
        pg.display.set_caption(title)

    def draw_grid(self):
        # A grid of lines to represent the tiles of the map. The grid will
        # move along with the player/camera.
        for x in range(self.camera.x, SCREEN_WIDTH, TILESIZE):
            pg.draw.line(self.screen, LIGHTGRAY, (x, 0), (x, SCREEN_HEIGHT))
        for y in range(self.camera.y, SCREEN_HEIGHT, TILESIZE):
            pg.draw.line(self.screen, LIGHTGRAY, (0, y), (SCREEN_WIDTH, y))

    def draw_boundary(self, sprite, sprite_color):
        # Image boundary.
        pg.draw.rect(self.screen, sprite_color, self.camera.apply_sprite(sprite), 1)
        # Hit box.
        pg.draw.rect(self.screen, sprite_color, self.camera.apply_rect(sprite.hit_rect), 1)
        surface = pg.Surface((sprite.hit_rect.width, sprite.hit_rect.height))
        surface.set_alpha(128)
        surface.fill(sprite_color)
        self.screen.blit(surface, self.camera.apply_rect(sprite.hit_rect))

    def draw_debug(self):
        # Grid of tiles.
        self.draw_grid()

        # Draw wall boundaries.
        for sprite in self.all_sprites:
            self.draw_boundary(sprite, sprite.color)

    def draw(self):
        # Game draw loop.
        self.screen.fill(BGCOLOR)
        # Map image.
        self.screen.blit(self.map.image, self.camera.apply_rect(self.map.rect))
        # Draw all sprites.
        for sprite in self.visible_sprites:
            self.screen.blit(sprite.image, self.camera.apply_sprite(sprite))

        if self.show_fps:
            # Draw FPS
            self.draw_text(f"FPS: {round(self.clock.get_fps(), 2)}",
                           OVERLAY_SIZE,
                           TEXT_COLOR, SCREEN_WIDTH / 2, 0, align="n",
                           font_name=self.theme_font)
        if self.debug:
            # Draw debug.
            self.draw_debug()

        # # Cool effect.
        # self.player_pos.append(Vec(self.player.pos.x, self.player.pos.y))
        # if len(self.player_pos) > 100:
        #     del self.player_pos[0]
        # width, height = self.player.hit_rect.width, self.player.hit_rect.height
        # for pos in self.player_pos:
        #     surface = pg.Surface(
        #         (width, height))
        #     surface.set_alpha(50)
        #     surface.fill(self.player.color)
        #     self.screen.blit(surface,
        #                      self.camera.apply_rect(pg.Rect(pos.x - width / 2,
        #                                                     pos.y - height / 2,
        #                                                     width, height)))
        # Make sure it doesn't cover the player, so draw the player on top.
        # for sprite in self.players:
        #     self.screen.blit(sprite.image, self.camera.apply_sprite(sprite))

        # Flip the display (update the display).
        pg.display.flip()

    def draw_text(self, text, size, fillcolor, x, y, align="n", font_name=None):
        # Create the font.
        font = pg.font.Font(font_name, size)
        # Create a surface to put the text on.
        text_surface = font.render(text, True, fillcolor)
        text_rect = text_surface.get_rect()
        # Align the text.
        if align == "nw":
            text_rect.topleft = (x, y)
        elif align == "ne":
            text_rect.topright = (x, y)
        elif align == "sw":
            text_rect.bottomleft = (x, y)
        elif align == "se":
            text_rect.bottomright = (x, y)
        elif align == "n":
            text_rect.midtop = (x, y)
        elif align == "s":
            text_rect.midbottom = (x, y)
        elif align == "e":
            text_rect.midright = (x, y)
        elif align == "w":
            text_rect.midleft = (x, y)
        elif align == "center":
            text_rect.center = (x, y)
        self.screen.blit(text_surface, text_rect)

        # Return the dimensions of the text rect in case it is needed for
        # positioning multiple text rects so that they fit together nicely.

        return text_rect

    def show_start_screen(self):
        # Game start screen.
        pass

    def show_game_over_screen(self):
        # Game over screen.
        pass


g = Game()
g.show_start_screen()
while g.running:
    g.new()

pg.quit()
