from random import choice, randint
from itertools import chain
from pytweening import easeInOutSine
import pygame as pg
from pygame.locals import *
from pygame.math import Vector2 as Vec
from settings import *


def collide_hit_rect_both(one, two):
    return one.hit_rect.colliderect(two.hit_rect)


def collide_group(sprite, group, direction):
    if direction == "x":
        # Find all sprites in the target group that are bring hit.
        hits = pg.sprite.spritecollide(sprite, group, False, collide_hit_rect_both)
        if hits:
            return hits

    elif direction == "y":
        # Find all sprites in the target group that are bring hit.
        hits = pg.sprite.spritecollide(sprite, group, False, collide_hit_rect_both)
        if hits:
            return hits


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
        self.groups = [game.all_sprites, game.visible_sprites]
        pg.sprite.Sprite.__init__(self, self.groups)
        # Save the game object to access data later.
        self.game = game
        # Position.
        self.pos = Vec(x, y)
        self.vel = Vec(0, 0)
        self.acc = Vec(0, 0)
        # Jumping.
        self.jumping = False
        self.on_ground = False
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

    def collisions(self, group, directions):
        # All the hit data,
        hits = {direction: None for direction in directions}

        for direction in directions:
            if direction == "up":
                self.hit_rect.centery += 1
                hits['up'] = [data for data in collide_group(self, group, "y")]
                self.hit_rect.centery -= 1
            elif direction == "down":
                self.hit_rect.centery -= 1
                hits['down'] = [data for data in collide_group(self, group,
                                                               "y")]
                self.hit_rect.centery += 1
            elif direction == "right":
                self.hit_rect.centerx += 1
                hits['right'] = [data for data in collide_group(self, group,
                                                                "x")]
                self.hit_rect.centerx -= 1
            elif direction == "left":
                self.hit_rect.centerx -= 1
                hits['left'] = [data for data in collide_group(self, group,
                                                               "x")]
                self.hit_rect.centerx += 1

        return hits

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
                collision = collide_group(self, self.game.walls, "x")
                self.hit_rect.x -= 1

                if collision:
                    wall_jump_direction = -1
                else:
                    self.hit_rect.x -= 1
                    collision = collide_group(self, self.game.walls, "x")
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

        self.hit_rect.centery = self.pos.y
        # Find all sprites in the target group that are bring hit.
        hits = pg.sprite.spritecollide(self, self.game.walls, False,
                                       collide_hit_rect_both)
        if hits:
            if self.vel.y > 0:
                hit = min([hit.hit_rect.top for hit in hits])
                self.pos.y = hit - self.hit_rect.width / 2
                self.hit_rect.bottom = hit
                self.vel.y = 0
                self.jumping = False
                self.on_ground = True
            elif self.vel.y < 0:
                hit = max([hit.hit_rect.bottom for hit in hits])
                self.pos.y = hit + self.hit_rect.width / 2
                self.hit_rect.top = hit
                self.vel.y = 0
        else:
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

        # Wall collision detection x.
        # self.hit_rect.centerx = self.pos.x
        # hit_obj, hit_x, side = collide_group(self, self.game.walls, "x")
        # if hit_x:
        #     # There is a collision. hit_x is where the player's x and y
        #     # should be to line up against what it collided against.
        #     self.pos.x = hit_x
        #     self.hit_rect.centerx = self.pos.x
        #     if self.move_type == "jump":
        #         # Stop against the wall.
        #         self.vel.x = 0
        #         # Slide down a wall slowly if not on the ground and going down
        #         # beside a wall.
        #         if self.gravity_orientation == 1 and not self.on_ground \
        #                 and self.vel.y > 0:
        #             self.vel.y *= PLAYER_MOVEMENT["jump"]["wall slide"]
        #         elif self.gravity_orientation == -1 and not self.on_ground \
        #                 and self.vel.y < 0:
        #             self.vel.y *= PLAYER_MOVEMENT["jump"]["wall slide"]
        #     elif self.move_type == "spin":
        #         # Bounce off the wall.
        #         self.vel.x *= -1

        # Wall collision detection y.
        # collide_group(self, self.game.walls, "y")
        # hit_obj, hit_y, side = collide_group(self, self.game.walls, "y")
        # if hit_y:
        #     # There is a collision. hit_x is where the player's x and y
        #     # should be to line up against what it collided against.
        #     self.pos.y = hit_y
        #     self.hit_rect.centery = self.pos.y
        #     print("rect after:", self.hit_rect.centery)
        #     if self.move_type == "jump":
        #         # Stop against the wall.
        #         self.vel.y = 0
        #         if side == "top" and self.gravity_orientation == 1 or \
        #                 side == "bottom" and self.gravity_orientation == -1:
        #             # The player can jump again if they landed on a floor.
        #             self.on_ground = True
        #             self.jumping = False
        #             # If they are on a moving platform, add the platform's
        #             # velocity to their velocity. That way, they will stay
        #             # on the platform when it moves.
        #     elif self.move_type == "spin":
        #         # Bounce off the wall.
        #         self.vel.y *= -hit_obj.bounce
        # else:
        #     self.on_ground = False

        # Match the sprite's rect with where it should be, based on the hit
        # rect.

    def update(self):
        # Move the player sprite based on the current movement mode type.
        self.move()

        # Update the sprite image with the correct positioning.
        self.update_image()


