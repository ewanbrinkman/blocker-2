from random import randint
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
        self.displacement = Vec(0, 0)
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

        self.moving_obstacle = None

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

                self.hit_rect.centerx += 1
                collision = pg.sprite.spritecollide(self, self.game.walls,
                                                    False,
                                                    collide_hit_rect_both)
                self.hit_rect.centerx -= 1

                if collision:
                    wall_jump_direction = -1
                else:
                    self.hit_rect.centerx -= 1
                    collision = pg.sprite.spritecollide(self, self.game.walls,
                                                        False,
                                                        collide_hit_rect_both)
                    self.hit_rect.centerx += 1

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

    def check_force_push(self):
        # Check to see what the player was pushed into, and if they should
        # be killed because of it.
        hits = pg.sprite.spritecollide(self, self.game.walls, False,
                                       collide_hit_rect_both)
        if hits:
            # The player was pushed into something they should not be in,
            # reset their position to the start.
            self.pos = Vec(100, 1900)

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
                if self.vel.y >= 0 and self.gravity_orientation == 1 or \
                        self.vel.y <= 0 and self.gravity_orientation == -1:
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

            # Test to reset y velocity. The only scenario where it would not
            # be reset when their is a y axis collision, is when it is a
            # moving obstacle. That way, you smoothly move with the moving
            # obstacle. If there is no moving obstacle, then reset the y
            # velocity.
            self.moving_obstacle = None
            for hit in hits:
                if isinstance(hit, MovingObstacle):
                    if self.vel.y >= 0 and self.gravity_orientation == 1 or \
                            self.vel.y <= 0 and self.gravity_orientation == -1:
                        self.moving_obstacle = hit
            if not self.moving_obstacle:
                self.vel.y = 0

            # Follow along on x.
            for hit in hits:
                if isinstance(hit, MovingObstacle):
                    # Only follow along if the moving obstacle is going down.
                    if hit.vel.y >= 0 and self.gravity_orientation == 1 or \
                            hit.vel.y <= 0 and self.gravity_orientation == -1:
                        self.pos.x += hit.vel.x * self.game.dt
        else:
            # Reset velocity of just fell off a moving platform.
            if self.moving_obstacle and not self.jumping:
                if self.vel.y >= 0 and self.gravity_orientation == 1 or \
                        self.vel.y <= 0 and self.gravity_orientation == -1:
                    # If going down, start falling at the speed of the
                    # platform.
                    if self.gravity_orientation == 1:
                        if self.moving_obstacle.vel.y > 0:
                            self.vel.y = self.moving_obstacle.vel.y
                        else:
                            self.vel.y = 0
                            # self.vel.y = self.moving_obstacle.vel.y
                    elif self.gravity_orientation == -1:
                        if self.moving_obstacle.vel.y < 0:
                            self.vel.y = self.moving_obstacle.vel.y
                        else:
                            self.vel.y = 0
                            # self.vel.y = self.moving_obstacle.vel.y
                    self.moving_obstacle = None
                    # Make sure to counteract the velocity that was just added
                    # this frame, and add the correct velocity instead (the
                    # new velocity for this frame will become the velocity
                    # of the platform.
                    self.pos.y += self.displacement.y * -1
                    self.pos.y += self.vel.y * self.game.dt
                    self.hit_rect.centery = self.pos.y
            # Test to see if a platform is nearby. Make the player move
            # along with the moving obstacle along x if they are close
            # enough to the moving obstacle.
            check_direction_amount = 5
            if self.gravity_orientation == 1:
                self.hit_rect.y += check_direction_amount
                hits = pg.sprite.spritecollide(self, self.game.moving_walls, False,
                                               collide_hit_rect_both)
                self.hit_rect.y -= check_direction_amount
            elif self.gravity_orientation == -1:
                self.hit_rect.y -= check_direction_amount
                hits = pg.sprite.spritecollide(self, self.game.moving_walls,
                                               False,
                                               collide_hit_rect_both)
                self.hit_rect.y += check_direction_amount
            if hits:
                # Near a platform.
                self.on_ground = True
                # Make the player move along with the moving obstacle along x.
                self.pos.x += hits[0].vel.x * self.game.dt

                # Update player rect.
                self.hit_rect.centerx = self.pos.x
            else:
                # Not near a platform.
                self.on_ground = False

        self.rect.center = self.hit_rect.center

    def collide_items(self):
        hits = pg.sprite.spritecollide(self, self.game.items, False,
                                       collide_hit_rect_both)
        if hits:
            for hit in hits:
                if hit.item_type == "coin":
                    self.game.sounds['coin'].play()
                hit.destroy()

    def move(self):
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
        self.displacement = self.vel * self.game.dt + 0.5 * self.acc * \
                        self.game.dt ** 2

        self.pos += self.displacement

        # Wrap around the screen.
        # screen_wrap(self)

        self.collide_walls()

        self.collide_items()

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
        # If the moving obstacle goes goes back, then copy create a copy of
        # movement and add it to movement, except reversed.
        if self.movement['back']:
            back_part = self.parts.copy()
            back_part.reverse()
            self.parts += back_part

        # Movement for the current part.
        rot = self.movement['parts'][self.parts[self.part - 1]]['rot']
        self.vel = Vec(
            self.movement['parts'][self.parts[self.part - 1]]['vel'],
            0).rotate(-rot)
        self.distance = self.movement['parts'][self.parts[self.part - 1]][
            'distance']
        # The starting position for each movement part.
        self.start_pos = Vec(x, y)
        self.end_pos = Vec(self.start_pos.x, self.start_pos.y) + Vec(
            self.distance, 0).rotate(-rot)

        # Other data.
        self.game = game

    def move(self):
        # Update position.
        self.pos += self.vel * self.game.dt

        # If the moving obstacle moved onto the player, push the player out
        # of the way.
        pos = Vec(self.game.player.pos.x, self.game.player.pos.y)
        self.collide_player()

        # Update current part of movement if f the moving obstacle moved the
        # required distance.
        distance = self.pos - self.start_pos
        distance = distance.length()
        if distance >= self.distance:
            # Set end position, and make sure player is there too.
            # self.pos = Vec(self.end_pos.x, self.end_pos.y)

            # If all steps are done for the section, go to the next section.
            if self.part + 1 <= len(self.parts):
                # Go to the next part if.
                self.part += 1
            else:
                # The final part just finished, so go back to the start.
                self.part = 1
            rot = self.movement['parts'][self.parts[self.part - 1]]['rot']
            self.vel = Vec(
                self.movement['parts'][self.parts[self.part - 1]]['vel'],
                0).rotate(-rot)
            self.distance = self.movement['parts'][self.parts[self.part - 1]][
                'distance']
            # The starting position for each movement part.
            self.start_pos = Vec(self.pos.x, self.pos.y)
            # Make the vel and distance the opposite if it is on the way back.
            if self.part > self.one_way_length:
                self.vel *= -1
                self.end_pos = Vec(self.start_pos.x, self.start_pos.y) - Vec(
                    self.distance, 0).rotate(-rot)
            else:
                self.end_pos = Vec(self.start_pos.x, self.start_pos.y) + Vec(
                    self.distance, 0).rotate(-rot)

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

        # Check to see if the player was pushed into anything they shouldn't
        # be in.
        self.game.player.check_force_push()

    def update(self):
        # Move the obstacle around.
        self.move()


