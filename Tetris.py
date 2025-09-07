
import pygame
import random
import sys
import time


shapes = [
    [[1, 5, 9, 13], [4, 5, 6, 7]],
    [[4, 5, 9, 10], [2, 6, 5, 9]],
    [[6, 7, 9, 10], [1, 5, 6, 10]],
    [[2, 1, 5, 9], [0, 4, 5, 6], [1, 5, 9, 8], [4, 5, 6, 10]],
    [[1, 2, 6, 10], [5, 6, 7, 9], [2, 6, 10, 11], [3, 5, 6, 7]],
    [[1, 4, 5, 6], [1, 4, 5, 9], [4, 5, 6, 9], [1, 5, 6, 9]],
    [[1, 2, 5, 6]],
]
shapeColors = [(0, 255, 102)] * len(shapes)


WIDTH = 700
HEIGHT = 640
BLOCK_PIXEL = 24   
GAME_COLS = 10
GAME_ROWS = 20


PLAY_X = 60
PLAY_Y = 40


BG = (0, 0, 0)
MATRIX = (0, 255, 102)
DARK = (0, 100, 40)
SCANLINE_ALPHA = 28


DAS_INITIAL = 0.15   
DAS_INTERVAL = 0.06  


SOFT_DROP_MULT = 6


PREVIEW_CELL = BLOCK_PIXEL * 2
PREVIEW_ORIGIN_X = PLAY_X + GAME_COLS * BLOCK_PIXEL + 50
PREVIEW_ORIGIN_Y = PLAY_Y + 40


SHOW_RAIN = False


class Block:
    def __init__(self, x, y, n):
        self.x = x
        self.y = y
        self.type = n
        self.color = n
        self.rotation = 0
    def image(self):
        return shapes[self.type][self.rotation]
    def rotate(self):
        self.rotation = (self.rotation + 1) % len(shapes[self.type])

class Tetris:
    def __init__(self, height, width):
        self.level = 2
        self.score = 0
        self.state = "start"
        self.height = height
        self.width = width
        self.zoom = BLOCK_PIXEL
        self.x = PLAY_X
        self.y = PLAY_Y
        self.block = None
        self.nextBlock = None
        self.field = [[0 for _ in range(width)] for __ in range(height)]

    def new_block(self):
        self.block = Block(3, 0, random.randint(0, len(shapes) - 1))
    def next_block(self):
        self.nextBlock = Block(3, 0, random.randint(0, len(shapes) - 1))

    def intersects(self):
        for i in range(4):
            for j in range(4):
                if i * 4 + j in self.block.image():
                    if (i + self.block.y > self.height - 1 or
                        j + self.block.x > self.width - 1 or
                        j + self.block.x < 0 or
                        self.field[i + self.block.y][j + self.block.x] > 0):
                        return True
        return False

    def break_lines(self):
        lines = 0
        for i in range(1, self.height):
            if all(self.field[i][j] != 0 for j in range(self.width)):
                lines += 1
                for i1 in range(i, 1, -1):
                    for j in range(self.width):
                        self.field[i1][j] = self.field[i1 - 1][j]
        self.score += lines ** 2

    def go_down(self):
        self.block.y += 1
        if self.intersects():
            self.block.y -= 1
            self.freeze()

    def moveBottom(self):
        while not self.intersects():
            self.block.y += 1
        self.block.y -= 1
        self.freeze()

    def moveDown(self):
        self.block.y += 1
        if self.intersects():
            self.block.y -= 1
            self.freeze()

    def freeze(self):
        for i in range(4):
            for j in range(4):
                if i * 4 + j in self.block.image():
                    self.field[i + self.block.y][j + self.block.x] = self.block.color + 1
        self.break_lines()
        self.block = self.nextBlock
        self.next_block()
        if self.intersects():
            self.state = "gameover"

    def moveHoriz(self, dx):
        old_x = self.block.x
        self.block.x += dx
        if self.intersects():
            self.block.x = old_x

    def rotate(self):
        old_rotation = self.block.rotation
        self.block.rotate()
        if self.intersects():
            self.block.rotation = old_rotation


pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Tetris - Terminal Outline Theme")
clock = pygame.time.Clock()


try:
    mono = pygame.font.Font(pygame.font.match_font('couriernew, courier, monospace'), 18)
    big = pygame.font.Font(pygame.font.match_font('couriernew, courier, monospace'), 26)
