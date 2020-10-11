import pygame as pg
import pytmx
from settings import *


class Camera:
    def __init__(self, screen_width, screen_height, map_width, map_height):
        self.rect = pg.Rect(0, 0, map_width, map_height)
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.width = map_width
        self.height = map_height
        self.x = None
        self.y = None

    def apply_sprite(self, sprite):
        return sprite.rect.move(self.rect.topleft)

    def apply_rect(self, rect):
        return rect.move(self.rect.topleft)

    def update(self, target):
        # Make the target on the center of the screen
        self.x = -target.rect.centerx + self.screen_width / 2
        self.y = -target.rect.centery + self.screen_height / 2

        # Limit scrolling to map size.
        self.x = min(0, self.x)  # left
        self.y = min(0, self.y)  # top
        self.x = max(-(self.width - self.screen_width), self.x)  # right
        self.y = max(-(self.height - self.screen_height), self.y)  # left

        # Center the map if it is smaller then the screen size.
        if self.width < self.screen_width:
            self.x = self.screen_width / 2 - self.width / 2
        if self.height < self.screen_height:
            self.y = self.screen_height / 2 - self.height / 2

        self.x, self.y = int(self.x), int(self.y)

        self.rect = pg.Rect(self.x, self.y, self.width, self.height)


class TiledMap:
    def __init__(self, filename):
        tilemap_data = pytmx.load_pygame(filename, pixelalpha=True)
        self.width = tilemap_data.width * tilemap_data.tilewidth
        self.height = tilemap_data.height * tilemap_data.tileheight
        self.image = pg.Surface((self.width, self.height), pg.SRCALPHA)
        self.rect = self.image.get_rect()
        self.tilemap_data = tilemap_data

    def render(self, surface):
        tile_image = self.tilemap_data.get_tile_image_by_gid
        for layer in self.tilemap_data.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                for x, y, gid in layer:
                    tile = tile_image(gid)
                    if tile:
                        surface.blit(tile, (x * self.tilemap_data.tilewidth,
                                            y * self.tilemap_data.tileheight))

    def make_map(self):
        self.render(self.image)
