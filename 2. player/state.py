from settings import *
import pygame
from pytmx.util_pygame import load_pygame

class State:
	def __init__(self, game):
		self.game = game
		self.prev_state = None

	def actions(self, events):
		pass

	def update(self, dt):
		pass

	def draw(self, screen):
		pass

	def enter_state(self):
		if len(self.game.stack) > 1:
			self.prev_state = self.game.stack[-1]
		self.game.stack.append(self)

	def exit_state(self):
		self.game.stack.pop()

class Object(pygame.sprite.Sprite):
	def __init__(self, groups, pos, surf=pygame.Surface((TILESIZE, TILESIZE)), z= LAYERS['blocks']):
		super().__init__(groups)

		self.image = surf
		self.rect = self.image.get_rect(topleft = pos)
		self.hitbox = self.rect.copy().inflate(0,0)
		self.old_hitbox = self.hitbox.copy()
		self.z = z

class NPC(pygame.sprite.Sprite):
	def __init__(self, game, scene, groups, pos, name, z):
		super().__init__(groups)

		self.game = game
		self.scene = scene
		self.name = name
		self.z = z
		self.import_images()
		self.frame_index = 0
		self.image = self.animations['fall'][self.frame_index].convert_alpha()
		self.rect = self.image.get_rect(topleft = pos)
		self.pos = pygame.math.Vector2(self.rect.center)
		self.hitbox = self.rect.copy().inflate(-self.rect.width * 0.5,- self.rect.height * 0.5)
		self.old_pos = self.pos.copy()
		self.old_hitbox = self.hitbox.copy()
		self.speed = 80
		self.force = pygame.math.Vector2()
		self.vel = pygame.math.Vector2()
		self.friction = -20
		self.facing = 0
		self.alive = True
		
	def import_images(self):
		path = f'assets/characters/{self.name}/'

		self.animations = self.game.get_animation_states(path)

		for animation in self.animations.keys():
			full_path = path + animation
			self.animations[animation] = self.game.get_images(full_path)

	def input(self):

		keys = pygame.key.get_pressed()

		if keys[pygame.K_LEFT]:
			self.force.x = -2000
		elif keys[pygame.K_RIGHT]:
			self.force.x = 2000
		else:
			self.force.x = 0

		if keys[pygame.K_UP]:
			self.force.y = -2000
		elif keys[pygame.K_DOWN]:
			self.force.y = 2000
		else:
			self.force.y = 0

	def animate(self, state, speed, loop=True):

		self.frame_index += speed

		if self.frame_index >= len(self.animations[state]):
			if loop: 
				self.frame_index = 0
			else:
				self.frame_index = len(self.animations[state]) -1
		
		direction = self.facing if self.facing == 1 else 0
		self.image = pygame.transform.flip(self.animations[state][int(self.frame_index)], direction-1, False)

	def physics(self, dt):

		# x direction
		self.force.x += self.vel.x * self.friction
		self.vel.x += self.force.x * dt
		self.pos.x += self.vel.x * dt + (0.5 * self.vel.x) * dt
		self.hitbox.centerx = round(self.pos.x)
		self.rect.centerx = self.hitbox.centerx

		#y direction
		self.force.y += self.vel.y * self.friction
		self.vel.y += self.force.y * dt
		self.pos.y += self.vel.y * dt + (0.5 * self.vel.y) * dt
		self.hitbox.centery = round(self.pos.y)
		self.rect.centery = self.hitbox.centery
		
		if self.vel.magnitude() >= self.speed: 
			self.vel = self.vel.normalize() * self.speed

	def update(self, dt):

		self.animate('run', 15 * dt)
		self.input()
		self.physics(dt)


class Player(NPC):
	def __init__(self, game, scene, groups, pos, name, z):
		super().__init__(game, scene, groups, pos, name, z)

class Camera(pygame.sprite.Group):
    def __init__(self, game, scene):
        super().__init__()

        self.game = game
        self.scene = scene
        self.offset = pygame.math.Vector2()

    def draw(self, target, group):
        self.game.screen.fill(LIGHT_GREY)

        self.offset = target.rect.center - RES/2

        for layer in LAYERS.values():
            for sprite in group:
                if sprite.z == layer: # and self.scene.visible_window.contains(sprite.rect):
                    offset = sprite.rect.topleft - self.offset
                    self.game.screen.blit(sprite.image, offset)

class Scene(State):
	def __init__(self, game):
		State.__init__(self, game)

		self.game = game
		self.current_scene = 'tutorial'
		self.entry_point = '0'
		self.exiting = False
		
		self.camera = Camera(self.game, self)
		self.drawn_sprites = pygame.sprite.Group()
		self.update_sprites = pygame.sprite.Group()
		self.block_sprites = pygame.sprite.Group()

		# create all objects in the scene using tmx data
		self.tmx_data = load_pygame(f'scenes/{self.current_scene}/{self.current_scene}.tmx')

		self.create_scene_instances()

	def get_scene_size(self):
		with open(f'../scenes/{self.current_scene}/{self.current_scene}_blocks.csv', newline='') as csvfile:
		    reader = csv.reader(csvfile, delimiter=',')
		    for row in reader:
		        rows = (sum (1 for row in reader) + 1)
		        cols = len(row)
		return (cols * TILESIZE, rows * TILESIZE)

	def create_scene_instances(self):

		layers = []
		for layer in self.tmx_data.layers:
			layers.append(layer.name)

		if 'blocks' in layers:
			for x, y, surf in self.tmx_data.get_layer_by_name('blocks').tiles():
				Object([self.block_sprites, self.drawn_sprites], (x * TILESIZE, y * TILESIZE), surf, LAYERS['blocks'])

		if 'entries' in layers:
			for obj in self.tmx_data.get_layer_by_name('entries'):
				if obj.name == self.entry_point:
					self.player = Player(self.game, self, [self.update_sprites, self.drawn_sprites], (obj.x, obj.y), 'player', LAYERS['player'])

	def update(self, dt):
		self.update_sprites.update(dt)

	def debug(self, debug_list):
		for index, name in enumerate(debug_list):
			self.game.render_text(name, WHITE, self.game.font, (10, 15 * index))

	def draw(self, screen):

		self.camera.draw(self.player, self.drawn_sprites)
		self.debug([str('FPS: '+ str(round(self.game.clock.get_fps(), 2))),
					str('force: '+ str(round(self.player.force, 2))),
					str('vel: '+ str(round(self.player.vel, 2))),
					None,])


class SplashScreen(State):
	def __init__(self, game):
		State.__init__(self, game)
		
	def update(self, dt):
		if ACTIONS['space']:
			Scene(self.game).enter_state()

	def draw(self, screen):
		screen.fill(BLUE)