class Obstacle(pg.sprite.Sprite):
    def __init__(self, game, x, y, width, height, obstacle_type,
                 bounce=1, groups=None):
        self.groups = [game.all_sprites, game.obstacles]
        # Add any extra groups.
        if groups:
            for group in groups:
                self.groups.append(group)
        if obstacle_type == "wall":
            self.groups.append(game.walls)
            self.color = GREEN
        if obstacle_type == "moving_wall":
            self.groups.append(game.moving_walls)
            self.color = GREEN
        pg.sprite.Sprite.__init__(self, self.groups)
        self.rect = pg.Rect(x, y, width, height)
        self.hit_rect = self.rect
        self.obstacle_type = obstacle_type
        # Bounce is the how much of the velocity should be conserved when
        # bouncing off the wall. It is a multiplier, so 0 is none, 1 is all,
        # and 2 would be twice the velocity, and so on.
        self.bounce = bounce


class MovingObstacle(Obstacle):
    def __init__(self, game, x, y, width, height, obstacle_type, movement,
                 bounce=1, id=0):
        self.id = id
        self.game = game
        groups = [game.visible_sprites, game.moving_obstacles]
        # The image size will be the width and the height.
        # self.image = game.wall_imgs["sky.png"]
        self.image = pg.Surface((width, height))
        image_rect = self.image.get_rect()
        super().__init__(game, x, y, image_rect.width, image_rect.height,
                         obstacle_type, bounce, groups)

        # Movement.
        self.pos = Vec(x, y)
        self.movement = movement
        self.part = 1
        self.step = 0
        rot = self.movement['parts'][self.part]['rot']
        self.vel = Vec(self.movement['parts'][self.part]['vel'], 0).rotate(-rot)

    def update(self):
        # Update position.
        rot = self.movement['parts'][self.part]['rot']
        vel = Vec(self.movement['parts'][self.part]['vel'], 0).rotate(-rot)
        self.pos += vel * self.game.dt

        # Add another step to the counter.
        self.step += 1
        if self.step == self.movement['parts'][self.part]['steps']:
            # If all steps are done for the section, go to the next section.
            if self.part + 1 in self.movement['parts']:
                # Go to the next part.
                self.part += 1
            else:
                # The final part just finished, so go back to the start.
                self.part = 1
            self.step = 0
            rot = self.movement['parts'][self.part]['rot']
            self.vel = Vec(self.movement['parts'][self.part]['vel'], 0).rotate(-rot)

        # Wrap around the screen.
        screen_wrap(self)

        # Update actual rect position.
        self.rect.topleft = (self.pos.x, self.pos.y)
