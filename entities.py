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
            # Return the position the sprite should be at so it is touching
            # but not overlapping the sprite it touched.
            if hits[0].hit_rect.centerx > sprite.hit_rect.centerx:
                return hits[0], \
                       hits[0].hit_rect.left - sprite.hit_rect.width / 2, \
                       "left"

            if hits[0].hit_rect.centerx < sprite.hit_rect.centerx:
                return hits[0], \
                       hits[0].hit_rect.right + sprite.hit_rect.width / 2, \
                       "right"

    elif direction == "y":
        # Find all sprites in the target group that are bring hit.
        hits = pg.sprite.spritecollide(sprite, group, False, collide_hit_rect_both)
        if hits:
            # Return the position the sprite should be at so it is touching
            # but not overlapping the sprite it touched.
            if hits[0].hit_rect.centery > sprite.hit_rect.centery:
                return hits[0], \
                       hits[0].hit_rect.top - sprite.hit_rect.height / 2, \
                       "bottom"

            if hits[0].hit_rect.centery < sprite.hit_rect.centery:
                return hits[0], \
                       hits[0].hit_rect.bottom + sprite.hit_rect.height / 2, \
                       "top"

    # Return three None values as no hit was detected. If there is a hit,
    # three values are returned, so if there is no hit, three values must
    # also be returned.
    return None, None, None


