import pygame
import random
import math
import asyncio

pygame.init()

WIDTH = 1000
HEIGHT = 700
GRID_SIZE = 25

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("STRAWBERRY SNAKE")
clock = pygame.time.Clock()

WHITE = (255, 255, 255)
BLACK = (65, 55, 75)
PINK = (255, 145, 185)
LIGHT_PINK = (255, 225, 238)
DARK_PINK = (230, 100, 150)
PURPLE = (180, 145, 225)
DARK_PURPLE = (125, 90, 170)
LIGHT_PURPLE = (235, 220, 250)
RED = (240, 70, 100)
LIGHT_RED = (255, 135, 165)
GREEN = (160, 220, 180)
YELLOW = (255, 220, 120)
BOARD = (255, 250, 253)
GRID = (238, 225, 237)
JOYSTICK_BG = (248, 232, 245)
JOYSTICK_RING = (220, 190, 220)

HEADER_HEIGHT = 100


def get_font(size):
    return pygame.font.Font(None, size)


def get_board_size():
    margin = 18
    gap = 16
    joystick_width = 220
    board_x = margin
    board_y = HEADER_HEIGHT + margin
    aw = WIDTH - board_x - margin - joystick_width - gap
    ah = HEIGHT - board_y - margin
    bw = (aw // GRID_SIZE) * GRID_SIZE
    bh = (ah // GRID_SIZE) * GRID_SIZE
    return board_x, board_y, bw, bh


def get_joystick_rect():
    bx, by, bw, bh = get_board_size()
    area_x = bx + bw + 16
    return pygame.Rect(area_x, by, WIDTH - area_x - 18, bh)


snake = []
direction = (1, 0)
foods = []
FOOD_COUNT = 10
score = 0
best_score = 0
state = "menu"
joystick_active = False
joystick_knob_pos = None
move_timer = 0
MOVE_INTERVAL = 10


def draw_board():
    bx, by, bw, bh = get_board_size()
    rect = pygame.Rect(bx, by, bw, bh)
    pygame.draw.rect(screen, BOARD, rect, border_radius=15)
    for x in range(bx, bx + bw + 1, GRID_SIZE):
        pygame.draw.line(screen, GRID, (x, by), (x, by + bh), 1)
    for y in range(by, by + bh + 1, GRID_SIZE):
        pygame.draw.line(screen, GRID, (bx, y), (bx + bw, y), 1)
    pygame.draw.rect(screen, LIGHT_PINK, rect, 3, border_radius=15)


def draw_strawberry(x, y):
    cx = x + GRID_SIZE // 2
    cy = y + GRID_SIZE // 2
    pygame.draw.circle(screen, RED, (cx - 5, cy), 8)
    pygame.draw.circle(screen, RED, (cx + 5, cy), 8)
    pygame.draw.polygon(screen, RED, [
        (cx - 11, cy - 1),
        (cx + 11, cy - 1),
        (cx, cy + 12)
    ])
    pygame.draw.polygon(screen, GREEN, [
        (cx, cy - 8),
        (cx - 7, cy - 13),
        (cx - 2, cy - 5),
        (cx + 2, cy - 14),
        (cx + 7, cy - 6)
    ])
    pygame.draw.circle(screen, YELLOW, (cx - 5, cy), 1)
    pygame.draw.circle(screen, YELLOW, (cx + 5, cy), 1)
    pygame.draw.circle(screen, YELLOW, (cx, cy + 5), 1)


def draw_head(x, y, dx, dy):
    rect = pygame.Rect(x + 2, y + 2, GRID_SIZE - 4, GRID_SIZE - 4)
    pygame.draw.rect(screen, PINK, rect, border_radius=8)

    if dx == 1:
        e1 = (x + 16, y + 9)
        e2 = (x + 16, y + 17)
    elif dx == -1:
        e1 = (x + 9, y + 9)
        e2 = (x + 9, y + 17)
    elif dy == -1:
        e1 = (x + 9, y + 8)
        e2 = (x + 17, y + 8)
    else:
        e1 = (x + 9, y + 18)
        e2 = (x + 17, y + 18)

    pygame.draw.circle(screen, WHITE, e1, 4)
    pygame.draw.circle(screen, WHITE, e2, 4)
    pygame.draw.circle(screen, BLACK, e1, 2)
    pygame.draw.circle(screen, BLACK, e2, 2)

    pygame.draw.circle(screen, LIGHT_RED, (x + 6, y + 18), 3)
    pygame.draw.circle(screen, LIGHT_RED, (x + 19, y + 18), 3)


def draw_snake():
    for i, (x, y) in enumerate(snake):
        if i == 0:
            draw_head(x, y, direction[0], direction[1])
        else:
            c = LIGHT_PINK if i % 2 == 0 else LIGHT_PURPLE
            pygame.draw.rect(
                screen, c,
                (x + 2, y + 2, GRID_SIZE - 4, GRID_SIZE - 4),
                border_radius=7
            )


def create_food():
    bx, by, bw, bh = get_board_size()
    cols = bw // GRID_SIZE
    rows = bh // GRID_SIZE
    available = []
    for c in range(cols):
        for r in range(rows):
            x = bx + c * GRID_SIZE
            y = by + r * GRID_SIZE
            if (x, y) not in snake and (x, y) not in foods:
                available.append((x, y))
    if not available:
        return None
    return random.choice(available)


def fill_food():
    while len(foods) < FOOD_COUNT:
        f = create_food()
        if f is None:
            break
        foods.append(f)


def reset_game():
    global snake, direction, foods, score, state, move_timer
    bx, by, bw, bh = get_board_size()
    cx = bx + (bw // 2 // GRID_SIZE) * GRID_SIZE
    cy = by + (bh // 2 // GRID_SIZE) * GRID_SIZE
    snake = [
        (cx, cy),
        (cx - GRID_SIZE, cy),
        (cx - GRID_SIZE * 2, cy),
        (cx - GRID_SIZE * 3, cy)
    ]
    direction = (1, 0)
    foods = []
    score = 0
    move_timer = 0
    fill_food()
    state = "playing"


def move_snake():
    global score, best_score, state
    if not snake:
        return
    bx, by, bw, bh = get_board_size()
    hx, hy = snake[0]
    nx = hx + direction[0] * GRID_SIZE
    ny = hy + direction[1] * GRID_SIZE
    min_x = bx
    max_x = bx + bw - GRID_SIZE
    min_y = by
    max_y = by + bh - GRID_SIZE
    if nx < min_x or nx > max_x or ny < min_y or ny > max_y:
        state = "gameover"
        if score > best_score:
            best_score = score
        return
    if (nx, ny) in snake:
        state = "gameover"
        if score > best_score:
            best_score = score
        return
    snake.insert(0, (nx, ny))
    if (nx, ny) in foods:
        foods.remove((nx, ny))
        score += 1
        if score > best_score:
            best_score = score
        f = create_food()
        if f:
            foods.append(f)
    else:
        snake.pop()


def change_direction(nd):
    global direction
    if nd[0] == -direction[0] and nd[1] == -direction[1]:
        return
    direction = nd


def get_joystick_center():
    r = get_joystick_rect()
    return r.centerx, r.centery + 10


def draw_joystick_area():
    r = get_joystick_rect()
    pygame.draw.rect(screen, JOYSTICK_BG, r, border_radius=20)
    pygame.draw.rect(screen, JOYSTICK_RING, r, 3, border_radius=20)
    t = get_font(20).render("JOYSTICK", True, DARK_PURPLE)
    screen.blit(t, t.get_rect(center=(r.centerx, r.top + 30)))


def draw_joystick():
    c = get_joystick_center()
    radius = 65
    knob = 24
    pygame.draw.circle(screen, JOYSTICK_RING, c, radius + 6)
    pygame.draw.circle(screen, WHITE, c, radius)
    kp = c if joystick_knob_pos is None else joystick_knob_pos
    pygame.draw.circle(screen, DARK_PINK, kp, knob + 3)
    pygame.draw.circle(screen, PINK, kp, knob)
    pygame.draw.circle(screen, LIGHT_PINK,
                       (kp[0] - knob // 3, kp[1] - knob // 3),
                       max(3, knob // 5))


def joystick_control(pos):
    global joystick_knob_pos
    cx, cy = get_joystick_center()
    radius = 65
    knob = 24
    dx = pos[0] - cx
    dy = pos[1] - cy
    dist = math.sqrt(dx * dx + dy * dy)
    maxd = radius - knob
    if dist > maxd and dist > 0:
        dx = dx / dist * maxd
        dy = dy / dist * maxd
    joystick_knob_pos = (int(cx + dx), int(cy + dy))
    if dist < 15:
        return
    if abs(dx) > abs(dy):
        change_direction((1, 0) if dx > 0 else (-1, 0))
    else:
        change_direction((0, 1) if dy > 0 else (0, -1))


def release_joystick():
    global joystick_active, joystick_knob_pos
    joystick_active = False
    joystick_knob_pos = None


def draw_header():
    pygame.draw.rect(screen, LIGHT_PINK, (0, 0, WIDTH, HEADER_HEIGHT))
    title = get_font(30).render("STRAWBERRY SNAKE GAME", True, DARK_PURPLE)
    screen.blit(title, (20, 12))

    margin = 18
    gap = 6
    bw = max(90, min(150, (WIDTH - margin * 2 - gap * 3) // 4))
    total = bw * 4 + gap * 3
    sx = (WIDTH - total) // 2
    sy = HEADER_HEIGHT - 46

    stats = [
        ("SCORE", str(score)),
        ("BEST", str(best_score)),
        ("FOOD", str(len(foods))),
        ("STATE", state.upper())
    ]
    for i, (lbl, val) in enumerate(stats):
        x = sx + i * (bw + gap)
        r = pygame.Rect(x, sy, bw, 34)
        pygame.draw.rect(screen, WHITE, r, border_radius=10)
        pygame.draw.rect(screen, PURPLE, r, 2, border_radius=10)
        lt = get_font(16).render(lbl, True, DARK_PURPLE)
        screen.blit(lt, lt.get_rect(midleft=(r.left + 8, r.centery)))
        vt = get_font(16).render(val, True, DARK_PINK)
        screen.blit(vt, vt.get_rect(midright=(r.right - 8, r.centery)))


def draw_menu():
    screen.fill(LIGHT_PURPLE)
    t1 = get_font(70).render("STRAWBERRY", True, DARK_PURPLE)
    screen.blit(t1, t1.get_rect(center=(WIDTH // 2, 150)))
    t2 = get_font(50).render("SNAKE GAME", True, DARK_PINK)
    screen.blit(t2, t2.get_rect(center=(WIDTH // 2, 210)))

    draw_strawberry(WIDTH // 2 - 25, 260)
    draw_strawberry(WIDTH // 2 - 100, 260)
    draw_strawberry(WIDTH // 2 + 50, 260)

    pr = pygame.Rect(0, 0, 300, 65)
    pr.center = (WIDTH // 2, 400)
    pygame.draw.rect(screen, PINK, pr, border_radius=20)
    pygame.draw.rect(screen, DARK_PINK, pr, 3, border_radius=20)
    pt = get_font(32).render("PLAY", True, WHITE)
    screen.blit(pt, pt.get_rect(center=pr.center))

    qr = pygame.Rect(0, 0, 300, 65)
    qr.center = (WIDTH // 2, 490)
    pygame.draw.rect(screen, DARK_PURPLE, qr, border_radius=20)
    qt = get_font(32).render("QUIT", True, WHITE)
    screen.blit(qt, qt.get_rect(center=qr.center))

    c = get_font(22).render("WASD / ARROW KEYS / JOYSTICK / TOUCH",
                            True, DARK_PURPLE)
    screen.blit(c, c.get_rect(center=(WIDTH // 2, 600)))

    return pr, qr


def draw_pause():
    ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    ov.fill((80, 50, 90, 150))
    screen.blit(ov, (0, 0))
    t = get_font(60).render("PAUSED", True, WHITE)
    screen.blit(t, t.get_rect(center=(WIDTH // 2, 180)))

    rr = pygame.Rect(0, 0, 280, 55)
    rr.center = (WIDTH // 2, 300)
    pygame.draw.rect(screen, PINK, rr, border_radius=18)
    rt = get_font(28).render("RESUME", True, WHITE)
    screen.blit(rt, rt.get_rect(center=rr.center))

    rs = pygame.Rect(0, 0, 280, 55)
    rs.center = (WIDTH // 2, 380)
    pygame.draw.rect(screen, PURPLE, rs, border_radius=18)
    st = get_font(28).render("RESTART", True, WHITE)
    screen.blit(st, st.get_rect(center=rs.center))

    mr = pygame.Rect(0, 0, 280, 55)
    mr.center = (WIDTH // 2, 460)
    pygame.draw.rect(screen, DARK_PURPLE, mr, border_radius=18)
    mt = get_font(28).render("MENU", True, WHITE)
    screen.blit(mt, mt.get_rect(center=mr.center))

    return rr, rs, mr


def draw_gameover():
    ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    ov.fill((80, 50, 90, 160))
    screen.blit(ov, (0, 0))
    t = get_font(70).render("GAME OVER", True, WHITE)
    screen.blit(t, t.get_rect(center=(WIDTH // 2, 150)))
    sc = get_font(34).render("Score : " + str(score), True, WHITE)
    screen.blit(sc, sc.get_rect(center=(WIDTH // 2, 240)))
    bs = get_font(34).render("Best : " + str(best_score), True, YELLOW)
    screen.blit(bs, bs.get_rect(center=(WIDTH // 2, 290)))

    rr = pygame.Rect(0, 0, 280, 55)
    rr.center = (WIDTH // 2, 400)
    pygame.draw.rect(screen, PINK, rr, border_radius=18)
    rt = get_font(28).render("RESTART", True, WHITE)
    screen.blit(rt, rt.get_rect(center=rr.center))

    mr = pygame.Rect(0, 0, 280, 55)
    mr.center = (WIDTH // 2, 480)
    pygame.draw.rect(screen, PURPLE, mr, border_radius=18)
    mt = get_font(28).render("MENU", True, WHITE)
    screen.blit(mt, mt.get_rect(center=mr.center))

    return rr, mr


async def main():
    global state, joystick_active, move_timer

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    return

                if state == "playing":
                    if event.key in (pygame.K_UP, pygame.K_w):
                        change_direction((0, -1))
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        change_direction((0, 1))
                    elif event.key in (pygame.K_LEFT, pygame.K_a):
                        change_direction((-1, 0))
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        change_direction((1, 0))
                    elif event.key == pygame.K_p:
                        state = "paused"
                elif state == "paused":
                    if event.key == pygame.K_p:
                        state = "playing"

            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos
                if state == "menu":
                    pr, qr = draw_menu()
                    if pr.collidepoint(pos):
                        reset_game()
                    elif qr.collidepoint(pos):
                        pygame.quit()
                        return
                elif state == "playing":
                    if get_joystick_rect().collidepoint(pos):
                        joystick_active = True
                        joystick_control(pos)
                elif state == "paused":
                    rr, rs, mr = draw_pause()
                    if rr.collidepoint(pos):
                        state = "playing"
                    elif rs.collidepoint(pos):
                        reset_game()
                    elif mr.collidepoint(pos):
                        state = "menu"
                elif state == "gameover":
                    rr, mr = draw_gameover()
                    if rr.collidepoint(pos):
                        reset_game()
                    elif mr.collidepoint(pos):
                        state = "menu"

            if event.type == pygame.MOUSEMOTION:
                if state == "playing" and joystick_active:
                    joystick_control(event.pos)

            if event.type == pygame.MOUSEBUTTONUP:
                release_joystick()

        if state == "playing":
            move_timer += 1
            if move_timer >= MOVE_INTERVAL:
                move_timer = 0
                move_snake()

        if state == "menu":
            draw_menu()
        elif state == "playing":
            screen.fill(WHITE)
            draw_header()
            draw_board()
            draw_joystick_area()
            for fd in foods:
                draw_strawberry(fd[0], fd[1])
            draw_snake()
            draw_joystick()
        elif state == "paused":
            screen.fill(WHITE)
            draw_header()
            draw_board()
            draw_joystick_area()
            for fd in foods:
                draw_strawberry(fd[0], fd[1])
            draw_snake()
            draw_joystick()
            draw_pause()
        elif state == "gameover":
            screen.fill(WHITE)
            draw_header()
            draw_board()
            draw_joystick_area()
            for fd in foods:
                draw_strawberry(fd[0], fd[1])
            draw_snake()
            draw_joystick()
            draw_gameover()

        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)


asyncio.run(main())