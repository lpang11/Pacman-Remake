import sys
import pygame
import os
import random
import time
import threading

os.environ['SDL_VIDEO_CENTERED'] = '1'
WIN_W = 32 * 31
WIN_H = 32 * 40
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (244, 22, 22)
BLUE = (119, 157, 255)
YELLOW = (255, 243, 17)
intro = outro = gameplay = True
lose = win = superstate = blink_ghost = False
clock = pygame.time.Clock()


class Camera(object):
    def __init__(self, total_width, total_height):
        self.state = pygame.Rect(0, 0, total_width, total_height)

    def apply(self, target):
        return target.rect.move(self.state.topleft)

    def update(self, target_rect):
        x = -target_rect.x + WIN_W / 2
        y = -target_rect.y + WIN_H / 2
        if x > 0:
            x = 0
        elif x < -(self.state.width - WIN_W):
            x = -(self.state.width - WIN_W)
        if y > 0:
            y = 0
        elif y < -(self.state.height - WIN_H):
            y = -(self.state.height - WIN_H)
        self.state = pygame.Rect(x, y, self.state.width, self.state.height)


class Hero(pygame.sprite.Sprite):
    def __init__(self, x, y, col):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load("images/pacman.png").convert_alpha()
        self.rect = self.image.get_rect()
        self.rect = self.rect.move(x, y)
        self.col = col
        self.speed = 2.5
        self.lives = 3
        self.score = 0

    def collide(self, platform_group, dir):
        for p in platform_group:
            if pygame.sprite.collide_rect(self, p):
                if dir == "up" and self.rect.top < p.rect.bottom:
                    self.rect.top = p.rect.bottom
                elif dir == "down" and self.rect.bottom > p.rect.top:
                    self.rect.bottom = p.rect.top
                elif dir == "left" and self.rect.left < p.rect.right:
                    self.rect.left = p.rect.right
                elif dir == "right" and self.rect.right > p.rect.left:
                    self.rect.right = p.rect.left

    def update(self, platform_group, pill_group, enemy_group, powerup_group, fruit_group):
        global lose, win, superstate, WIN_W, blink_ghost

        def false():
            global superstate
            superstate = False

        def blinkghost():
            global blink_ghost
            blink_ghost = True

        key = pygame.key.get_pressed()

        if key[pygame.K_w] or key[pygame.K_UP]:
            self.rect.y -= self.speed
            self.collide(platform_group, "up")
            self.image = pygame.image.load("images/pacmanup.png").convert_alpha()
            if pygame.time.get_ticks() % 500 < 250:
                self.image = pygame.image.load("images/pacman closed.png").convert_alpha()
        elif key[pygame.K_s] or key[pygame.K_DOWN]:
            self.rect.y += self.speed
            self.collide(platform_group, "down")
            self.image = pygame.image.load("images/pacmandown.png").convert_alpha()
            if pygame.time.get_ticks() % 500 < 250:
                self.image = pygame.image.load("images/pacman closed.png").convert_alpha()
        if key[pygame.K_a] or key[pygame.K_LEFT]:
            self.rect.x -= self.speed
            self.collide(platform_group, "left")
            self.image = pygame.image.load("images/pacmanleft.png").convert_alpha()
            if pygame.time.get_ticks() % 500 < 250:
                self.image = pygame.image.load("images/pacman closed.png").convert_alpha()
        elif key[pygame.K_d] or key[pygame.K_RIGHT]:
            self.rect.x += self.speed
            self.collide(platform_group, "right")
            self.image = pygame.image.load("images/pacman.png").convert_alpha()
            if pygame.time.get_ticks() % 500 < 250:
                self.image = pygame.image.load("images/pacman closed.png").convert_alpha()

        if self.rect.x >= WIN_W:
            self.rect.x = 0
            self.rect.y = 32 * 18
        elif self.rect.x <= 0:
            self.rect.x = 32 * 31
            self.rect.y = 32 * 18

        collisions = pygame.sprite.spritecollide(self, pill_group, True)
        for key in collisions:
            self.score += key.score

        if pygame.sprite.spritecollideany(self, enemy_group) and not superstate:
            self.lives -= 1
            self.rect.x = 16 * 32
            self.rect.y = 20 * 32

        if self.lives <= 0:
            lose = True

        if pygame.sprite.spritecollide(self, fruit_group, True):
            self.score += 100

        if pygame.sprite.spritecollide(self, powerup_group, True):
            self.score += 50
            superstate = True
            # timing superstate and blinking ghost animation
            t = threading.Timer(15.0, false)
            t.start()
            e = threading.Timer(10.0, blinkghost)
            e.start()


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, image, color):
        pygame.sprite.Sprite.__init__(self)
        self.speed = 2.3
        self.direction = random.randint(1, 4)
        self.moves = random.randint(100, 200)
        self.moveCount = 0
        self.image = image
        self.color = color
        self.image = pygame.image.load(image).convert_alpha()
        self.rect = self.image.get_rect()
        self.rect = self.rect.move(x, y)
        self.scared = self.killed = False

    def update(self, platform_group, hero, hero_group):
        global superstate, blink_ghost

        xMove, yMove = 0, 0

        if self.rect.x >= WIN_W:
            self.rect.x = 0
            self.rect.y = 32 * 18
        elif self.rect.x <= 0:
            self.rect.x = 32 * 31
            self.rect.y = 32 * 18
        # ghost direction
        if self.direction == 1:
            xMove = -self.speed
        elif self.direction == 2:
            yMove = -self.speed
        elif self.direction == 3:
            xMove = self.speed
        elif self.direction == 4:
            yMove = self.speed

        self.rect.move_ip(xMove, yMove)

        if pygame.sprite.spritecollideany(self, platform_group):
            self.rect.move_ip(-xMove, -yMove)
            self.direction = random.randint(1, 4)

        if superstate and not self.killed:
            self.scared = True
            self.image = pygame.image.load("images/scaredghost.png").convert_alpha()

        if blink_ghost:
            if not self.killed:
                self.image = pygame.image.load("images/scaredghost.png").convert_alpha()
                if pygame.time.get_ticks() % 1000 < 500:
                    self.image = pygame.image.load("images/scaredghost2.png").convert_alpha()
        # logic of superstate
        if not superstate:
            self.scared = False
            self.killed = False
            blink_ghost = False
            if self.color == 'red':
                self.image = pygame.image.load("images/red.png").convert_alpha()
            if self.color == 'blue':
                self.image = pygame.image.load("images/blue.png").convert_alpha()
            if self.color == 'pink':
                self.image = pygame.image.load("images/pink.png").convert_alpha()
            if self.color == 'orange':
                self.image = pygame.image.load("images/orange.png").convert_alpha()

        if pygame.sprite.spritecollideany(self, hero_group) and self.scared:
            self.scared = False
            self.killed = True
            if self.color == 'red':
                self.image = pygame.image.load("images/red.png").convert_alpha()
            if self.color == 'blue':
                self.image = pygame.image.load("images/blue.png").convert_alpha()
            if self.color == 'pink':
                self.image = pygame.image.load("images/pink.png").convert_alpha()
            if self.color == 'orange':
                self.image = pygame.image.load("images/orange.png").convert_alpha()
            self.rect.x = 16 * 32
            self.rect.y = 18 * 32
            hero.score += 200
            self.direction = random.randint(1, 4)

        if pygame.sprite.spritecollideany(self, hero_group) and self.killed:
            hero.lives -= 1
            time.sleep(1.5)
            hero.rect.x = 16 * 32
            hero.rect.y = 20 * 32


