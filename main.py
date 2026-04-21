import pygame
import random
import os
import time
import json
import math

# --- INITIALISIERUNG ---
pygame.init()

# Vollbild & System-Info
info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Whac-A-Mole: Character Edition")

clock = pygame.time.Clock()
pygame.mouse.set_visible(False)

# --- FARBPALETTE ---
BG_COLOR = (25, 25, 25)
NAZI_BG_COLOR = (70, 70, 75)
POLITIKER_BG_COLOR = (130, 130, 135)
HOLE_COLOR = (45, 45, 45)
GULLY_BASE_COLOR = (30, 30, 32)
GRID_COLOR = (60, 60, 60)
TEXT_COLOR = (240, 240, 240)
ACCENT_COLOR = (180, 180, 180)
PANEL_COLOR = (30, 30, 30)
BUTTON_COLOR = (50, 50, 50)
BUTTON_HOVER = (80, 80, 80)

COLOR_WHITE = (255, 255, 255)
COLOR_GREEN = (0, 255, 0)
COLOR_RED = (255, 0, 0)
COLOR_GOLD = (255, 215, 0)

# Schriften
font_main = pygame.font.SysFont("Skia", int(HEIGHT * 0.05), bold=False)
font_ui = pygame.font.SysFont("Skia", int(HEIGHT * 0.04))
font_big = pygame.font.SysFont("Skia", int(HEIGHT * 0.1), bold=False)
font_small = pygame.font.SysFont("Skia", int(HEIGHT * 0.03))
title_font = pygame.font.SysFont("Skia", int(HEIGHT * 0.08), bold=False)
font_timer_bg = pygame.font.SysFont("Skia", int(HEIGHT * 0.05), bold=False)

# Einstellungen
GAME_TIME = 30
TRANSITION_TIME = 0.08
TARGET_SIZE = int(HEIGHT * 0.18)
HAMMER_DURATION = 0.12
HIGHSCORE_FILE = "highscores.json"

# Theme auf "Nazi" geändert
THEMES = {
    "Nazi": "Themes/Nazis",
    "Politiker": "Themes/Politiker",
}


# --- BILDER LADEN ---
def load_theme_images(folder, target_height):
    images = []
    if not os.path.exists(folder):
        return images
    forbidden_files = ["pult.png", "faust_revolution.png"]
    for file in os.listdir(folder):
        if file.lower().endswith(".png") and file.lower() not in forbidden_files:
            try:
                img = pygame.image.load(os.path.join(folder, file)).convert_alpha()
                name = os.path.splitext(file)[0].replace("_", " ").title()
                rect = img.get_bounding_rect()
                img = img.subsurface(rect)
                scale = target_height / img.get_height()
                img = pygame.transform.smoothscale(img, (int(img.get_width() * scale), int(target_height)))
                images.append((img, name))
            except:
                continue
    return images


