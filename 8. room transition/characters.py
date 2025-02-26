import pygame
from settings import *

class NPC(pygame.sprite.Sprite):
	def __init__(self, game, scene, groups, pos, z, name):
		super().__init__(groups)

		self.game = game
		self.scene = scene
		self.z = z
		self.name = name
		self.frame_index = 0
		self.import_images()
		self.image = self.animations['idle_down'][self.frame_index].convert_alpha()
		self.rect = self.image.get_rect(topleft = pos)
		self.pos = pygame.math.Vector2(self.rect.center)
		self.hitbox = self.rect.copy().inflate(-self.rect.width * 0.5,- self.rect.height * 0.5)
		self.old_pos = self.pos.copy()
		self.old_hitbox = self.hitbox.copy()
		self.acc = pygame.math.Vector2()
		self.vel = pygame.math.Vector2()
		self.force = 2000
		self.speed = 60
		self.friction = -15
		self.state = Idle(self)
		self.move = {'left':False, 'right':False, 'up':False, 'down':False}

	def get_direction(self):
		angle = self.vel.angle_to(pygame.math.Vector2(0,1))
		angle = (angle + 360) % 360
		if 45 <= angle < 135: return 'right'
		elif 135 <= angle < 225: return 'up'
		elif 225 <= angle < 315: return 'left'
		else: return 'down'

	def movement(self):
		if self.move['left']: self.acc.x = -2000
		elif self.move['right']: self.acc.x = 2000
		else: self.acc.x = 0

		if self.move['up']: self.acc.y = -2000
		elif self.move['down']: self.acc.y = 2000
		else: self.acc.y = 0

	def import_images(self):
		path = f'assets/characters/{self.name}/'

		self.animations = self.game.get_animation_states(path)

		for animation in self.animations.keys():
			full_path = path + animation
			self.animations[animation] = self.game.get_images(full_path)

	def animate(self, state, fps, loop=True):

		self.frame_index += fps

		if self.frame_index >= len(self.animations[state]):
			if loop: 
				self.frame_index = 0
			else:
				self.frame_index = len(self.animations[state]) -1
		
		self.image = self.animations[state][int(self.frame_index)]

	def get_collide_list(self, group): 
		collidable_list = pygame.sprite.spritecollide(self, group, False)
		return collidable_list

	def collisions(self, direction, group):
		for sprite in self.get_collide_list(group):
			if self.hitbox.colliderect(sprite.hitbox):
				if direction == 'x':
					if self.vel.x >= 0: self.hitbox.right = sprite.hitbox.left
					if self.vel.x <= 0: self.hitbox.left = sprite.hitbox.right
					self.rect.centerx = self.hitbox.centerx
					self.pos.x = self.hitbox.centerx
				if direction == 'y':			
					if self.vel.y >= 0: self.hitbox.bottom = sprite.hitbox.top	
					if self.vel.y <= 0: self.hitbox.top = sprite.hitbox.bottom
					self.rect.centery = self.hitbox.centery
					self.pos.y = self.hitbox.centery

	def physics(self, dt, friction):

		# x direction
		self.acc.x += self.vel.x * friction
		self.vel.x += self.acc.x * dt
		self.pos.x += self.vel.x * dt + (0.5 * self.vel.x) * dt
		self.hitbox.centerx = round(self.pos.x)
		self.rect.centerx = self.hitbox.centerx
		self.collisions('x', self.scene.block_sprites)

		#y direction
		self.acc.y += self.vel.y * friction
		self.vel.y += self.acc.y * dt
		self.pos.y += self.vel.y * dt + (0.5 * self.vel.y) * dt
		self.hitbox.centery = round(self.pos.y)
		self.rect.centery = self.hitbox.centery
		self.collisions('y', self.scene.block_sprites)
		
		if self.vel.magnitude() >= self.speed: 
			self.vel = self.vel.normalize() * self.speed

	def change_state(self):
		new_state = self.state.enter_state(self)
		if new_state: self.state = new_state
		else: self.state

	def update(self, dt):
		self.get_direction()
		self.change_state()
		self.state.update(dt, self)

class Idle:
	def __init__(self, character):
		character.frame_index = 0

	def enter_state(self, character):
		if character.vel.magnitude() > 1:
			return Run(character)

	def update(self, dt, character):
		character.animate(f'idle_{character.get_direction()}', 15 * dt)
		character.movement()
		character.physics(dt, character.friction)

class Run:
	def __init__(self, character):
		Idle.__init__(self, character)

	def enter_state(self, character):
		if character.vel.magnitude() < 1:
			return Idle(character)

	def update(self, dt, character):
		character.animate(f'run_{character.get_direction()}', 15 * dt)
		character.movement()
		character.physics(dt, character.friction)

class Dash:
	def __init__(self, character):
		Idle.__init__(self, character)
		self.timer = 3

	def enter_state(self, character):
		if self.timer < 0:
			return Idle(character)

	def update(self, dt, character):
		self.timer -= dt
		character.animate(f'attack_{character.get_direction()}', 15 * dt)
		character.vel = vec()