class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, col, color):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load("images/platform.png").convert()
        self.rect = self.image.get_rect()
        self.rect = self.rect.move(x, y)
        self.col = col
        self.color = color


class Pill(pygame.sprite.Sprite):
    def __init__(self, x, y, col):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load("images/pill.png").convert()
        self.rect = self.image.get_rect()
        self.rect = self.rect.move(x, y)
        self.col = col
        self.score = 10


class Powerup(pygame.sprite.Sprite):
    def __init__(self, x, y, col):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load("images/pill.png").convert()
        self.image = pygame.transform.scale(self.image, (20, 20))
        self.rect = self.image.get_rect()
        self.rect = self.rect.move(x, y)
        self.col = col


class Fruit(pygame.sprite.Sprite):
    def __init__(self, x, y, col):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load("images/cherry.png").convert()
        self.rect = self.image.get_rect()
        self.rect = self.rect.move(x, y)
        self.col = col


class Text(pygame.sprite.Sprite):
    def __init__(self, size, color, position):
        pygame.sprite.Sprite.__init__(self)
        self.color = color
        self.position = position
        self.font = pygame.font.SysFont("Monaco", size)

    def update(self, hero):
        text = "SCORE: " + str(hero.score) + "    LIVES: " + str(hero.lives)

        self.image = self.font.render(str(text), 1, self.color)
        self.rect = self.image.get_rect()
        self.rect.move_ip(self.position[0] - self.rect.width / 2, self.position[1])