except:
    mono = pygame.font.SysFont('Courier New', 18)
    big = pygame.font.SysFont('Courier New', 26)


cols = WIDTH // 10
drops = [random.randint(-200, 0) for _ in range(cols)]

def draw_matrix_rain(surface):
    for i in range(cols):
        x = i * 10
        y = drops[i]
        ch = chr(random.randint(33, 126))
        r = mono.render(ch, True, MATRIX)
        surface.blit(r, (x, y))
        drops[i] += random.randint(6, 20)
        if drops[i] > HEIGHT + random.randint(0, 200):
            drops[i] = random.randint(-200, 0)

def draw_scanlines(surface, spacing=4, alpha=SCANLINE_ALPHA):
    line = pygame.Surface((WIDTH, 1), pygame.SRCALPHA)
    line.fill((0, 0, 0, alpha))
    for y in range(0, HEIGHT, spacing):
        surface.blit(line, (0, y))


def draw_cell_outline(surface, px, py, size, color=MATRIX, thickness=2):
    """Draw a hollow box (outline) representing a block cell."""
    rect = pygame.Rect(px, py, size, size)
    
    pygame.draw.rect(surface, color, rect, thickness, border_radius=2)
    
    inner = pygame.Rect(px + 1, py + 1, size - 2, size - 2)
    pygame.draw.rect(surface, DARK, inner, 1, border_radius=1)

def draw_ghost_piece(surface, game, glyph_positions):
    """Draw ghost (where the block will land). Uses faint outline."""
    
    ghost_y = game.block.y
    while True:
        ghost_y += 1
        ok = True
        for i in range(4):
            for j in range(4):
                p = i * 4 + j
                if p in game.block.image():
                    gy = i + ghost_y
                    gx = j + game.block.x
                    if gy >= game.height or gx < 0 or gx >= game.width or game.field[gy][gx] > 0:
                        ok = False
                        break
            if not ok:
                break
        if not ok:
            ghost_y -= 1
            break
    
    for i in range(4):
        for j in range(4):
            p = i * 4 + j
            if p in game.block.image():
                px = game.x + game.zoom * (j + game.block.x)
                py = game.y + game.zoom * (i + ghost_y)
                
                draw_cell_outline(surface, px + 1, py + 1, game.zoom - 2, color=(0, 120, 50), thickness=1)

def draw_playfield_border(surface, game):
    left_x = game.x - 24
    right_x = game.x + game.zoom * game.width + 6
    for i in range(game.height + 1):
        yy = game.y + i * game.zoom - 6
        surface.blit(mono.render('<', True, MATRIX), (left_x, yy))
        surface.blit(mono.render('>', True, MATRIX), (right_x, yy))
    base = '-' * (game.width * 2)
    surface.blit(mono.render(base, True, MATRIX), (game.x, game.y + game.zoom * game.height + 10))

def draw_next_block_big(surface, game):
    sx = PREVIEW_ORIGIN_X
    sy = PREVIEW_ORIGIN_Y
    
    surface.blit(mono.render("NEXT", True, MATRIX), (sx, sy - 28))
    
    
    preview_area_w = PREVIEW_CELL * 4
    preview_area_h = PREVIEW_CELL * 4
    
    panel = pygame.Surface((preview_area_w + 8, preview_area_h + 8), pygame.SRCALPHA)
    panel.fill((0,0,0,180))
    screen.blit(panel, (sx - 4, sy - 4))
    if not game.nextBlock:
        return
    for i in range(4):
        for j in range(4):
            p = i * 4 + j
            if p in game.nextBlock.image():
                px = sx + j * PREVIEW_CELL
                py = sy + i * PREVIEW_CELL
                draw_cell_outline(surface, px + 6, py + 6, PREVIEW_CELL - 12, color=MATRIX, thickness=2)


class KeyRepeat:
    def __init__(self, initial=DAS_INITIAL, interval=DAS_INTERVAL):
        self.initial = initial
        self.interval = interval
        self.key_state = {}
    def press(self, key):
        self.key_state[key] = {'time': time.time(), 'last': None}
    def release(self, key):
        if key in self.key_state:
            del self.key_state[key]
    def should_fire(self, key):
        """Return True if action should occur this frame for this held key."""
        if key not in self.key_state:
            return False
        now = time.time()
        data = self.key_state[key]
        if data['last'] is None:
            
            data['last'] = now
            return True
        elapsed = now - data['time']
        since_last = now - data['last']
        if elapsed >= self.initial:
            if since_last >= self.interval:
                data['last'] = now
                return True
        return False