class Item(pg.sprite.Sprite):
    def __init__(self, game, pos, item_type, random_start_step):
        self.groups = game.all_sprites, game.visible_sprites, game.items
        pg.sprite.Sprite.__init__(self, self.groups)
        # Image.
        if item_type == "coin":
            item_img = "coinGold.png"
        else:
            item_img = "coinGold.png"
        self.image = game.item_imgs[item_img]
        self.rect = self.image.get_rect()
        self.hit_rect = self.rect
        self.rect.center = pos
        self.hit_rect.center = pos
        # Data to store.
        self.game = game
        self.item_type = item_type
        self.pos = pos
        # Item bob animation.
        self.tween = easeInOutSine
        if random_start_step:
            self.step = randint(0, BOB_RANGE)
        else:
            self.step = 0
        self.direction = 1
        # Debug.
        self.color = YELLOW

    def update(self):
        # bobbing motion (subtract 0.5 to shift halfway)
        offset = BOB_RANGE * (self.tween(self.step / BOB_RANGE) - 0.5)
        self.rect.centery = self.pos.y + offset * self.direction
        self.step += BOB_SPEED
        # switch and reset if hit maximum
        if self.step > BOB_RANGE:
            self.step = 0
            self.direction *= -1

    def destroy(self):
        # Remove the item.
        self.kill()