class Player(pg.sprite.Sprite):
    def __init__(self, game, x, y, image_string):
        self._layer = PLAYER_LAYER
        # Pygame sprite creation with groups.
        self.groups = game.all_sprites, game.visible_sprites
        pg.sprite.Sprite.__init__(self, self.groups)
        # Save the game object to access data later.
        self.game = game
        # Position.
        self.pos = Vec(x, y)
        self.vel = Vec(0, 0)
        self.acc = Vec(0, 0)
        self.rot = 0
        self.rot_vel = 0
        self.rot_acc = 0
        # jump = up/down/left/right (diagonal movement works too).
        # spin = forwards/backwards/left/right (spin to turn).
        self.move_type = "jump"
        # Jumping.
        self.jumping = False
        self.jumps = 0
        self.on_ground = False
        self.gravity_orientation = 1
        # Sprite image.
        self.image_string = image_string
        self.image = game.player_imgs[image_string]
        self.image = pg.transform.rotate(self.image, self.rot)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.hit_rect = pg.Rect(self.rect.x, self.rect.x,
                                PLAYER_HIT_RECT_WIDTH, PLAYER_HIT_RECT_HEIGHT)
        self.hit_rect.center = self.rect.center
        self.color = CYAN

    def update_image(self):
        # Use .copy() to not modify the stored image
        self.image = self.game.player_imgs[self.image_string].copy()
        self.rect = self.image.get_rect()

        # Image details.
        self.image = pg.transform.rotate(self.image, self.rot)
        self.rect = self.image.get_rect()
        self.rect.center = (self.pos.x, self.pos.y)
        self.hit_rect.center = self.rect.center

    def can_wall_jump(self):
        if not self.on_ground:
            self.hit_rect.centerx += 1
            hit_obj, hit_x, side = collide_group(self, self.game.walls, "x")
            self.hit_rect.centerx -= 1
            if hit_obj:
                return -1
            else:
                self.hit_rect.centerx -= 1
                hit_obj, hit_x, side = collide_group(self, self.game.walls, "x")
                self.hit_rect.centerx += 1
                if hit_obj:
                    return 1
                else:
                    return False

    def jump(self, wall_jump):
        # Jump.
        self.jumping = True
        self.vel.y = PLAYER_MOVEMENT["jump"]["jump"] * self.gravity_orientation
        if wall_jump:
            # Wall jump if required. The wall jump value will be either
            # positive or negative 1, which will determine which way to move
            # away from the wall.
            self.vel.x = PLAYER_MOVEMENT["jump"]["wall jump"] * wall_jump
        else:
            # Only take off jumps if it is not a wall jump.
            self.jumps -= 1

    def apply_keys(self, move_type):
        # Get key presses.
        keys = pg.key.get_pressed()

        # Apply key presses.
        if move_type == "jump":
            if keys[K_a] or keys[K_LEFT]:
                self.acc.x = -PLAYER_MOVEMENT["jump"]["acc"]
            if keys[K_d] or keys[K_RIGHT]:
                self.acc.x = PLAYER_MOVEMENT["jump"]["acc"]
            if keys[K_SPACE] and self.on_ground:
                self.jump(False)
        elif move_type == "spin":
            if keys[K_a] or keys[K_LEFT]:
                self.rot_acc = PLAYER_MOVEMENT["spin"]["rot acc"]
            if keys[K_d] or keys[K_RIGHT]:
                self.rot_acc = -PLAYER_MOVEMENT["spin"]["rot acc"]
            if keys[K_w] or keys[K_UP]:
                self.acc = Vec(PLAYER_MOVEMENT["spin"]["acc"], 0).rotate(-self.rot)
            if keys[K_s] or keys[K_DOWN]:
                self.acc = Vec(-PLAYER_MOVEMENT["spin"]["acc"] / 3, 0).rotate(-self.rot)

    def move_type_update(self):
        keys = pg.key.get_pressed()
        if keys[K_1]:
            self.move_type = "jump"
        elif keys[K_2]:
            self.move_type = "spin"

    def move(self, move_type):
        # Save the position before any new movement.
        last_pos = Vec(self.pos.x, self.pos.y)

        # Reset acceleration.
        self.acc = Vec(0, 0)
        self.rot_acc = 0

        if move_type == "jump":
            # Apply gravity to the jump move type.
            self.acc = Vec(0, PLAYER_MOVEMENT["jump"]["gravity"] * self.gravity_orientation)

        # Get key presses for movement.
        self.apply_keys(move_type)

        if move_type == "jump":
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
        elif move_type == "spin":
            # Forward/backwards movement.
            # Apply friction.
            self.acc += self.vel * PLAYER_MOVEMENT["spin"]["friction"]
            # New velocity after.
            # vf = vi + at
            self.vel = self.vel + self.acc * self.game.dt
            # Displacement.
            # d = vit + 1/2at^2
            displacement = self.vel * self.game.dt + 0.5 * self.acc * self.game.dt ** 2
            self.pos += displacement

            # Rotation movement.
            # Apply friction.
            self.rot_acc += self.rot_vel * PLAYER_MOVEMENT["spin"]["friction"]
            # New velocity after.
            self.rot_vel = self.rot_vel + self.rot_acc * self.game.dt
            # Displacement.
            rot_displacement = self.rot_vel * self.game.dt + 0.5 * self.rot_acc * self.game.dt ** 2
            self.rot += rot_displacement % 360

        # Edge of screen teleport.
        if self.pos.x < 0:
            self.pos.x = self.game.map.width
        elif self.pos.x > self.game.map.width:
            self.pos.x = 0

        # Collision detection x.
        self.hit_rect.centerx = self.pos.x
        hit_obj, hit_x, side = collide_group(self, self.game.walls, "x")
        if hit_x:
            # There is a collision. hit_x is where the player's x and y
            # should be to line up against what it collided against.
            self.pos.x = hit_x
            self.hit_rect.centerx = self.pos.x
            if self.move_type == "jump":
                # Stop against the wall.
                self.vel.x = 0
                # Slide down a wall slowly if not on the ground and going down
                # beside a wall.
                if self.gravity_orientation == 1 and not self.on_ground \
                        and self.vel.y > 0:
                    self.vel.y *= PLAYER_MOVEMENT["jump"]["wall slide"]
                elif self.gravity_orientation == -1 and not self.on_ground \
                        and self.vel.y < 0:
                    self.vel.y *= PLAYER_MOVEMENT["jump"]["wall slide"]
            else:
                # Bounce off the wall.
                self.vel.x *= -1

        # Collision detection y.
        self.hit_rect.centery = self.pos.y
        hit_obj, hit_y, side = collide_group(self, self.game.walls, "y")
        if hit_y:
            # There is a collision. hit_x is where the player's x and y
            # should be to line up against what it collided against.
            self.pos.y = hit_y
            self.hit_rect.centery = self.pos.y
            if self.move_type == "jump":
                # Stop against the wall.
                self.vel.y = 0
                if side == "bottom" and self.gravity_orientation == 1 or \
                        side == "top" and self.gravity_orientation == -1:
                    # The player can jump again if they landed on a floor.
                    self.jumps = JUMPS
                    self.on_ground = True
                    self.jumping = False
            elif self.move_type == "spin":
                # Bounce off the wall.
                self.vel.y *= -hit_obj.bounce
        elif self.on_ground:
            # If not touching a wall and on_ground is True, it should be set
            # to False.
            self.on_ground = False
            if not self.jumping:
                # If not jumping, that means the player fell off an edge.
                # This means they will lose a jump. So, if they can double
                # jump, they will only actually be able to jump once.
                self.jumps -= 1

        # Match the sprite's rect with where it should be, based on the hit
        # rect.
        self.rect.center = self.hit_rect.center

    def update(self):
        # Update the movement mode.
        self.move_type_update()

        # Move the player sprite based on the current movement mode type.
        self.move(self.move_type)

        # Update the sprite image with the correct positioning.
        self.update_image()


class Obstacle(pg.sprite.Sprite):
    def __init__(self, game, x, y, width, height, obstacle_type,
                 bounce=1):
        if obstacle_type == "wall":
            self.groups = game.all_sprites, game.obstacles, game.walls
            self.color = GREEN
        elif obstacle_type == "void":
            self.groups = game.all_sprites, game.obstacles, game.voids
            self.color = RED
        pg.sprite.Sprite.__init__(self, self.groups)
        self.rect = pg.Rect(x, y, width, height)
        self.hit_rect = self.rect
        self.obstacle_type = obstacle_type
        # Bounce is the how much of the velocity should be conserved when
        # bouncing off the wall. It is a multiplier, so 0 is none, 1 is all,
        # and 2 would be twice the velocity, and so on.
        self.bounce = bounce