# --- HIGHSCORE SYSTEM ---
def load_highscores():
    if not os.path.exists(HIGHSCORE_FILE):
        return {"overall": 0, "themes": {}}
    try:
        with open(HIGHSCORE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "overall" not in data: data["overall"] = 0
        if "themes" not in data: data["themes"] = {}
        return data
    except:
        return {"overall": 0, "themes": {}}


def save_highscores(data):
    with open(HIGHSCORE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# --- UI ELEMENTE ---
class Button:
    def __init__(self, rect, text):
        self.rect = pygame.Rect(rect);
        self.text = text

    def draw(self, surface):
        c = BUTTON_HOVER if self.rect.collidepoint(pygame.mouse.get_pos()) else BUTTON_COLOR
        pygame.draw.rect(surface, c, self.rect, border_radius=12)
        pygame.draw.rect(surface, (255, 255, 255), self.rect, 2, border_radius=12)
        txt = font_small.render(self.text, True, (255, 255, 255))
        surface.blit(txt, txt.get_rect(center=self.rect.center))

    def is_clicked(self, event):
        return event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos)


def draw_text_center(text, text_font, color, y):
    rendered = text_font.render(text, True, color)
    screen.blit(rendered, rendered.get_rect(center=(WIDTH // 2, y)))


def draw_flame(surface, x, y, size, streak, bonus):
    f_width, f_height = int(size * 2.5), int(size * 3.5)
    flame_surf = pygame.Surface((f_width, f_height), pygame.SRCALPHA)
    cx, cy = f_width // 2, f_height - int(size * 1.2)
    pulse = math.sin(time.time() * 15) * (size * 0.05) if streak > 0 else 0
    if streak >= 4:
        colors = [(255, 50, 0), (255, 120, 0), (255, 220, 0)]
    elif streak > 0:
        colors = [(200, 50, 0), (200, 100, 0), (200, 150, 0)]
    else:
        colors = [(80, 80, 80), (110, 110, 110), (140, 140, 140)]
    layers = [(colors[0], size + pulse, size * 1.8 + pulse), (colors[1], size * 0.7 + pulse, size * 1.3 + pulse),
              (colors[2], size * 0.4 + pulse, size * 0.8 + pulse)]
    for color, w, h in layers:
        pygame.draw.circle(flame_surf, color, (int(cx), int(cy)), int(w))
        points = [(cx, cy - h), (cx - w * 0.9, cy), (cx + w * 0.9, cy)]
        pygame.draw.polygon(flame_surf, color, points)
    txt_str = str(streak)
    txt = font_main.render(txt_str, True, (255, 255, 255) if streak < 4 else (0, 0, 0))
    flame_surf.blit(txt, txt.get_rect(center=(cx, cy)))
    rect = flame_surf.get_rect(center=(x, y))
    surface.blit(flame_surf, rect)
    if bonus > 0:
        b_txt = font_main.render(f"(+{bonus})", True, COLOR_GREEN)
        surface.blit(b_txt, b_txt.get_rect(midleft=(rect.right + 5, y)))


# --- SOUND SYSTEM ---
pygame.mixer.init()


def load_sound_category(folder_name):
    sounds = []
    path = os.path.join("Sounds", folder_name)
    if os.path.exists(path):
        for file in os.listdir(path):
            if file.lower().endswith(".wav"):
                try:
                    sounds.append(pygame.mixer.Sound(os.path.join(path, file)))
                except:
                    continue
    return sounds


SND_HITS, SND_MISSES, SND_SPECIAL, SND_PENALTY = load_sound_category("Hits"), load_sound_category(
    "Misses"), load_sound_category("Special"), load_sound_category("Bomb")
SND_TRUMP = load_sound_category("trumpfx")
SND_KANYE = load_sound_category("kanyefx")
SND_POWERUP = load_sound_category("powerupfx")

SND_BREATH = None
try:
    SND_BREATH = pygame.mixer.Sound(os.path.join("Sounds", "breath.wav"))
    SND_BREATH.set_volume(0.7)
except:
    pass

for s in SND_TRUMP: s.set_volume(0.8)
for s in SND_KANYE: s.set_volume(0.6)
for s in SND_POWERUP: s.set_volume(0.9)


def play_variant(sound_list):
    if sound_list: random.choice(sound_list).play()


def play_bg_music(filename, volume=0.5):
    """Stoppt aktuelle Musik und startet einen neuen Track in Endlosschleife."""
    try:
        pygame.mixer.music.stop()
        path = os.path.join("Sounds", filename)
        if os.path.exists(path):
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play(-1)
    except Exception as e:
        print(f"Musikfehler: {e}")


# --- PARTIKEL SYSTEM ---
class Particle:
    def __init__(self, x, y, color):
        self.x, self.y = x, y
        self.vx, self.vy = random.uniform(-4, 4), random.uniform(-10, -2)
        self.life, self.color, self.size = 1.0, color, random.randint(3, 6)
        self.is_dirt = False  # Flag für klebenden Dreck

    def update(self):
        if not self.is_dirt:
            self.x += self.vx;
            self.y += self.vy;
            self.vy += 0.4;
            self.life -= 0.025
        else:
            # Dreck bewegt sich nicht und fällt nicht, er fadet nur aus
            self.life -= 0.05

    def draw(self, surface):
        if self.life > 0:
            p_surf = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
            pygame.draw.circle(p_surf, (*self.color, int(self.life * 255)), (self.size, self.size), self.size)
            surface.blit(p_surf, (self.x - self.size, self.y - self.size))


# --- GULLY DESIGN ---
def draw_gully_base(surface, pos, off_x, off_y):
    hx, hy = pos;
    r_w, r_h = WIDTH // 5, HEIGHT // 12.5
    # Grauer Balken / Umrandung entfernt!
    pygame.draw.ellipse(surface, GULLY_BASE_COLOR,
                        (hx - r_w // 2 + off_x + 10, hy - r_h // 2 + off_y + 5, r_w - 20, r_h - 10))


def draw_gully_lid(surface, pos, off_x, off_y, slide=0):
    hx, hy = pos;
    r_w, r_h, depth = WIDTH // 5, HEIGHT // 12.5, 8
    lid_surf = pygame.Surface((r_w, r_h + depth), pygame.SRCALPHA)
    pygame.draw.ellipse(lid_surf, (60, 60, 65), (0, depth, r_w, r_h))
    pygame.draw.rect(lid_surf, (60, 60, 65), (0, depth // 2, r_w, depth))
    pygame.draw.ellipse(lid_surf, (110, 110, 115), (0, 0, r_w, r_h))
    pygame.draw.ellipse(lid_surf, (200, 200, 205), (0, 0, r_w, r_h), 2)
    for i in range(1, 6):
        pygame.draw.line(lid_surf, (80, 80, 85), (i * (r_w // 6), r_h * 0.05), (i * (r_w // 6), r_h * 0.95), 2)
        pygame.draw.line(lid_surf, (80, 80, 85), (r_w * 0.05, i * (r_h // 6)), (r_w * 0.95, i * (r_h // 6)), 2)
    surface.blit(lid_surf, (hx - r_w // 2 + off_x, hy - r_h // 2 + off_y - slide))


# --- HAMMER DESIGN & EVOLUTION ---
def draw_hammer(surface, angle, streak, selected_theme, scale=1.0):
    mx, my = pygame.mouse.get_pos()
    s = int(HEIGHT * 0.18 * scale)
    h_surf = pygame.Surface((s * 3, s * 3), pygame.SRCALPHA);
    off = s
    x, y, w, h, d = s * 0.25 + off, s * 0.2 + off, s * 0.5, s * 0.3, s * 0.08
    dx, dy = d, -d

    if streak >= 7:
        C_M, C_S, C_T, C_ST = (40, 40, 45), (20, 20, 25), (60, 60, 70), (30, 30, 35);
        glow_color = (255, 100, 0)
    elif streak >= 4:
        C_M, C_S, C_T, C_ST = (60, 20, 20), (40, 10, 10), (90, 30, 30), (30, 10, 10)
    else:
        if selected_theme == "Politiker":
            C_M, C_S, C_T, C_ST = (80, 40, 15), (50, 25, 10), (110, 60, 30), (40, 20, 5)
        else:
            C_M, C_S, C_T, C_ST = (110, 110, 110), (80, 80, 80), (140, 140, 140), (50, 50, 50)

    show_aura = streak in [2, 3, 5, 6, 8, 9] or streak >= 10
    show_blitze = streak in [3, 6, 9] or streak >= 10
    if streak >= 10: angle = (time.time() * 2000) % 360

    if show_aura:
        sl = streak - 1;
        cx, cy = int(x + w / 2), int(y + h / 2);
        ar = int((w * 0.8) + (math.fabs(math.sin(time.time() * 10)) * 8))
        pygame.draw.circle(h_surf, (255, 215, 0, 80), (cx, cy), ar)
        if show_blitze:
            for _ in range(random.randint(2, 4)):
                ex, ey = cx + random.randint(-ar, ar), cy + random.randint(-ar, ar)
                pygame.draw.line(h_surf, (255, 255, 255), (cx, cy), (ex, ey), 1)

    pygame.draw.rect(h_surf, C_ST, (s * 0.45 + off, s * 0.4 + off, s * 0.1, s * 0.5), border_radius=5)
    pygame.draw.polygon(h_surf, C_T, [(x, y), (x + w, y), (x + w + dx, y + dy), (x + dx, y + dy)])
    pygame.draw.polygon(h_surf, C_S, [(x + w, y), (x + w + dx, y + dy), (x + w + dx, y + h + dy), (x + w, y + h)])
    pygame.draw.rect(h_surf, C_M, (x, y, w, h), border_radius=3)
    if 4 <= streak < 7:
        pygame.draw.rect(h_surf, COLOR_GOLD, (x + w * 0.4, y, w * 0.2, h))
    elif streak >= 7:
        pygame.draw.rect(h_surf, glow_color, (x + 2, y + 2, w - 4, h - 4), 2)
        pygame.draw.line(h_surf, glow_color, (x, y + h // 2), (x + w, y + h // 2), 2)

    rot = pygame.transform.rotate(h_surf, angle)
    surface.blit(rot, rot.get_rect(center=(mx + s * 0.2, my - s * 0.2)))


# --- ADERN GENERIERUNG ---
def create_vein_surface(width, height):
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    for _ in range(60):
        if random.random() < 0.5:
            x = random.choice([0, width])
            y = random.randint(0, height)
        else:
            x = random.randint(0, width)
            y = random.choice([0, height])

        cx, cy = width // 2, height // 2
        px, py = x, y
        segments = random.randint(5, 12)
        length = random.randint(100, 400)

        for i in range(segments):
            dx, dy = cx - px, cy - py
            dist = math.hypot(dx, dy)
            if dist == 0: break
            step = length / segments
            nx = px + (dx / dist) * step + random.randint(-30, 30)
            ny = py + (dy / dist) * step + random.randint(-30, 30)
            w_line = max(1, int(5 * (1 - i / segments)))
            pygame.draw.line(surf, (150, 0, 0, 180), (px, py), (nx, ny), w_line)
            px, py = nx, ny
    return surf


# --- MENÜ ---
def run_menu(highscores):
    play_bg_music("menusound.wav", 0.4)
    pygame.mouse.set_visible(True)
    base_dir = os.path.dirname(os.path.abspath(__file__));
    current_mode = "Classic"

    btn_mode = Button((WIDTH // 2 - 150, HEIGHT - 100, 300, 70), f"MODUS: {current_mode.upper()}")

    while True:
        mx, my = pygame.mouse.get_pos();

        hover_color = (60, 60, 60) if current_mode == "Classic" else (90, 15, 15)
        l_bg, r_bg = (hover_color, (0, 0, 0)) if mx < WIDTH // 2 else ((0, 0, 0), hover_color)

        pygame.draw.rect(screen, l_bg, (0, 0, WIDTH // 2, HEIGHT));
        pygame.draw.rect(screen, r_bg, (WIDTH // 2, 0, WIDTH // 2, HEIGHT));
        pygame.draw.line(screen, GRID_COLOR, (WIDTH // 2, 0), (WIDTH // 2, HEIGHT), 4)
        draw_text_center("WHAC A", title_font, TEXT_COLOR, HEIGHT * 0.15);
        draw_text_center("Wen willst du boxen?", font_main, ACCENT_COLOR, HEIGHT * 0.25)

        for side, label, hs_key_base, x_pos in [("links", "NAZI", "Nazi", WIDTH // 4),
                                                ("rechts", "POLITIKER", "Politiker", 3 * WIDTH // 4)]:
            lbl = font_big.render(label, True, TEXT_COLOR);
            screen.blit(lbl, lbl.get_rect(center=(x_pos, HEIGHT // 2)))

            hs_key = hs_key_base if current_mode == "Classic" else f"Endless_{hs_key_base}"
            hs = font_main.render(f"Best ({current_mode}): {highscores['themes'].get(hs_key, 0)}", True, ACCENT_COLOR);
            screen.blit(hs, hs.get_rect(center=(x_pos, HEIGHT // 2 + 100)))

        btn_mode.text = f"MODUS: {current_mode.upper()}"
        btn_mode.draw(screen)

        pygame.display.flip();
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT: return None
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: return None
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if btn_mode.rect.collidepoint(event.pos):
                    current_mode = "Endless" if current_mode == "Classic" else "Classic"
                else:
                    theme = "Nazi" if event.pos[0] < WIDTH // 2 else "Politiker"
                    return (theme, current_mode)


# --- HAUPTSPIEL ---
def run_game(selected_theme, game_mode="Classic"):
    play_bg_music("soundtrack.wav", 0.5)
    global GAME_TIME
    pygame.mouse.set_visible(False)
    base_dir = os.path.dirname(os.path.abspath(__file__));

    img_pult, img_fist = None, None
    bg_image = None

    if selected_theme == "Politiker":
        p_path = os.path.join(base_dir, "Themes", "Politiker", "pult.png")
        if os.path.exists(p_path):
            raw = pygame.image.load(p_path).convert_alpha()
            p_scale = ((WIDTH // 5) * 0.825) / raw.get_width()
            img_pult = pygame.transform.smoothscale(raw, (int(raw.get_width() * p_scale * 1.25),
                                                          int(raw.get_height() * p_scale)))

        # Hintergrundbild Politiker
        bg_path = os.path.join(base_dir, "Themes", "Politiker", "Bundestag.jpg")
        if os.path.exists(bg_path):
            raw_bg = pygame.image.load(bg_path).convert()
            bg_image = pygame.transform.smoothscale(raw_bg, (WIDTH, HEIGHT))
            bg_image.set_alpha(int(255 * 0.20))

    elif selected_theme == "Nazi":
        # Hintergrundbild Nazi
        bg_path = os.path.join(base_dir, "Themes", "Nazis", "Nazi_hintergrund.jpg")
        if os.path.exists(bg_path):
            raw_bg = pygame.image.load(bg_path).convert()
            bg_image = pygame.transform.smoothscale(raw_bg, (WIDTH, HEIGHT))
            bg_image.set_alpha(int(255 * 0.50))

    fist_path = os.path.join(base_dir, "Themes", "Politiker", "Faust_revolution.png")
    if os.path.exists(fist_path):
        rf = pygame.image.load(fist_path).convert_alpha();
        img_fist = pygame.transform.smoothscale(rf,
                                                (int(rf.get_width() * (TARGET_SIZE / rf.get_height())), TARGET_SIZE))

    theme_base = THEMES[selected_theme]
    imgs = {
        "white": load_theme_images(os.path.join(theme_base, "Schlecht"), TARGET_SIZE) + load_theme_images(theme_base,
                                                                                                          TARGET_SIZE),
        "red": load_theme_images(os.path.join(theme_base, "Gut"), TARGET_SIZE),
        "green": load_theme_images(os.path.join(theme_base, "Bonus"), TARGET_SIZE)}

    holes = [
        {'pos': (c * (WIDTH // 4) + (WIDTH // 8), r * (HEIGHT // 2) + (HEIGHT // 4) + 20), 'row': r, 'lid_surf': None}
        for r in range(2) for c in range(4)]
    if selected_theme == "Nazi":
        for h in holes: h['lid_surf'] = pygame.Surface((WIDTH // 5, (HEIGHT // 12.5) + 8), pygame.SRCALPHA)

    clouds = []
    active_flashes, blood_splatters = [], []
    score, streak, max_streak, total_swings, total_hits, red_hits, hit_counts = 0, 0, 0, 0, 0, 0, {}
    start_time, acc_pause, game_paused, pause_t = time.time(), 0, False, 0;
    active_moles, particles, impact_effects = [], [], []
    next_spawn, shake_amount, is_swinging, swing_start = time.time(), 0, False, 0;
    power_timers = {"freeze": 0, "big": 0, "double": 0}
    NAZI_Q = ["Hau ab!", "Nix da!", "Zurück in den Gully!", "Verpiss dich!", "Klappe zu, Nazi tot"];
    POLI_Q = ["Abgewählt!", "Wahlversprechen!", "Rücktritt!"]
    breath_playing = False

    stress_level = 0.0
    time_survived = 0.0

    # Ader-Surface einmalig initialisieren
    vein_surf = create_vein_surface(WIDTH, HEIGHT)

    while True:
        clock.tick(60);
        now = pause_t if game_paused else time.time() - acc_pause

        if game_mode == "Classic":
            time_left = max(0, int(GAME_TIME - (now - start_time)))
            if time_left <= 0:
                if SND_BREATH: SND_BREATH.stop()
                return {"score": score, "swings": total_swings, "hits": total_hits, "red_hits": red_hits,
                        "max_streak": max_streak, "counts": hit_counts, "mode": game_mode, "time": GAME_TIME}
            difficulty = 1.0 - (time_left / GAME_TIME)
        else:  # Endless Modus
            time_survived = now - start_time
            time_left = int(time_survived)
            difficulty = min(1.0, time_survived / 120.0)

            if not game_paused:
                stress_rate = 2.0 + (difficulty * 13.0)
                stress_level += (stress_rate / 60.0)
                if stress_level >= 100.0:
                    if SND_BREATH: SND_BREATH.stop()
                    return {"score": score, "swings": total_swings, "hits": total_hits, "red_hits": red_hits,
                            "max_streak": max_streak, "counts": hit_counts, "mode": game_mode, "time": time_survived}

        if SND_BREATH:
            if streak >= 4 and not breath_playing:
                SND_BREATH.play(-1);
                breath_playing = True
            elif streak < 4 and breath_playing:
                SND_BREATH.stop();
                breath_playing = False

        if not game_paused:
            if is_swinging and now - swing_start > HAMMER_DURATION: is_swinging = False
            max_simul = 1 if difficulty < 0.4 else (2 if difficulty < 0.8 else 3)
            if len(active_moles) < max_simul and now >= next_spawn:
                idx = random.randint(0, 7)
                if not any(m['idx'] == idx for m in active_moles):
                    r = random.random();
                    m_type = "gold" if r < 0.05 else ("red" if r < 0.15 else ("green" if r < 0.35 else "white"))
                    choice = random.choice(imgs[m_type]) if (m_type != "gold" and imgs[m_type]) else (None, "Power Up")
                    active_moles.append(
                        {'idx': idx, 'type': m_type, 'img': choice[0], 'name': choice[1], 'spawn_t': now,
                         'dur': random.uniform(0.8, 1.1) - (difficulty * 0.15), 'hit': False})
                    next_spawn = now + random.uniform(0.2, 0.6)
            for c in clouds:
                c['x'] += c['v']
                if c['x'] > WIDTH: c['x'] = -c['w']
            active_flashes = [f for f in active_flashes if now - f['t'] < 0.1]
            if streak < 15: blood_splatters = []
            freeze_active = power_timers["freeze"] > now
            for m in active_moles[:]:
                if freeze_active:
                    if (now - m['spawn_t']) < TRANSITION_TIME:
                        m['spawn_t'] -= 2 / 60
                    else:
                        m['spawn_t'] += 1 / 60
                if not m['hit'] and now - m['spawn_t'] > m['dur']:
                    if game_mode == "Endless" and m['type'] not in ["red", "gold"]:
                        stress_level = min(100.0, stress_level + 3.0)
                    active_moles.remove(m)
            for p in particles[:]: p.update()
            particles = [p for p in particles if p.life > 0]

        off_x, off_y = (random.randint(-shake_amount, shake_amount),
                        random.randint(-shake_amount, shake_amount)) if shake_amount > 0 else (0, 0)
        if shake_amount > 0 and not game_paused: shake_amount -= 2
        screen.fill(NAZI_BG_COLOR if selected_theme == "Nazi" else (
            POLITIKER_BG_COLOR if selected_theme == "Politiker" else BG_COLOR))

        # Hintergrundbild zeichnen falls vorhanden
        if bg_image:
            screen.blit(bg_image, (0, 0))

        if selected_theme == "Nazi":
            # GESTRICHELTE LINIE (Horizontal, Mitte)
            l_y = HEIGHT // 2
            l_w = 40
            l_h = 10
            l_s = 60
            for l_x in range(0, WIDTH, l_s):
                pygame.draw.rect(screen, COLOR_WHITE, (l_x, l_y - l_h // 2, l_w, l_h))

            for h in holes: draw_gully_base(screen, h['pos'], off_x, off_y)
        elif selected_theme != "Politiker":
            for h in holes: pygame.draw.ellipse(screen, HOLE_COLOR,
                                                (h['pos'][0] - WIDTH // 10 + off_x, h['pos'][1] - HEIGHT // 25 + off_y,
                                                 WIDTH // 5, HEIGHT // 12.5))

        for b in blood_splatters:
            pygame.draw.circle(screen, (130, 0, 0), b['p'], b['r'])
            if len(b['pts']) > 2: pygame.draw.polygon(screen, (130, 0, 0), b['pts'])

        # UI & Zeit Zeichnen
        if game_mode == "Endless":
            bar_w = WIDTH * 0.6
            bar_h = 20
            bar_x = (WIDTH - bar_w) // 2
            bar_y = HEIGHT * 0.05
            pygame.draw.rect(screen, (50, 50, 50), (bar_x, bar_y, bar_w, bar_h), border_radius=10)
            fill_w = (stress_level / 100.0) * bar_w
            r_c = min(255, int((stress_level / 50) * 255))
            g_c = min(255, int(((100 - stress_level) / 50) * 255))
            if fill_w > 0:
                pygame.draw.rect(screen, (r_c, g_c, 0), (bar_x, bar_y, fill_w, bar_h), border_radius=10)
            pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, bar_w, bar_h), 2, border_radius=10)

            bg_time = font_timer_bg.render(f"{time_left}s", True, (255, 255, 255));
        else:
            bg_time = font_timer_bg.render(str(time_left), True, (255, 255, 255));

        screen.blit(bg_time, bg_time.get_rect(center=(WIDTH // 2, int(HEIGHT * 0.92))))

        draw_text_center(selected_theme.upper(), font_main, TEXT_COLOR, 110);
        draw_text_center(str(score), font_main, TEXT_COLOR, 160)

        for m in active_moles:
            h = holes[m['idx']];
            prog = (now - m['spawn_t']) / TRANSITION_TIME if (now - m['spawn_t']) < TRANSITION_TIME else (
                1.0 if (now - m['spawn_t']) < m['dur'] - TRANSITION_TIME else max(0, (
                        m['dur'] - (now - m['spawn_t'])) / TRANSITION_TIME))
            rise = int((1.0 - prog) * TARGET_SIZE);
            clip = pygame.Rect(h['pos'][0] - WIDTH // 8, 0 if h['row'] == 0 else HEIGHT // 2, WIDTH // 4,
                               h['pos'][1] if h['row'] == 0 else h['pos'][1] - HEIGHT // 2)
            if h['row'] == 1: clip = pygame.Rect(h['pos'][0] - WIDTH // 8, HEIGHT // 2, WIDTH // 4,
                                                 h['pos'][1] - HEIGHT // 2)
            old_clip = screen.get_clip();
            screen.set_clip(clip)
            if m['type'] == "gold" and img_fist:
                screen.blit(img_fist, img_fist.get_rect(centerx=h['pos'][0] + off_x, bottom=h['pos'][1] + rise + off_y))
            elif m['img']:
                img = pygame.transform.smoothscale(m['img'],
                                                   (int(m['img'].get_width() * 1.3), int(TARGET_SIZE * 0.5))) if m[
                    'hit'] else m['img']
                screen.blit(img, img.get_rect(centerx=h['pos'][0] + off_x, bottom=h['pos'][1] + rise + off_y + (
                    10 if selected_theme == "Politiker" else 0)))
            screen.set_clip(old_clip)

        if selected_theme == "Nazi":
            for idx, h in enumerate(holes):
                slide = 0;
                active_m = next((m for m in active_moles if m['idx'] == idx), None)
                if active_m:
                    m_p = (now - active_m['spawn_t']) / TRANSITION_TIME if (now - active_m[
                        'spawn_t']) < TRANSITION_TIME else (
                        1.0 if (now - active_m['spawn_t']) < active_m['dur'] - TRANSITION_TIME else max(0, (
                                active_m['dur'] - (now - active_m['spawn_t'])) / TRANSITION_TIME))
                    slide = int(int((HEIGHT // 12.5) * 2.5) * min(1.0, m_p * 2.0))

                # CLIPPING ENTFERNT: Verhindert den waagerechten grauen Balken!
                draw_gully_lid(screen, h['pos'], off_x, off_y, slide);

        if selected_theme == "Politiker" and img_pult:
            for h in holes: screen.blit(img_pult, img_pult.get_rect(centerx=h['pos'][0] + off_x, bottom=(HEIGHT // 2 if
                                                                                                         h[
                                                                                                             'row'] == 0 else HEIGHT) + off_y + 45))

        for f in active_flashes:
            flash_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA);
            alpha = int(200 * (1 - (now - f['t']) / 0.1))
            pygame.draw.circle(flash_surf, (255, 255, 255, alpha), f['p'], f['r']);
            screen.blit(flash_surf, (0, 0))

        for p in particles: p.draw(screen)
        draw_flame(screen, WIDTH // 2, HEIGHT // 2, min(HEIGHT * 0.1, HEIGHT * 0.03 + (streak * HEIGHT * 0.003)),
                   streak, streak - 3 if streak >= 4 else 0)
        h_s = 1.5 if power_timers["big"] > now else 1.0;
        hammer_a = math.sin(((now - swing_start) / HAMMER_DURATION) * math.pi) * 80 if is_swinging else 0
        draw_hammer(screen, hammer_a, streak, selected_theme, h_s)

        if streak > 0:
            fade_alpha = min(streak * 12, 180);
            fade_size = min(streak * 10, 300);
            fade_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            for i in range(0, fade_size, 4):
                current_alpha = int(fade_alpha * (1 - i / fade_size));
                pygame.draw.rect(fade_surf, (220, 0, 0, current_alpha), (i, i, WIDTH - 2 * i, HEIGHT - 2 * i), 4)

            # --- Adern blitten ---
            temp_veins = vein_surf.copy()
            temp_veins.set_alpha(fade_alpha)
            fade_surf.blit(temp_veins, (0, 0))

            screen.blit(fade_surf, (0, 0))

        impact_effects = [e for e in impact_effects if now - e['t'] < 0.4]
        for e in impact_effects:
            txt = font_ui.render(e['txt'], True, e['c']);
            screen.blit(txt, (e['p'][0] - txt.get_width() // 2, e['p'][1] - 80 - int((now - e['t']) / 0.4 * 30)))

        # --- MUSIK FADING LOGIK & PAUSE MENU ---
        current_music_vol = pygame.mixer.music.get_volume()
        if game_paused:
            if current_music_vol > 0.125:
                pygame.mixer.music.set_volume(max(0.125, current_music_vol - 0.02))

            s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA);
            s.fill((0, 0, 0, 200));
            screen.blit(s, (0, 0));
            Button((WIDTH // 2 - 150, HEIGHT // 2 - 100, 300, 70), "WEITERSPIELEN").draw(screen);
            Button((WIDTH // 2 - 150, HEIGHT // 2, 300, 70), "ZUM MENÜ").draw(screen)
        else:
            if current_music_vol < 0.5:
                pygame.mixer.music.set_volume(min(0.5, current_music_vol + 0.02))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if SND_BREATH: SND_BREATH.stop()
                return "QUIT"
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                if not game_paused:
                    game_paused, pause_t = True, time.time();
                    pygame.mouse.set_visible(True)
                else:
                    game_paused = False;
                    acc_pause += (time.time() - pause_t);
                    pygame.mouse.set_visible(False)
            if not game_paused and event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos;
                is_swinging, swing_start = True, now;
                c_idx = (mx // (WIDTH // 4)) + (my // (HEIGHT // 2)) * 4;
                hit_any = False;
                total_swings += 1
                for m in active_moles:
                    if m['idx'] == c_idx and not m['hit']:
                        m['hit'], hit_any = True, True;
                        total_hits += 1;
                        hit_counts[m['name']] = hit_counts.get(m['name'], 0) + 1

                        if selected_theme == "Nazi":
                            p_c = (120, 80, 50)
                            q_l = NAZI_Q
                            # --- DRECK PARTIKEL DIE KLEBEN UND VERBLASSEN ---
                            for _ in range(15):
                                p = Particle(mx + random.randint(-40, 40), my + random.randint(-40, 40), p_c)
                                p.is_dirt = True
                                particles.append(p)
                        else:
                            p_c = (200, 200, 200)
                            q_l = POLI_Q
                            for _ in range(15):
                                particles.append(Particle(mx, my, p_c))

                        if streak >= 14:
                            for _ in range(random.randint(1, 3)):
                                bx, by = mx + random.randint(-50, 50), my + random.randint(-50, 50)
                                pts = [(bx + random.randint(-20, 20), by + random.randint(-20, 20)) for _ in range(4)]
                                blood_splatters.append({'p': (bx, by), 'r': random.randint(4, 12), 'pts': pts})
                        if "Trump" in m['name']:
                            play_variant(SND_TRUMP)
                        elif "Kanye" in m['name']:
                            play_variant(SND_KANYE)
                        if selected_theme == "Politiker":
                            for _ in range(3): active_flashes.append(
                                {'p': (random.randint(0, WIDTH), random.randint(0, HEIGHT)), 't': now,
                                 'r': random.randint(50, 150)})

                        if m['type'] == "gold":
                            stress_level = max(0.0, stress_level - 20.0)
                            play_variant(SND_HITS);
                            play_variant(SND_POWERUP)
                            pu = random.choice(["freeze", "big", "double"]);
                            power_timers[pu] = now + 5.0;
                            impact_effects.append(
                                {'p': event.pos, 't': now, 'txt': f"POWERUP: {pu.upper()}!", 'c': COLOR_GOLD})
                        elif m['type'] == "red":
                            red_hits += 1;
                            streak, score, shake_amount = 0, score - 5, 30;
                            stress_level = min(100.0, stress_level + 15.0)
                            play_variant(SND_PENALTY);
                            impact_effects.append({'p': event.pos, 't': now, 'txt': "-5 BOOM!", 'c': COLOR_RED})
                        else:
                            streak += 1;
                            max_streak = max(max_streak, streak);
                            stress_level = max(0.0, stress_level - (2.0 + streak * 0.5))
                            mult = 2 if power_timers["double"] > now else 1
                            pts = int(
                                (1 + (streak - 3 if streak >= 4 else 0)) * (2 if m['type'] == "green" else 1) * mult)
                            score, shake_amount = score + pts, 20 if m['type'] == "green" else 12;
                            play_variant(SND_SPECIAL if m['type'] == "green" else SND_HITS);
                            impact_effects.append({'p': event.pos, 't': now, 'txt': random.choice(q_l),
                                                   'c': COLOR_GREEN if m['type'] == "green" else COLOR_WHITE})
                        pygame.time.set_timer(pygame.USEREVENT, 250)

                if not hit_any:
                    streak, score, shake_amount = 0, score - 1, 3;
                    stress_level = min(100.0, stress_level + 5.0)
                    play_variant(SND_MISSES);
                    impact_effects.append({'p': event.pos, 't': now, 'txt': "-1 MISS", 'c': ACCENT_COLOR})

            if game_paused and event.type == pygame.MOUSEBUTTONDOWN:
                if Button((WIDTH // 2 - 150, HEIGHT // 2 - 100, 300, 70), "").rect.collidepoint(
                        event.pos): game_paused = False; acc_pause += (time.time() - pause_t); pygame.mouse.set_visible(
                    False)
                if Button((WIDTH // 2 - 150, HEIGHT // 2, 300, 70), "").rect.collidepoint(event.pos):
                    if SND_BREATH: SND_BREATH.stop()
                    return "MENU"
            if event.type == pygame.USEREVENT:
                pygame.time.set_timer(pygame.USEREVENT, 0);
                active_moles = [m for m in active_moles if not m['hit']]


def run_game_over(stats, theme, highscores):
    pygame.mouse.set_visible(True);
    score = stats['score'];
    mode = stats.get('mode', 'Classic')
    prec = (stats['hits'] / stats['swings'] * 100) if stats['swings'] > 0 else 0

    hs_key = theme if mode == "Classic" else f"Endless_{theme}"

    if score > highscores["themes"].get(hs_key, 0): highscores["themes"][hs_key] = score
    if mode == "Classic" and score > highscores.get("overall", 0): highscores["overall"] = score
    save_highscores(highscores);

    btn_menu = Button((WIDTH // 2 - 150, HEIGHT * 0.88, 300, 70), "ZUM MENÜ")
    achievements = []
    if stats['red_hits'] == 0: achievements.append("PAZIFIST")
    if prec > 92: achievements.append("SCHARFSCHÜTZE")

    while True:
        screen.fill(PANEL_COLOR);
        draw_text_center("GAME OVER", font_big, ACCENT_COLOR, HEIGHT * 0.1);
        draw_text_center(f"Theme: {theme} ({mode}) | Score: {score}", font_main, TEXT_COLOR, HEIGHT * 0.22);

        if mode == "Endless":
            draw_text_center(f"Überlebt: {int(stats['time'])} Sekunden", font_small, COLOR_RED, HEIGHT * 0.28)
            y_base = HEIGHT * 0.33
        else:
            draw_text_center(f"Präzision: {int(prec)}% | Max Streak: {stats['max_streak']}", font_small, TEXT_COLOR,
                             HEIGHT * 0.28)
            y_base = HEIGHT * 0.33

        if achievements: draw_text_center(" + ".join(achievements), font_small, COLOR_GREEN, y_base)

        y_offset = HEIGHT * 0.4;
        sorted_hits = sorted(stats['counts'].items(), key=lambda item: item[1], reverse=True)
        for name, count in sorted_hits:
            if y_offset < HEIGHT * 0.85: txt = font_small.render(f"{name}: {count} Treffer", True,
                                                                 COLOR_GOLD); screen.blit(txt, txt.get_rect(
                center=(WIDTH // 2, y_offset))); y_offset += 35
        btn_menu.draw(screen);
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return False
            if btn_menu.is_clicked(event) or (
                    event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE): return True


def main():
    while True:
        hs = load_highscores();
        sel = run_menu(hs)
        if sel is None: break
        theme, mode = sel
        final_stats = run_game(theme, mode)
        if final_stats == "QUIT": break
        if final_stats == "MENU": continue
        if not run_game_over(final_stats, theme, hs): break
    pygame.quit()


if __name__ == "__main__": main()