def blink(image, rect, screen):
    if pygame.time.get_ticks() % 1000 < 500:
        screen.blit(image, rect)


def main():
    global lose, win, superstate, intro, outro, gameplay
    screen = pygame.display.set_mode((WIN_W, WIN_H), pygame.SRCALPHA)
    pygame.display.set_caption('Pacman')

    score = Text(40, YELLOW, (WIN_W / 2, WIN_H / 1.04))

    title = pygame.image.load("images/title.png").convert_alpha()
    title_rect = title.get_rect()
    title_rect.center = (WIN_W / 2, WIN_H / 2)

    subtitle = pygame.image.load("images/clicktoplay.png").convert_alpha()
    subtitle_rect = subtitle.get_rect()
    subtitle_rect.center = (WIN_W / 2, (WIN_H / 2) + 120)

    exit = pygame.image.load("images/clicktoexit.png").convert_alpha()
    exit_rect = exit.get_rect()
    exit_rect.center = (WIN_W / 2, (WIN_H / 2) + 160)

    lost = pygame.image.load("images/gameover.png").convert_alpha()
    lost_rect = lost.get_rect()
    lost_rect.center = (WIN_W / 2, WIN_H / 2)

    won = pygame.image.load("images/win.png").convert_alpha()
    won_rect = won.get_rect()
    won_rect.center = (WIN_W / 2, WIN_H / 2)

    map = [
        "PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP",
        "P                             P",
        "P Z C C C C C C C C C C C C Z P",
        "P                             P",
        "P C PP C P  C PPP C  P C PP C P",
        "P   PP   PP    P    PP   PP   P",
        "P C PP C PP C PPP C PP C PP C P",
        "P                             P",
        "P C C C C C C C C C C C C C C P",
        "P G       PPPPPPPPPPP       H P",
        "P              P              P",
        "P C PP  C C C  P  C C C  PP C P",
        "P   PP         P         PP   P",
        "P C PP  C  PPPPPPPPP  C  PP C P",
        "P                             P",
        "P C C C C C C C C C C C C C C P",
        "P              B              P",
        "PPPPPPP C C C PPP C C C PPPPPPP",
        " T             P               ",
        "                               ",
        "PPPPPPP C C C C C C C C PPPPPPP",
        "P                             P",
        "P C C C C C PPPPPPP C C C C C P",
        "P E            P            F P",
        "P C C C P C C  P  C C P C C C P",
        "P       P      P      P       P",
        "PPPP C  PPPPPPPPPPPPPPP  C PPPP",
        "P              P              P",
        "P C C C C C C  P  C C C C C C P",
        "P     P       PPP       P     P",
        "P C PPPPP C C PPP C C PPPPP C P",
        "P                             P",
        "P C C C C C C C C C C C C C C P",
        "PPPPPPP   PPPPPPPPPPP   PPPPPPP",
        "P                             P",
        "P Z C C C C C C C C C C C C Z P",
        "P                             P",
        "PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP",
        "                               ",
        "                               ", ]

    platform_group = pygame.sprite.Group()
    pill_group = pygame.sprite.Group()
    hero_group = pygame.sprite.Group()
    score_group = pygame.sprite.Group()
    fruit_group = pygame.sprite.Group()
    enemy_group = pygame.sprite.Group()
    powerup_group = pygame.sprite.Group()

    x = y = 0
    for row in map:
        for col in row:
            if col == "P":
                p = Platform(x, y, col, 'blue')
                platform_group.add(p)
            elif col == "T":
                hero = Hero(x, y, col)
                hero_group.add(hero)
            elif col == "C":
                c = Pill(x, y, col)
                pill_group.add(c)
            elif col == "E":
                red = Enemy(x, y, "images/red.png", 'red')
                enemy_group.add(red)
            elif col == "F":
                blue = Enemy(x, y, "images/blue.png", 'blue')
                enemy_group.add(blue)
            elif col == "G":
                pink = Enemy(x, y, "images/pink.png", 'pink')
                enemy_group.add(pink)
            elif col == "H":
                orange = Enemy(x, y, "images/orange.png", 'orange')
                enemy_group.add(orange)
            elif col == "Z":
                z = Powerup(x, y, col)
                powerup_group.add(z)
            elif col == "B":
                b = Fruit(x, y, col)
                fruit_group.add(b)

            x += 32
        y += 32
        x = 0

    total_width = len(map[0]) * 32
    total_height = len(map) * 32
    camera = Camera(total_width, total_height)

    fps = 60
    score_group.add(score)

    while True:
        while intro:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:  sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN or pygame.key.get_pressed()[pygame.K_RETURN] != 0:
                    intro = False
                    gameplay = True
            screen.fill(BLACK)
            blink(subtitle, subtitle_rect, screen)
            screen.blit(title, title_rect)
            clock.tick(fps)
            pygame.display.flip()

        while gameplay:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
            hero.update(platform_group, pill_group, enemy_group, powerup_group, fruit_group)
            camera.update(hero.rect)
            enemy_group.update(platform_group, hero, hero_group)
            score.update(hero)

            screen.fill(BLACK)
            if superstate:
                for b in fruit_group:
                    screen.blit(b.image, camera.apply(b))
            for h in hero_group:
                screen.blit(h.image, camera.apply(h))
            for p in platform_group:
                screen.blit(p.image, camera.apply(p))
            for c in pill_group:
                screen.blit(c.image, camera.apply(c))
            for s in score_group:
                screen.blit(s.image, camera.apply(s))
            for e in enemy_group:
                screen.blit(e.image, camera.apply(e))
            for z in powerup_group:
                blink(z.image, camera.apply(z), screen)

            clock.tick(fps)

            pygame.display.flip()

            if len(pill_group) == 0:
                win = True
            if lose or win:
                gameplay = False
                time.sleep(2)
                outro = True

        while outro:
            screen.fill(BLACK)
            blink(exit, exit_rect, screen)
            if lose:
                screen.blit(lost, lost_rect)
            if win:
                screen.blit(won, won_rect)

            for event in pygame.event.get():
                if event.type == pygame.QUIT or event.type == pygame.MOUSEBUTTONDOWN or pygame.key.get_pressed()[pygame.K_RETURN] != 0:
                    time.sleep(1)
                    sys.exit()

            clock.tick(fps)
            pygame.display.flip()


if __name__ == "__main__":
    pygame.init()
    main()