key_repeat = KeyRepeat()


def startGame():
    fps = 60
    game = Tetris(GAME_ROWS, GAME_COLS)
    counter = 0
    pressing_down = False
    last_move_time = 0

    
    game.new_block()
    game.next_block()

    running = True
    paused = False
    while running:
        dt = clock.tick(fps) / 1000.0
        counter += 1

        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                
                if event.key == pygame.K_LEFT:
                    key_repeat.press('left')
                if event.key == pygame.K_RIGHT:
                    key_repeat.press('right')
                if event.key == pygame.K_DOWN:
                    pressing_down = True
                if event.key == pygame.K_UP:
                    game.rotate()
                if event.key == pygame.K_SPACE:
                    game.moveBottom()
                if event.key == pygame.K_p:
                    paused = not paused
                if event.key == pygame.K_ESCAPE:
                    
                    game = Tetris(GAME_ROWS, GAME_COLS)
                    game.new_block()
                    game.next_block()
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT:
                    key_repeat.release('left')
                if event.key == pygame.K_RIGHT:
                    key_repeat.release('right')
                if event.key == pygame.K_DOWN:
                    pressing_down = False

        
        if key_repeat.should_fire('left'):
            game.moveHoriz(-1)
        if key_repeat.should_fire('right'):
            game.moveHoriz(1)

        
        if not paused and game.state == "start":
            gravity_timer = 0.5 / game.level  
            if pressing_down:
                
                interval = gravity_timer / SOFT_DROP_MULT
            else:
                interval = gravity_timer
            
            if not hasattr(startGame, "_last_tick"):
                startGame._last_tick = time.time()
                startGame._accum = 0
            now = time.time()
            elapsed = now - startGame._last_tick
            startGame._last_tick = now
            startGame._accum += elapsed
            if startGame._accum >= interval:
                startGame._accum = 0
                game.go_down()

        
        screen.fill(BG)
        if SHOW_RAIN:
            draw_matrix_rain(screen)

        
        panel = pygame.Surface((game.zoom * game.width + 8, game.zoom * game.height + 8), pygame.SRCALPHA)
        panel.fill((0,0,0,220))
        screen.blit(panel, (game.x - 4, game.y - 4))

        
        if game.block and game.state == "start":
            draw_ghost_piece(screen, game, None)

        
        for r in range(game.height):
            for c in range(game.width):
                px = game.x + game.zoom * c
                py = game.y + game.zoom * r
                
                pygame.draw.rect(screen, (0, 32, 0), (px, py, game.zoom, game.zoom), 1)
                if game.field[r][c] != 0:
                    draw_cell_outline(screen, px + 1, py + 1, game.zoom - 2, color=MATRIX, thickness=2)

        
        if game.block is not None:
            for i in range(4):
                for j in range(4):
                    p = i * 4 + j
                    if p in game.block.image():
                        px = game.x + game.zoom * (j + game.block.x)
                        py = game.y + game.zoom * (i + game.block.y)
                        
                        draw_cell_outline(screen, px + 1, py + 1, game.zoom - 2, color=MATRIX, thickness=2)

        
        draw_playfield_border(screen, game)

        
        score_label = mono.render("Score:", True, MATRIX)
        score_val = big.render(str(game.score), True, MATRIX)
        screen.blit(score_label, (20, 12))
        screen.blit(score_val, (20, 36))

        
        inst = mono.render("P - Pause | Arrows - Move | Space - Drop", True, MATRIX)
        screen.blit(inst, (20, HEIGHT - 28))

        
        draw_next_block_big(screen, game)

        
        if game.state == "gameover":
            go_surf = big.render("GAME OVER", True, MATRIX)
            screen.blit(go_surf, (game.x + 20, game.y + 200))
            info = mono.render("Press ESC to restart", True, MATRIX)
            screen.blit(info, (game.x + 20, game.y + 240))

        
        draw_scanlines(screen, spacing=3, alpha=SCANLINE_ALPHA)

        pygame.display.flip()


def main_menu():
    while True:
        screen.fill(BG)
        title = big.render("Press any key to begin!", True, MATRIX)
        screen.blit(title, (40, 260))
        sub = mono.render("Terminal Tetris - Outline Blocks", True, MATRIX)
        screen.blit(sub, (40, 320))
        draw_scanlines(screen, spacing=4, alpha=16)
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                startGame()

if __name__ == "__main__":
    main_menu()
