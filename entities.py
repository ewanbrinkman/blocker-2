from random import choice, randint
from itertools import chain
from pytweening import easeInOutSine
import pygame as pg
from pygame.locals import *
from pygame.math import Vector2 as Vec
from settings import *


def collide_hit_rect_both(one, two):
    return one.hit_rect.colliderect(two.hit_rect)


def screen_wrap(sprite):
    # Edge of screen teleport.
    if sprite.pos.x < 0:
        sprite.pos.x = sprite.game.map.width
    elif sprite.pos.x > sprite.game.map.width:
        sprite.pos.x = 0


class Player(pg.sprite.Sprite):
    def __init__(self, game, x, y, image_string):
        self._layer = PLAYER_LAYER
        # Pygame sprite creation with groups.
        self.groups = [game.all_sprites, game.visible_sprites, game.players]
        pg.sprite.Sprite.__init__(self, self.groups)
        # Save the game object to access data later.
        self.game = game
        # Position.
        self.pos = Vec(x, y)
        self.vel = Vec(0, 0)
        self.acc = Vec(0, 0)
        # Jumping.
        self.on_ground = False
        self.jumping = False
        self.gravity_orientation = 1
        # Sprite image.
        self.image_string = image_string
        self.image = game.player_imgs[image_string]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.hit_rect = pg.Rect(self.rect.x, self.rect.y,
                                PLAYER_HIT_RECT_WIDTH, PLAYER_HIT_RECT_HEIGHT)
        self.hit_rect.center = self.rect.center
        self.color = CYAN

    def update_image(self):
        # Use .copy() to not modify the stored image
        self.image = self.game.player_imgs[self.image_string].copy()
        self.rect = self.image.get_rect()

        # Image details.
        self.rect = self.image.get_rect()
        self.rect.center = (self.pos.x, self.pos.y)
        self.hit_rect.center = self.rect.center

    def jump(self, wall_jump, x_direction=None):
        # Jump up.
        self.jumping = True
        self.vel.y = PLAYER_MOVEMENT["jump"]["jump"] * self.gravity_orientation
        if wall_jump:
            # Also jump away from the wall if it is a wall jump.
            self.vel.x = PLAYER_MOVEMENT["jump"]["wall jump"] * x_direction

    def try_jump(self, trigger):
        # Trigger is the action that triggered the jump being called.
        if trigger == "hold":
            # The jump button was held down.
            if not self.jumping and self.on_ground:
                # Ground jump.
                self.jump(False)
        elif trigger == "push":
            # The jump button was pushed down.
            if not self.on_ground:
                # Test to see if there is a wall to jump off of.
                wall_jump_direction = None

                self.hit_rect.x += 1
                collision = pg.sprite.spritecollide(self, self.game.walls,
                                                    False,
                                                    collide_hit_rect_both)
                self.hit_rect.x -= 1

                if collision:
                    wall_jump_direction = -1
                else:
                    self.hit_rect.x -= 1
                    collision = pg.sprite.spritecollide(self, self.game.walls,
                                                        False,
                                                        collide_hit_rect_both)
                    self.hit_rect.x += 1

                    if collision:
                        wall_jump_direction = 1

                if wall_jump_direction:
                    # Wall jump.
                    self.jump(True, x_direction=wall_jump_direction)

    def apply_keys(self):
        # Get key presses.
        keys = pg.key.get_pressed()

        # Apply key presses.
        if keys[K_a] or keys[K_LEFT]:
            self.acc.x = -PLAYER_MOVEMENT["jump"]["acc"]
        if keys[K_d] or keys[K_RIGHT]:
            self.acc.x = PLAYER_MOVEMENT["jump"]["acc"]
        if keys[K_SPACE]:
            self.try_jump("hold")

    def collide_walls(self):
        self.hit_rect.centerx = self.pos.x
        # Find all sprites in the target group that are bring hit.
        hits = pg.sprite.spritecollide(self, self.game.walls, False,
                                       collide_hit_rect_both)
        if hits:
            if self.vel.x > 0:
                # Moving right, will hit left side.
                hit = min([hit.hit_rect.left for hit in hits])
                self.pos.x = hit - self.hit_rect.width / 2
                self.hit_rect.right = hit
                self.vel.x = 0
            elif self.vel.x < 0:
                # Moving left, will hit right side.
                hit = max([hit.hit_rect.right for hit in hits])
                self.pos.x = hit + self.hit_rect.width / 2
                self.hit_rect.left = hit
                self.vel.x = 0
            if not self.on_ground:
                # Only slide on walls when in the air, and going down
                # towards where gravity is pulling. That way, you don't
                # slide on walls when jumping up.
                if self.vel.y > 0 and self.gravity_orientation == 1 or \
                        self.vel.y < 0 and self.gravity_orientation == -1:
                    # Wall slide.
                    self.vel.y *= PLAYER_MOVEMENT["jump"]["wall slide"]

        self.hit_rect.centery = self.pos.y
        # Find all sprites in the target group that are bring hit.
        hits = pg.sprite.spritecollide(self, self.game.walls, False,
                                       collide_hit_rect_both)
        if hits:
            if self.vel.y > 0:
                # Moving down, will hit top.
                hit = min([hit.hit_rect.top for hit in hits])
                self.pos.y = hit - self.hit_rect.width / 2
                self.hit_rect.bottom = hit
                # self.vel.y = 0
                if self.gravity_orientation == 1:
                    # Hit the ground again if the gravity is normal.
                    self.on_ground = True
                    self.jumping = False
            elif self.vel.y < 0:
                # Moving up, will hit bottom.
                hit = max([hit.hit_rect.bottom for hit in hits])
                self.pos.y = hit + self.hit_rect.width / 2
                self.hit_rect.top = hit
                # self.vel.y = 0
                if self.gravity_orientation == -1:
                    # Hit the ground again if the gravity is reversed (you
                    # fall up instead of down).
                    self.on_ground = True
                    self.jumping = False

            # Reset y velocity.
            self.vel.y = 0

            for hit in hits:
                if isinstance(hit, MovingObstacle):
                    # Only follow along if the moving obstacle is going down.
                    if hit.vel.y > 0 and self.gravity_orientation == 1 or \
                            hit.vel.y < 0 and self.gravity_orientation == -1:
                        self.pos.x += hit.vel.x * self.game.dt
        else:
            # Test to see if a platform is nearby. Make the player move
            # along with the moving obstacle if they are close enough to the
            # moving obstacle.
            if self.gravity_orientation == 1:
                self.hit_rect.y += 2
                hits = pg.sprite.spritecollide(self, self.game.moving_walls, False,
                                               collide_hit_rect_both)
                self.hit_rect.y -= 2
            elif self.gravity_orientation == -1:
                self.hit_rect.y -= 2
                hits = pg.sprite.spritecollide(self, self.game.moving_walls,
                                               False,
                                               collide_hit_rect_both)
                self.hit_rect.y += 2
            if hits:
                # Near a platform.
                self.on_ground = True
                # Make the player move along with the moving obstacle.
                self.pos.x += hits[0].vel.x * self.game.dt

                # Update player rect.
                self.hit_rect.x = self.pos.x
                self.rect = self.hit_rect
            else:
                # Not near a platform.
                self.on_ground = False

        self.rect.center = self.hit_rect.center

    def move(self):
        # Reset acceleration.
        self.acc = Vec(0, 0)

        # Apply gravity.
        self.acc = Vec(0, PLAYER_MOVEMENT["jump"]["gravity"] * self.gravity_orientation)

        # Get key presses for movement.
        self.apply_keys()

        # Forward/backwards movement.
        # Apply friction.
        self.acc += self.vel * PLAYER_MOVEMENT["jump"]["friction"]
        # New velocity after.
        # vf = vi + at
        self.vel = self.vel + self.acc * self.game.dt
        # Displacement.
        # d = vit + 1/2at^2
        displacement = self.vel * self.game.dt + 0.5 * self.acc * self.game.dt ** 2

        self.pos += displacement

        # Wrap around the screen.
        # screen_wrap(self)

        self.collide_walls()

    def update(self):
        # Move the player sprite based on the current movement mode type.
        self.move()

        # Update the sprite image with the correct positioning.
        self.update_image()


class Obstacle(pg.sprite.Sprite):
    def __init__(self, game, x, y, width, height, obstacle_type,
                 groups: list = None):
        # Base groups.
        self.groups = [game.all_sprites]
        # Add any extra groups.
        if groups:
            for group in groups:
                self.groups.append(group)
        # Add obstacle type group.
        if obstacle_type == "wall":
            self.groups.append(game.walls)
            self.color = GREEN
        elif obstacle_type == "moving_wall":
            self.groups.append(game.moving_walls)
            self.color = GREEN

        # Create sprite.
        pg.sprite.Sprite.__init__(self, self.groups)
        # Other data.
        self.rect = pg.Rect(x, y, width, height)
        self.hit_rect = self.rect
        self.obstacle_type = obstacle_type


class MovingObstacle(Obstacle):
    def __init__(self, game, x, y, width, height, obstacle_type, movement):
        # Base groups. The specific obstacle type group will be added in the
        # parent class.
        groups = [game.visible_sprites, game.walls]
        # The image size will be the width and the height.
        self.image = game.wall_imgs["bridge.png"]
        self.image = pg.transform.scale(self.image, (int(width), int(height)))
        # self.image = pg.Surface((width, height))
        image_rect = self.image.get_rect()
        super().__init__(game, x, y, image_rect.width, image_rect.height,
                         obstacle_type, groups)

        # Movement.
        self.pos = Vec(x, y)
        self.movement = movement
        self.parts = [n for n in self.movement['parts']]
        self.one_way_length = len(self.parts)
        self.part = 1
        self.step = 0
        # If the moving obstacle goes goes back, then copy create a copy of
        # movement and add it to movement, except reversed.
        if self.movement['back']:
            back_part = self.parts.copy()
            back_part.reverse()
            self.parts += back_part

        rot = self.movement['parts'][self.parts[self.part - 1]]['rot']
        self.vel = Vec(
            self.movement['parts'][self.parts[self.part - 1]]['vel'],
            0).rotate(-rot)
        # Other data.
        self.game = game

    def move(self):
        # Update position.
        self.pos += self.vel * self.game.dt

        # Add another step to the counter.
        self.step += 1

        # If the moving obstacle moved onto the player, push the player out
        # of the way.
        self.collide_player()

        # Update current part of movement.
        if self.step == self.movement['parts'][self.parts[self.part - 1]]['steps']:
            # If all steps are done for the section, go to the next section.
            if self.part + 1 <= len(self.parts):
                # Go to the next part if.
                self.part += 1
            else:
                # The final part just finished, so go back to the start.
                self.part = 1
            self.step = 0
            rot = self.movement['parts'][self.parts[self.part - 1]]['rot']
            self.vel = Vec(
                self.movement['parts'][self.parts[self.part - 1]]['vel'],
                0).rotate(-rot)
            # Make the vel the opposite if it is on the way back.
            if self.part > self.one_way_length:
                self.vel *= -1

        # Wrap around the screen.
        # screen_wrap(self)

    def collide_player(self):
        self.hit_rect.x = self.pos.x
        # Test if a player was hit.
        collision = pg.sprite.spritecollide(self, self.game.players, False,
                                            collide_hit_rect_both)

        if collision:
            player = collision[0]

            # Push the player to the correct side of the platform and change
            # the player's velocity.
            if self.vel.x > 0:
                # Moving right, place player on right side.
                player.pos.x = self.hit_rect.right + player.hit_rect.width / 2
                player.hit_rect.left = self.hit_rect.right
                # player.vel.x = 0
                # player.pos.x += self.vel.x * self.game.dt
            elif self.vel.x < 0:
                # Moving left, place player on left side.
                player.pos.x = self.hit_rect.left - player.hit_rect.width / 2
                player.hit_rect.right = self.hit_rect.left
                # player.vel.x = 0
                # player.pos.x += self.vel.x * self.game.dt

            # Update player rect.
            player.rect = player.hit_rect

        self.hit_rect.y = self.pos.y
        # Test if a player was hit.
        collision = pg.sprite.spritecollide(self, self.game.players, False,
                                            collide_hit_rect_both)
        if collision:
            player = collision[0]

            # Push the player to the correct side of the platform and change
            # the player's velocity.
            if self.vel.y > 0:
                # Moving down, place player on the bottom.
                player.pos.y = self.hit_rect.bottom + player.hit_rect.height / 2
                player.hit_rect.top = self.hit_rect.bottom
                # player.vel.y = 0
                # player.pos.y += self.vel.y * self.game.dt
            elif self.vel.y < 0:
                # Moving up, place player on the top.
                player.pos.y = self.hit_rect.top - player.hit_rect.height / 2
                player.hit_rect.bottom = self.hit_rect.top
                # player.vel.y = 0
                # player.pos.y += self.vel.y * self.game.dt

            # Make the player move along with the moving obstacle.
            player.pos.x += self.vel.x * self.game.dt

            # Update player rect.
            player.rect = player.hit_rect

        # Update self rect position.
        self.rect.topleft = self.hit_rect.topleft

    def update(self):
        # Move the obstacle around.
        self.move()
