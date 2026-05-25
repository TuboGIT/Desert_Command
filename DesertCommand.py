"""
DESERT COMMAND - Askeri Strateji Oyunu
Pygame + pygame_menu ile geliştirilmiş çöl savaş oyunu
"""

import pygame
import pygame_menu
import random
import math
import sys
import os
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum

# ─────────────────────────────────────────────
#  SABITLER
# ─────────────────────────────────────────────
SCREEN_W, SCREEN_H = 1280, 800
FPS = 60
GRID_SIZE = 64
GRID_COLS = 12
GRID_ROWS = 8

# Renkler
SAND1      = (210, 180, 120)
SAND2      = (190, 155, 95)
SAND3      = (230, 200, 140)
DARK_SAND  = (160, 130, 75)
BROWN      = (101, 67, 33)
STONE      = (140, 130, 115)
GREEN_MIL  = (75, 95, 50)
DARK_GREEN = (45, 65, 30)
RED_MIL    = (160, 30, 30)
RED_BRIGHT = (220, 50, 50)
ORANGE     = (220, 130, 30)
YELLOW     = (255, 220, 60)
WHITE      = (255, 255, 255)
BLACK      = (0, 0, 0)
GRAY       = (100, 100, 100)
LIGHT_GRAY = (180, 180, 180)
PANEL_BG   = (28, 22, 14, 220)
PANEL_BG2  = (40, 32, 18, 200)
HUD_BG     = (20, 15, 8, 240)
BLUE_MIL   = (40, 80, 140)
TEAL       = (30, 120, 100)
GOLD       = (200, 165, 50)

# ─────────────────────────────────────────────
#  BİRLİK TANIMLAMALARI
# ─────────────────────────────────────────────
class UnitType(Enum):
    ER         = "er"
    KESKIN_NIS = "keskin_nisanci"
    BAZUKALI   = "bazukali"
    KOMANDO    = "komando"
    HAFIF_ZIR  = "hafif_zirhli"
    TANK       = "tank"
    TOPCU      = "topcu"
    HELIKOPTER = "helikopter"

@dataclass
class UnitDef:
    type: UnitType
    name: str
    ap_cost: int
    hp: int
    atk: int
    defense: int
    range: int
    speed: int
    emoji: str
    color: Tuple
    enemy_color: Tuple
    description: str

UNIT_DEFS: Dict[UnitType, UnitDef] = {
    UnitType.ER: UnitDef(
        UnitType.ER, "Er", 30,
        hp=60, atk=15, defense=5, range=2, speed=3,
        emoji="🪖", color=(80, 110, 60), enemy_color=(140, 50, 50),
        description="Temel piyade birliği. Ucuz ve çok sayıda."
    ),
    UnitType.KESKIN_NIS: UnitDef(
        UnitType.KESKIN_NIS, "Keskin Nişancı", 60,
        hp=45, atk=35, defense=3, range=5, speed=2,
        emoji="🎯", color=(60, 90, 50), enemy_color=(120, 40, 40),
        description="Uzun menzil, yüksek hasar. Savunmasız yakın dövüşte."
    ),
    UnitType.BAZUKALI: UnitDef(
        UnitType.BAZUKALI, "Bazukalı Asker", 80,
        hp=55, atk=50, defense=4, range=3, speed=2,
        emoji="💥", color=(70, 100, 55), enemy_color=(150, 55, 30),
        description="Zırhlı araçlara karşı etkili. Alan hasarı yapar."
    ),
    UnitType.KOMANDO: UnitDef(
        UnitType.KOMANDO, "Komando", 100,
        hp=80, atk=40, defense=15, range=2, speed=4,
        emoji="⚔️", color=(50, 80, 40), enemy_color=(110, 35, 35),
        description="Elit piyade. Yüksek savunma ve hız."
    ),
    UnitType.HAFIF_ZIR: UnitDef(
        UnitType.HAFIF_ZIR, "Hafif Zırhlı Araç", 120,
        hp=120, atk=30, defense=25, range=3, speed=3,
        emoji="🚗", color=(85, 105, 65), enemy_color=(130, 60, 40),
        description="Hareketli zırhlı destek aracı."
    ),
    UnitType.TANK: UnitDef(
        UnitType.TANK, "Tank", 200,
        hp=250, atk=80, defense=50, range=4, speed=2,
        emoji="🛡️", color=(65, 85, 45), enemy_color=(100, 30, 30),
        description="Ağır zırh ve güçlü top. Pahalı ama yıkıcı."
    ),
    UnitType.TOPCU: UnitDef(
        UnitType.TOPCU, "Topçu Birliği", 150,
        hp=70, atk=90, defense=8, range=6, speed=1,
        emoji="🔫", color=(75, 95, 55), enemy_color=(145, 45, 25),
        description="Uzun menzilli ağır ateş desteği."
    ),
    UnitType.HELIKOPTER: UnitDef(
        UnitType.HELIKOPTER, "Saldırı Helikopteri", 250,
        hp=150, atk=70, defense=20, range=5, speed=5,
        emoji="🚁", color=(55, 75, 45), enemy_color=(115, 40, 35),
        description="Hava üstünlüğü ve hızlı saldırı kapasitesi."
    ),
}

# ─────────────────────────────────────────────
#  BİRLİK SINIFI
# ─────────────────────────────────────────────
@dataclass
class Unit:
    type: UnitType
    defn: UnitDef
    team: str  # "player" veya "enemy"
    grid_x: int
    grid_y: int
    hp: int = 0
    max_hp: int = 0
    moved: bool = False
    attacked: bool = False
    
    def __post_init__(self):
        if self.hp == 0:
            self.hp = self.defn.hp
        if self.max_hp == 0:
            self.max_hp = self.defn.hp

    @property
    def pixel_x(self):
        return self.grid_x * GRID_SIZE + GRID_SIZE // 2

    @property
    def pixel_y(self):
        return self.grid_y * GRID_SIZE + GRID_SIZE // 2

    @property
    def color(self):
        return self.defn.color if self.team == "player" else self.defn.enemy_color

    def is_alive(self):
        return self.hp > 0

    def take_damage(self, dmg: int):
        actual = max(1, dmg - self.defn.defense // 2)
        self.hp = max(0, self.hp - actual)
        return actual

    def can_move(self):
        return not self.moved

    def can_attack(self):
        return not self.attacked

    def reset_turn(self):
        self.moved = False
        self.attacked = False

    def in_range(self, other: 'Unit') -> bool:
        dist = abs(self.grid_x - other.grid_x) + abs(self.grid_y - other.grid_y)
        return dist <= self.defn.range


# ─────────────────────────────────────────────
#  RENDERER YARDIMCILARI
# ─────────────────────────────────────────────
def draw_rounded_rect(surf, color, rect, radius=8, alpha=255):
    if len(color) == 4:
        s = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
        pygame.draw.rect(s, color, (0, 0, rect[2], rect[3]), border_radius=radius)
        surf.blit(s, (rect[0], rect[1]))
    else:
        c = list(color) + [alpha]
        s = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
        pygame.draw.rect(s, c, (0, 0, rect[2], rect[3]), border_radius=radius)
        surf.blit(s, (rect[0], rect[1]))

def draw_text(surf, text, x, y, font, color=WHITE, center=False, shadow=True):
    if shadow:
        sh = font.render(text, True, (0,0,0,180))
        if center:
            surf.blit(sh, (x - sh.get_width()//2 + 1, y + 1))
        else:
            surf.blit(sh, (x+1, y+1))
    img = font.render(text, True, color)
    if center:
        surf.blit(img, (x - img.get_width()//2, y))
    else:
        surf.blit(img, (x, y))
    return img.get_width()

def lerp_color(c1, c2, t):
    return tuple(int(c1[i] + (c2[i]-c1[i])*t) for i in range(3))


# ─────────────────────────────────────────────
#  ANA OYUN SINIFI
# ─────────────────────────────────────────────
class DesertCommand:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("DESERT COMMAND – Çöl Savaş Komutanlığı")
        self.clock = pygame.time.Clock()
        
        # Fontlar
        self.font_xl  = pygame.font.SysFont("Impact", 52, bold=True)
        self.font_lg  = pygame.font.SysFont("Impact", 32)
        self.font_md  = pygame.font.SysFont("Arial", 20, bold=True)
        self.font_sm  = pygame.font.SysFont("Arial", 16)
        self.font_xs  = pygame.font.SysFont("Arial", 13)
        
        # Oyun durumu
        self.state = "menu"
        self.ap = 500
        self.turn = 1
        self.phase = "build"  # build / battle
        self.selected_unit: Optional[Unit] = None
        self.selected_grid: Optional[Tuple[int,int]] = None
        self.units: List[Unit] = []
        self.enemy_units: List[Unit] = []
        self.messages: List[Tuple[str, int, Tuple]] = []  # (text, timer, color)
        self.battle_log: List[str] = []
        self.animations: List[Dict] = []
        self.particles: List[Dict] = []
        self.wave = 1
        self.player_wins = 0
        self.enemy_wins = 0
        self.scroll_offset = 0
        self.highlight_cells: List[Tuple[int,int]] = []
        self.attack_cells: List[Tuple[int,int]] = []
        self.mode = "select"  # select / move / attack
        self.hover_unit_info: Optional[Unit] = None
        self.panel_scroll = 0
        
        # Zemin oluştur
        self.tiles = self._gen_tiles()
        self.deco  = self._gen_decorations()
        
        # Yüzeyler
        self.map_surf = pygame.Surface((GRID_COLS * GRID_SIZE, GRID_ROWS * GRID_SIZE))
        self._render_map()
        
        self._init_menu()

    # ── Harita ────────────────────────────────
    def _gen_tiles(self):
        tiles = []
        for r in range(GRID_ROWS):
            row = []
            for c in range(GRID_COLS):
                v = random.random()
                if v < 0.05:
                    row.append("rock")
                elif v < 0.12:
                    row.append("dark_sand")
                else:
                    row.append(random.choice(["sand1","sand2","sand3"]))
            tiles.append(row)
        return tiles

    def _gen_decorations(self):
        decos = []
        for _ in range(30):
            c = random.randint(0, GRID_COLS-1)
            r = random.randint(0, GRID_ROWS-1)
            t = random.choice(["cactus","stone","bush","crater"])
            decos.append((c, r, t))
        return decos

    def _render_map(self):
        tile_colors = {
            "sand1": SAND1, "sand2": SAND2, "sand3": SAND3,
            "dark_sand": DARK_SAND, "rock": STONE
        }
        for r, row in enumerate(self.tiles):
            for c, tile in enumerate(row):
                rect = (c*GRID_SIZE, r*GRID_SIZE, GRID_SIZE, GRID_SIZE)
                col = tile_colors.get(tile, SAND1)
                pygame.draw.rect(self.map_surf, col, rect)
                # Doku gürültüsü
                for _ in range(4):
                    nx = c*GRID_SIZE + random.randint(4,60)
                    ny = r*GRID_SIZE + random.randint(4,60)
                    nc = tuple(max(0,min(255,x+random.randint(-12,12))) for x in col)
                    pygame.draw.circle(self.map_surf, nc, (nx,ny), random.randint(2,6))
        # Grid çizgileri
        for c in range(GRID_COLS+1):
            pygame.draw.line(self.map_surf, (0,0,0,40), (c*GRID_SIZE,0), (c*GRID_SIZE,GRID_ROWS*GRID_SIZE), 1)
        for r in range(GRID_ROWS+1):
            pygame.draw.line(self.map_surf, (0,0,0,40), (0,r*GRID_SIZE), (GRID_COLS*GRID_SIZE,r*GRID_SIZE), 1)

    # ── Menu ──────────────────────────────────
    def _init_menu(self):
        theme = pygame_menu.themes.Theme(
            background_color=(20, 15, 10),
            title_background_color=(60, 40, 10),
            title_font=pygame_menu.font.FONT_8BIT,
            title_font_color=YELLOW,
            title_font_size=24,
            widget_font=pygame_menu.font.FONT_8BIT,
            widget_font_color=SAND1,
            widget_font_size=16,
            selection_color=ORANGE,
            widget_selection_effect=pygame_menu.widgets.HighlightSelection(border_width=2),
        )
        
        self.main_menu = pygame_menu.Menu(
            "DESERT COMMAND",
            SCREEN_W, SCREEN_H,
            theme=theme
        )
        self.main_menu.add.label("🏜️  Çöl Savaş Komutanlığı  🏜️", font_size=14, font_color=SAND3)
        self.main_menu.add.vertical_margin(20)
        self.main_menu.add.button("▶  YENİ SAVAŞ BAŞLAT", self._start_game)
        self.main_menu.add.button("📖  NASIL OYNANIR?",   self._how_to_play)
        self.main_menu.add.vertical_margin(10)
        self.main_menu.add.button("❌  ÇIKIŞ",            pygame_menu.events.EXIT)

    def _how_to_play(self):
        theme = pygame_menu.themes.Theme(
            background_color=(20, 15, 10),
            title_background_color=(60, 40, 10),
            title_font=pygame_menu.font.FONT_8BIT,
            title_font_color=YELLOW,
            title_font_size=20,
            widget_font=pygame_menu.font.FONT_8BIT,
            widget_font_color=SAND2,
            widget_font_size=12,
        )
        m = pygame_menu.Menu("NASIL OYNANIR?", SCREEN_W, SCREEN_H, theme=theme)
        lines = [
            "1. İNŞA AŞAMASI:",
            "   • 500 AP ile birlik satın al",
            "   • Yeşil bölgeye (sol 4 sütun) yerleştir",
            "   • SAVAŞA BAŞLA butonuna tıkla",
            "",
            "2. SAVAŞ AŞAMASI:",
            "   • Sıra tabanlı strateji oyunu",
            "   • Birime tıkla → Hareket et → Saldır",
            "   • TUR BİTİR ile sırayı düşmana ver",
            "",
            "3. BİRLİKLER:",
            "   Er: 30 AP  |  Keskin Nişancı: 60 AP",
            "   Bazukalı: 80 AP  |  Komando: 100 AP",
            "   H.Zırhlı: 120 AP |  Topçu: 150 AP",
            "   Tank: 200 AP  |  Helikopter: 250 AP",
            "",
            "4. HEDEF: Tüm düşman birimlerini yok et!",
        ]
        for l in lines:
            m.add.label(l, font_size=12)
        m.add.vertical_margin(15)
        m.add.button("◀  GERİ", pygame_menu.events.BACK)
        m.mainloop(self.screen)

    def _start_game(self):
        self.state = "build"
        self.ap = 500
        self.units = []
        self.enemy_units = []
        self.turn = 1
        self.wave = 1
        self.phase = "build"
        self.battle_log = []
        self.selected_unit = None
        self.mode = "select"
        self.panel_scroll = 0
        self._add_message("500 AP ile ordu kur! Yeşil alana birlikleri yerleştir.", 180, YELLOW)

    # ── Oyun mantığı ──────────────────────────
    def _add_message(self, text, duration=120, color=WHITE):
        self.messages.append([text, duration, color])

    def _grid_at(self, mx, my) -> Optional[Tuple[int,int]]:
        if mx < 0 or my < 0 or mx >= GRID_COLS*GRID_SIZE or my >= GRID_ROWS*GRID_SIZE:
            return None
        return mx // GRID_SIZE, my // GRID_SIZE

    def _unit_at(self, gx, gy, team=None) -> Optional[Unit]:
        for u in self.units + self.enemy_units:
            if u.grid_x == gx and u.grid_y == gy and u.is_alive():
                if team is None or u.team == team:
                    return u
        return None

    def _buy_unit(self, utype: UnitType):
        defn = UNIT_DEFS[utype]
        if self.ap < defn.ap_cost:
            self._add_message(f"❌ Yetersiz AP! ({defn.ap_cost} AP gerekli)", 120, RED_BRIGHT)
            return
        self.ap -= defn.ap_cost
        # Boş hücre bul (sol 4 sütun, satır 0-7)
        placed = False
        for attempt in range(50):
            gx = random.randint(0, 3)
            gy = random.randint(0, GRID_ROWS-1)
            if not self._unit_at(gx, gy):
                u = Unit(utype, defn, "player", gx, gy)
                self.units.append(u)
                placed = True
                self._add_message(f"✅ {defn.name} satın alındı! Kalan: {self.ap} AP", 90, YELLOW)
                self._spawn_particles(gx*GRID_SIZE+GRID_SIZE//2, gy*GRID_SIZE+GRID_SIZE//2, GREEN_MIL)
                break
        if not placed:
            self.ap += defn.ap_cost
            self._add_message("❌ Yer bulunamadı! Bazı birlikleri taşı.", 120, RED_BRIGHT)

    def _spawn_enemy_wave(self):
        budget = 200 + self.wave * 150
        types = list(UNIT_DEFS.keys())
        enemy_list = []
        while budget > 30:
            available = [t for t in types if UNIT_DEFS[t].ap_cost <= budget]
            if not available:
                break
            ut = random.choice(available)
            budget -= UNIT_DEFS[ut].ap_cost
            defn = UNIT_DEFS[ut]
            for _ in range(30):
                gx = random.randint(GRID_COLS-4, GRID_COLS-1)
                gy = random.randint(0, GRID_ROWS-1)
                if not self._unit_at(gx, gy) and (gx,gy) not in [(e.grid_x,e.grid_y) for e in enemy_list]:
                    enemy_list.append(Unit(ut, defn, "enemy", gx, gy))
                    break
        self.enemy_units = enemy_list
        self._add_message(f"⚠️ DALGA {self.wave}: {len(self.enemy_units)} düşman birliği yaklaşıyor!", 150, RED_BRIGHT)

    def _start_battle(self):
        if not self.units:
            self._add_message("❌ Önce birlik satın al!", 120, RED_BRIGHT)
            return
        self.phase = "battle"
        self.state = "battle"
        self._spawn_enemy_wave()
        self._add_message("⚔️  SAVAŞ BAŞLADI! Birliklerini seç ve saldır!", 150, ORANGE)
        for u in self.units:
            u.reset_turn()

    def _end_player_turn(self):
        for u in self.units:
            u.reset_turn()
        self._add_message("🔴 Düşman sırası...", 90, RED_BRIGHT)
        self._enemy_ai()
        for u in self.enemy_units:
            u.reset_turn()
        self.turn += 1
        self._add_message(f"✅ Tur {self.turn} - Senin sıran!", 90, YELLOW)
        self._check_battle_end()

    def _enemy_ai(self):
        for enemy in self.enemy_units:
            if not enemy.is_alive():
                continue
            # En yakın oyuncu birimini hedef al
            target = min(
                (u for u in self.units if u.is_alive()),
                key=lambda u: abs(u.grid_x-enemy.grid_x)+abs(u.grid_y-enemy.grid_y),
                default=None
            )
            if target is None:
                continue
            
            dist = abs(target.grid_x-enemy.grid_x) + abs(target.grid_y-enemy.grid_y)
            
            # Hareket et
            if dist > enemy.defn.range:
                dx = target.grid_x - enemy.grid_x
                dy = target.grid_y - enemy.grid_y
                # Hamle yönü
                moves = []
                if dx != 0: moves.append((int(math.copysign(1,dx)), 0))
                if dy != 0: moves.append((0, int(math.copysign(1,dy))))
                
                for mx, my in moves:
                    nx, ny = enemy.grid_x+mx, enemy.grid_y+my
                    if 0<=nx<GRID_COLS and 0<=ny<GRID_ROWS and not self._unit_at(nx,ny):
                        enemy.grid_x, enemy.grid_y = nx, ny
                        break
            
            # Saldır
            dist2 = abs(target.grid_x-enemy.grid_x) + abs(target.grid_y-enemy.grid_y)
            if dist2 <= enemy.defn.range:
                dmg = enemy.take_damage(-enemy.defn.atk)  # trick: get atk val
                actual = target.take_damage(enemy.defn.atk)
                self._spawn_particles(
                    target.pixel_x, target.pixel_y, RED_BRIGHT
                )
                self.battle_log.append(f"[D{self.turn}] {enemy.defn.name} → {target.defn.name}: -{actual} HP")
                if len(self.battle_log) > 20:
                    self.battle_log.pop(0)

    def _check_battle_end(self):
        alive_player = [u for u in self.units if u.is_alive()]
        alive_enemy  = [u for u in self.enemy_units if u.is_alive()]
        
        if not alive_enemy:
            self.player_wins += 1
            self._add_message(f"🏆 ZAFER! Dalga {self.wave} temizlendi!", 300, YELLOW)
            self.wave += 1
            self.ap += 100 + self.wave * 20  # Ödül AP
            self._add_message(f"💰 Ödül: +{100+self.wave*20} AP! Toplam: {self.ap} AP", 240, GOLD)
            self.phase = "build"
            self.state = "build"
            for u in self.units:
                u.reset_turn()
            self._add_message("Yeni birlikleri yerleştir ve SAVAŞA BAŞLA!", 200, SAND3)
        elif not alive_player:
            self.enemy_wins += 1
            self._add_message("💀 KAYBETTİN! Tüm birlikler yok edildi.", 300, RED_BRIGHT)
            self.state = "game_over"

    def _do_attack(self, attacker: Unit, target: Unit):
        dmg = attacker.defn.atk + random.randint(-5, 5)
        actual = target.take_damage(dmg)
        attacker.attacked = True
        
        self._spawn_particles(target.pixel_x, target.pixel_y, ORANGE)
        self.battle_log.append(
            f"[T{self.turn}] {attacker.defn.name} → {target.defn.name}: -{actual} HP"
            + (" 💀" if not target.is_alive() else "")
        )
        if len(self.battle_log) > 20:
            self.battle_log.pop(0)
        
        self._add_message(f"💥 {attacker.defn.name} saldırdı: -{actual} HP!", 90, ORANGE)
        if not target.is_alive():
            self._add_message(f"💀 {target.defn.name} yok edildi!", 120, RED_BRIGHT)
        
        self._check_battle_end()

    def _move_unit(self, unit: Unit, gx: int, gy: int):
        dist = abs(unit.grid_x-gx) + abs(unit.grid_y-gy)
        if dist > unit.defn.speed:
            self._add_message("❌ Çok uzak! Hareket menzili aşıldı.", 90, RED_BRIGHT)
            return
        if self._unit_at(gx, gy):
            self._add_message("❌ Bu hücre dolu!", 90, RED_BRIGHT)
            return
        unit.grid_x, unit.grid_y = gx, gy
        unit.moved = True
        self._add_message(f"📍 {unit.defn.name} hareket etti.", 60, SAND3)

    # ── Partiküller ───────────────────────────
    def _spawn_particles(self, x, y, color, count=12):
        for _ in range(count):
            angle = random.uniform(0, 2*math.pi)
            speed = random.uniform(1.5, 5)
            self.particles.append({
                "x": float(x), "y": float(y),
                "vx": math.cos(angle)*speed, "vy": math.sin(angle)*speed,
                "life": random.randint(20, 45),
                "color": color, "size": random.randint(2,5)
            })

    def _update_particles(self):
        alive = []
        for p in self.particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vy"] += 0.1
            p["life"] -= 1
            p["size"] = max(1, p["size"] - 0.05)
            if p["life"] > 0:
                alive.append(p)
        self.particles = alive

    def _draw_particles(self, surf):
        for p in self.particles:
            alpha = int(255 * (p["life"] / 45))
            r,g,b = p["color"][:3]
            c = (r,g,b)
            pygame.draw.circle(surf, c, (int(p["x"]), int(p["y"])), int(p["size"]))

    # ── Işık vurgulama hücreler ───────────────
    def _calc_highlights(self):
        self.highlight_cells = []
        self.attack_cells = []
        if not self.selected_unit:
            return
        u = self.selected_unit
        
        if self.mode == "move" and u.can_move():
            for dy in range(-u.defn.speed, u.defn.speed+1):
                for dx in range(-u.defn.speed, u.defn.speed+1):
                    if abs(dx)+abs(dy) <= u.defn.speed:
                        nx, ny = u.grid_x+dx, u.grid_y+dy
                        if 0<=nx<GRID_COLS and 0<=ny<GRID_ROWS:
                            if not self._unit_at(nx,ny):
                                self.highlight_cells.append((nx,ny))
        
        if self.mode == "attack" and u.can_attack():
            for dy in range(-u.defn.range, u.defn.range+1):
                for dx in range(-u.defn.range, u.defn.range+1):
                    if abs(dx)+abs(dy) <= u.defn.range:
                        nx, ny = u.grid_x+dx, u.grid_y+dy
                        if 0<=nx<GRID_COLS and 0<=ny<GRID_ROWS:
                            enemy = self._unit_at(nx, ny, "enemy")
                            if enemy:
                                self.attack_cells.append((nx,ny))

    # ── Çizim ─────────────────────────────────
    def _draw_grid(self, surf):
        surf.blit(self.map_surf, (0, 0))
        
        # İnşa aşaması - oyuncu bölgesi yeşil overlay
        if self.state == "build":
            s = pygame.Surface((4*GRID_SIZE, GRID_ROWS*GRID_SIZE), pygame.SRCALPHA)
            s.fill((60, 120, 60, 40))
            surf.blit(s, (0, 0))
            pygame.draw.rect(surf, (80,160,80,120), (0,0,4*GRID_SIZE,GRID_ROWS*GRID_SIZE), 3)
        
        # Hareket hücreleri
        for (gx,gy) in self.highlight_cells:
            s = pygame.Surface((GRID_SIZE, GRID_SIZE), pygame.SRCALPHA)
            s.fill((60,160,255,70))
            surf.blit(s, (gx*GRID_SIZE, gy*GRID_SIZE))
            pygame.draw.rect(surf, (80,180,255), (gx*GRID_SIZE,gy*GRID_SIZE,GRID_SIZE,GRID_SIZE), 2)
        
        # Saldırı hücreleri
        for (gx,gy) in self.attack_cells:
            s = pygame.Surface((GRID_SIZE, GRID_SIZE), pygame.SRCALPHA)
            s.fill((255,60,60,80))
            surf.blit(s, (gx*GRID_SIZE, gy*GRID_SIZE))
            pygame.draw.rect(surf, (255,80,80), (gx*GRID_SIZE,gy*GRID_SIZE,GRID_SIZE,GRID_SIZE), 2)

    def _draw_unit(self, surf, unit: Unit):
        if not unit.is_alive():
            return
        
        cx = unit.pixel_x
        cy = unit.pixel_y
        col = unit.color
        
        # Gölge
        pygame.draw.ellipse(surf, (0,0,0,60), (cx-18, cy+14, 36, 10))
        
        # Seçili vurgu
        if unit == self.selected_unit:
            t = pygame.time.get_ticks() / 500
            pulse = int(abs(math.sin(t)) * 3) + 2
            pygame.draw.circle(surf, YELLOW, (cx, cy), 26+pulse, 3)
        
        # Birim gövdesi
        pygame.draw.circle(surf, col, (cx, cy), 22)
        pygame.draw.circle(surf, tuple(min(255,c+40) for c in col), (cx-4, cy-4), 14)
        pygame.draw.circle(surf, tuple(max(0,c-30) for c in col), (cx, cy), 22, 3)
        
        # Takım göstergesi
        team_col = BLUE_MIL if unit.team == "player" else RED_MIL
        pygame.draw.circle(surf, team_col, (cx, cy-16), 7)
        pygame.draw.circle(surf, WHITE, (cx, cy-16), 7, 2)
        
        # Emoji / sembol (metin)
        sym = {"er":"E","keskin_nisanci":"N","bazukali":"B","komando":"K",
               "hafif_zirhli":"Z","tank":"T","topcu":"A","helikopter":"H"}
        s = sym.get(unit.type.value, "?")
        lbl = self.font_sm.render(s, True, WHITE)
        surf.blit(lbl, (cx - lbl.get_width()//2, cy - lbl.get_height()//2))
        
        # HP bar
        bar_w = 40
        bar_h = 5
        bx = cx - bar_w//2
        by = cy + 24
        pct = unit.hp / unit.max_hp
        pygame.draw.rect(surf, (40,20,10), (bx-1, by-1, bar_w+2, bar_h+2), border_radius=2)
        pygame.draw.rect(surf, (60, 30, 15), (bx, by, bar_w, bar_h))
        hp_col = lerp_color((200,50,50), (50,200,80), pct)
        pygame.draw.rect(surf, hp_col, (bx, by, int(bar_w*pct), bar_h))
        
        # Hareket/saldırı durumu
        if unit.team == "player" and self.state == "battle":
            indicators = []
            if unit.moved:   indicators.append(("M", GRAY))
            if unit.attacked:indicators.append(("A", RED_MIL))
            for i, (sym2, ic) in enumerate(indicators):
                il = self.font_xs.render(sym2, True, ic)
                surf.blit(il, (cx + 14 + i*12, cy - 28))

    def _draw_hud(self, surf):
        # Üst HUD
        hud = pygame.Surface((SCREEN_W, 50), pygame.SRCALPHA)
        hud.fill((15, 10, 5, 230))
        surf.blit(hud, (0, 0))
        pygame.draw.line(surf, GOLD, (0, 50), (SCREEN_W, 50), 2)
        
        # Başlık
        draw_text(surf, "DESERT COMMAND", 20, 10, self.font_lg, GOLD)
        
        # AP göstergesi
        ap_col = YELLOW if self.ap >= 100 else ORANGE if self.ap >= 50 else RED_BRIGHT
        draw_text(surf, f"⬡ AP: {self.ap}", 380, 12, self.font_md, ap_col)
        
        # Tur / Durum
        phase_text = "🔨 İNŞA AŞAMASI" if self.phase == "build" else f"⚔️  TUR {self.turn}"
        draw_text(surf, phase_text, 580, 12, self.font_md, SAND3)
        
        # Dalga
        draw_text(surf, f"🌊 DALGA: {self.wave}", 820, 12, self.font_md, ORANGE)
        
        # Skor
        draw_text(surf, f"🏆 {self.player_wins}  💀 {self.enemy_wins}", 1000, 12, self.font_md, LIGHT_GRAY)
        
        # Birim sayısı
        alive_p = len([u for u in self.units if u.is_alive()])
        alive_e = len([u for u in self.enemy_units if u.is_alive()])
        draw_text(surf, f"👥{alive_p}  👿{alive_e}", 1160, 12, self.font_md, SAND2)

    def _draw_side_panel(self, surf):
        pw = 280
        px = SCREEN_W - pw
        py = 52
        ph = SCREEN_H - py - 5
        
        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        panel.fill((20, 14, 7, 225))
        surf.blit(panel, (px, py))
        pygame.draw.rect(surf, GOLD, (px, py, pw, ph), 2, border_radius=4)
        
        y = py + 10
        
        if self.state == "build":
            draw_text(surf, "🏪 ORDU KURMA MERKEZİ", px+10, y, self.font_sm, GOLD)
            y += 28
            draw_text(surf, f"Mevcut AP: {self.ap}", px+10, y, self.font_sm, YELLOW)
            y += 24
            pygame.draw.line(surf, DARK_SAND, (px+5, y), (px+pw-5, y), 1)
            y += 8
            
            for utype, defn in UNIT_DEFS.items():
                if y > py + ph - 60:
                    break
                
                can_buy = self.ap >= defn.ap_cost
                bg_col  = (40, 55, 30, 160) if can_buy else (45, 25, 15, 140)
                
                btn_rect = (px+6, y, pw-12, 48)
                s2 = pygame.Surface((pw-12, 48), pygame.SRCALPHA)
                s2.fill(bg_col)
                surf.blit(s2, (px+6, y))
                pygame.draw.rect(surf, GREEN_MIL if can_buy else DARK_SAND,
                                 btn_rect, 1, border_radius=4)
                
                name_col = WHITE if can_buy else GRAY
                draw_text(surf, defn.name, px+14, y+5, self.font_sm, name_col, shadow=True)
                
                ap_col2 = YELLOW if can_buy else (100,100,80)
                draw_text(surf, f"{defn.ap_cost} AP", px+pw-65, y+5, self.font_sm, ap_col2)
                
                stat_txt = f"HP:{defn.hp} ATK:{defn.atk} MNZ:{defn.range}"
                draw_text(surf, stat_txt, px+14, y+25, self.font_xs, LIGHT_GRAY if can_buy else GRAY)
                
                # Tıklanabilir alan kaydet
                defn._btn_rect = btn_rect
                y += 52
            
            y = py + ph - 55
            pygame.draw.line(surf, GOLD, (px+5, y-5), (px+pw-5, y-5), 1)
            btn_col = (50, 150, 50) if self.units else (60, 60, 60)
            draw_rounded_rect(surf, btn_col + (200,), (px+10, y, pw-20, 42), radius=8)
            pygame.draw.rect(surf, YELLOW if self.units else GRAY,
                             (px+10, y, pw-20, 42), 2, border_radius=8)
            draw_text(surf, "⚔️  SAVAŞA BAŞLA!", px + pw//2, y+10, self.font_md,
                      YELLOW if self.units else GRAY, center=True)
            self._battle_btn = (px+10, y, pw-20, 42)
        
        elif self.state == "battle":
            if self.selected_unit:
                u = self.selected_unit
                draw_text(surf, f"📋 {u.defn.name.upper()}", px+10, y, self.font_md,
                          BLUE_MIL if u.team=="player" else RED_MIL)
                y += 28
                
                hp_pct = u.hp / u.max_hp
                hp_col = lerp_color((200,50,50),(50,200,80), hp_pct)
                draw_text(surf, f"❤  HP: {u.hp}/{u.max_hp}", px+10, y, self.font_sm, hp_col)
                y += 22
                draw_text(surf, f"⚔  ATK: {u.defn.atk}   🛡 DEF: {u.defn.defense}", px+10, y, self.font_sm, SAND2)
                y += 22
                draw_text(surf, f"🎯 MNZ: {u.defn.range}   💨 HIZ: {u.defn.speed}", px+10, y, self.font_sm, SAND2)
                y += 22
                draw_text(surf, f"📍 Konum: ({u.grid_x},{u.grid_y})", px+10, y, self.font_xs, GRAY)
                y += 22
                
                # Açıklama
                desc_lines = []
                words = u.defn.description.split()
                line = ""
                for w in words:
                    if len(line+" "+w) > 28:
                        desc_lines.append(line)
                        line = w
                    else:
                        line += " "+w if line else w
                if line: desc_lines.append(line)
                
                for dl in desc_lines:
                    draw_text(surf, dl, px+10, y, self.font_xs, LIGHT_GRAY)
                    y += 16
                
                y += 10
                pygame.draw.line(surf, DARK_SAND, (px+5, y), (px+pw-5, y), 1)
                y += 10
                
                if u.team == "player":
                    # Hareket butonu
                    can_move = u.can_move()
                    mc = (40,80,140) if can_move else (40,40,40)
                    draw_rounded_rect(surf, mc+(200,), (px+10, y, pw-20, 36), radius=6)
                    pygame.draw.rect(surf, (80,140,220) if can_move else GRAY,
                                     (px+10, y, pw-20, 36), 2, border_radius=6)
                    ml = "📍 HAREKET ET" + (" ✓" if self.mode=="move" else "")
                    draw_text(surf, ml, px+pw//2, y+8, self.font_sm,
                              WHITE if can_move else GRAY, center=True)
                    self._move_btn = (px+10, y, pw-20, 36)
                    y += 42
                    
                    # Saldırı butonu
                    can_atk = u.can_attack()
                    ac = (140,40,40) if can_atk else (40,40,40)
                    draw_rounded_rect(surf, ac+(200,), (px+10, y, pw-20, 36), radius=6)
                    pygame.draw.rect(surf, (220,80,80) if can_atk else GRAY,
                                     (px+10, y, pw-20, 36), 2, border_radius=6)
                    al = "⚔️  SALDIRI" + (" ✓" if self.mode=="attack" else "")
                    draw_text(surf, al, px+pw//2, y+8, self.font_sm,
                              WHITE if can_atk else GRAY, center=True)
                    self._attack_btn = (px+10, y, pw-20, 36)
                    y += 42
            
            else:
                draw_text(surf, "Birlik seçin", px+10, y, self.font_sm, GRAY)
                y += 30
                self._move_btn = None
                self._attack_btn = None
            
            # TUR BİTİR butonu (alt)
            y = py + ph - 55
            pygame.draw.line(surf, GOLD, (px+5, y-5), (px+pw-5, y-5), 1)
            draw_rounded_rect(surf, (130,80,20,200), (px+10, y, pw-20, 42), radius=8)
            pygame.draw.rect(surf, ORANGE, (px+10, y, pw-20, 42), 2, border_radius=8)
            draw_text(surf, "🔚 TUR BİTİR", px+pw//2, y+10, self.font_md, YELLOW, center=True)
            self._end_turn_btn = (px+10, y, pw-20, 42)
            
            # Mod göstergesi
            if self.mode != "select":
                mode_txt = "📍 Hedef hücre seç" if self.mode=="move" else "🎯 Düşman seç"
                draw_text(surf, mode_txt, px+10, py+ph-80, self.font_xs, ORANGE)

    def _draw_battle_log(self, surf):
        if not self.battle_log:
            return
        bx, by = 10, SCREEN_H - 200
        bw, bh = 280, 190
        s = pygame.Surface((bw, bh), pygame.SRCALPHA)
        s.fill((10, 8, 4, 180))
        surf.blit(s, (bx, by))
        pygame.draw.rect(surf, DARK_SAND, (bx, by, bw, bh), 1, border_radius=4)
        draw_text(surf, "📜 SAVAŞ GÜNLÜĞÜ", bx+8, by+5, self.font_xs, GOLD)
        for i, log in enumerate(reversed(self.battle_log[-10:])):
            col = RED_BRIGHT if "💀" in log else SAND2
            draw_text(surf, log[:40], bx+6, by+22 + i*16, self.font_xs, col, shadow=False)

    def _draw_messages(self, surf):
        y = 60
        for msg in self.messages:
            t, timer, col = msg[0], msg[1], msg[2]
            alpha = min(255, timer * 4)
            font_img = self.font_sm.render(t, True, col)
            s = pygame.Surface(font_img.get_size(), pygame.SRCALPHA)
            s.fill((0,0,0,0))
            s.blit(font_img, (0,0))
            s.set_alpha(alpha)
            surf.blit(s, (SCREEN_W//2 - font_img.get_width()//2, y))
            y += 24

    def _draw_mode_indicator(self, surf):
        if self.mode == "select":
            return
        col = (60,120,200) if self.mode=="move" else (180,40,40)
        txt = "📍 HAREKET MODU – Taşımak istediğin hücreye tıkla (ESC ile iptal)" \
              if self.mode=="move" else \
              "⚔️  SALDIRI MODU – Kırmızı hücredeki düşmana tıkla (ESC ile iptal)"
        s = pygame.Surface((SCREEN_W, 30), pygame.SRCALPHA)
        s.fill(col + (160,))
        surf.blit(s, (0, SCREEN_H - 34))
        draw_text(surf, txt, SCREEN_W//2, SCREEN_H-28, self.font_sm, WHITE, center=True)

    def _draw_game_over(self, surf):
        s = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        s.fill((0, 0, 0, 170))
        surf.blit(s, (0, 0))
        
        draw_text(surf, "💀 OYUN BİTTİ", SCREEN_W//2, SCREEN_H//2 - 80,
                  self.font_xl, RED_BRIGHT, center=True)
        draw_text(surf, f"Zafer: {self.player_wins}  |  Mağlubiyet: {self.enemy_wins}",
                  SCREEN_W//2, SCREEN_H//2, self.font_lg, SAND2, center=True)
        draw_text(surf, f"Ulaşılan Dalga: {self.wave}", SCREEN_W//2, SCREEN_H//2 + 50,
                  self.font_md, ORANGE, center=True)
        
        # Yeniden başlat
        draw_rounded_rect(surf, (50, 30, 10, 230), (SCREEN_W//2-120, SCREEN_H//2+110, 240, 50), radius=10)
        pygame.draw.rect(surf, GOLD, (SCREEN_W//2-120, SCREEN_H//2+110, 240, 50), 2, border_radius=10)
        draw_text(surf, "↩  YENİDEN BAŞLA", SCREEN_W//2, SCREEN_H//2+122, self.font_md, YELLOW, center=True)
        self._restart_btn = (SCREEN_W//2-120, SCREEN_H//2+110, 240, 50)

    # ── Koordinat kontrolü ────────────────────
    def _in_rect(self, mx, my, rect):
        return rect[0] <= mx <= rect[0]+rect[2] and rect[1] <= my <= rect[1]+rect[3]

    # ── Input ─────────────────────────────────
    def _handle_build_click(self, mx, my):
        # Birlik butonları
        for utype, defn in UNIT_DEFS.items():
            if hasattr(defn, '_btn_rect') and self._in_rect(mx, my, defn._btn_rect):
                self._buy_unit(utype)
                return
        
        # Savaşa başla
        if hasattr(self, '_battle_btn') and self._in_rect(mx, my, self._battle_btn):
            self._start_battle()
            return
        
        # Harita tıklama – birliği taşı
        if mx < GRID_COLS*GRID_SIZE and my < GRID_ROWS*GRID_SIZE:
            gx, gy = mx // GRID_SIZE, my // GRID_SIZE
            u = self._unit_at(gx, gy, "player")
            if u:
                self.selected_unit = u
                self._add_message(f"{u.defn.name} seçildi. Taşımak için başka hücreye tıkla.", 90, SAND3)
            elif self.selected_unit and gx < 4:
                # Seçili birliği taşı (inşa bölgesi içinde)
                if not self._unit_at(gx, gy):
                    self.selected_unit.grid_x, self.selected_unit.grid_y = gx, gy
                    self.selected_unit = None

    def _handle_battle_click(self, mx, my):
        # Tur bitir
        if hasattr(self, '_end_turn_btn') and self._in_rect(mx, my, self._end_turn_btn):
            self._end_player_turn()
            self.selected_unit = None
            self.mode = "select"
            self._calc_highlights()
            return
        
        # Hareket / saldırı butonları
        if self.selected_unit and self.selected_unit.team == "player":
            if hasattr(self, '_move_btn') and self._move_btn and self._in_rect(mx, my, self._move_btn):
                if self.selected_unit.can_move():
                    self.mode = "move" if self.mode != "move" else "select"
                    self._calc_highlights()
                return
            if hasattr(self, '_attack_btn') and self._attack_btn and self._in_rect(mx, my, self._attack_btn):
                if self.selected_unit.can_attack():
                    self.mode = "attack" if self.mode != "attack" else "select"
                    self._calc_highlights()
                return
        
        # Harita tıklama
        if mx >= GRID_COLS*GRID_SIZE or my < 52 or my >= SCREEN_H:
            return
        if my < 52:
            return
        actual_y = my
        gx, gy = mx // GRID_SIZE, actual_y // GRID_SIZE
        if gx >= GRID_COLS or gy >= GRID_ROWS:
            return
        
        if self.mode == "move" and self.selected_unit:
            if (gx, gy) in self.highlight_cells:
                self._move_unit(self.selected_unit, gx, gy)
                self.mode = "select"
                self._calc_highlights()
            else:
                self.mode = "select"
                self._calc_highlights()
            return
        
        if self.mode == "attack" and self.selected_unit:
            if (gx, gy) in self.attack_cells:
                target = self._unit_at(gx, gy, "enemy")
                if target:
                    self._do_attack(self.selected_unit, target)
                    self.mode = "select"
                    self._calc_highlights()
            else:
                self.mode = "select"
                self._calc_highlights()
            return
        
        # Birlik seç
        u = self._unit_at(gx, gy)
        if u and u.is_alive():
            self.selected_unit = u
            self.mode = "select"
            self._calc_highlights()
            team = "Senin" if u.team=="player" else "Düşman"
            self._add_message(f"[{team}] {u.defn.name} – HP:{u.hp}/{u.max_hp}", 90, SAND3)
        else:
            self.selected_unit = None
            self.mode = "select"
            self._calc_highlights()

    # ── Ana döngü ─────────────────────────────
    def run(self):
        while True:
            dt = self.clock.tick(FPS)
            events = pygame.event.get()
            
            for ev in events:
                if ev.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                
                if self.state == "menu":
                    if self.main_menu.is_enabled():
                        self.main_menu.update([ev])
                
                elif self.state in ("build","battle"):
                    if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                        mx, my = ev.pos
                        if self.state == "build":
                            self._handle_build_click(mx, my)
                        else:
                            self._handle_battle_click(mx, my)
                    
                    elif ev.type == pygame.KEYDOWN:
                        if ev.key == pygame.K_ESCAPE:
                            self.mode = "select"
                            self.selected_unit = None
                            self._calc_highlights()
                        elif ev.key == pygame.K_SPACE and self.state == "battle":
                            self._end_player_turn()
                            self.selected_unit = None
                            self.mode = "select"
                            self._calc_highlights()
                        elif ev.key == pygame.K_m and self.state == "battle" and self.selected_unit:
                            if self.selected_unit.team=="player" and self.selected_unit.can_move():
                                self.mode = "move"
                                self._calc_highlights()
                        elif ev.key == pygame.K_a and self.state == "battle" and self.selected_unit:
                            if self.selected_unit.team=="player" and self.selected_unit.can_attack():
                                self.mode = "attack"
                                self._calc_highlights()
                    
                    elif ev.type == pygame.MOUSEMOTION:
                        mx, my = ev.pos
                        if mx < GRID_COLS*GRID_SIZE:
                            gx, gy = mx // GRID_SIZE, my // GRID_SIZE
                            if 0<=gx<GRID_COLS and 0<=gy<GRID_ROWS:
                                self.hover_unit_info = self._unit_at(gx, gy)
                
                elif self.state == "game_over":
                    if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                        mx, my = ev.pos
                        if hasattr(self, '_restart_btn') and self._in_rect(mx, my, self._restart_btn):
                            self.state = "menu"
            
            # Mesajları güncelle
            self.messages = [[t, timer-1, c] for t,timer,c in self.messages if timer > 0]
            self._update_particles()
            
            # Ölü birimleri temizle
            self.units = [u for u in self.units if u.is_alive()]
            self.enemy_units = [u for u in self.enemy_units if u.is_alive()]
            
            # ─── ÇİZİM ───
            self.screen.fill((15, 10, 5))
            
            if self.state == "menu":
                self.main_menu.draw(self.screen)
            
            else:
                # Harita bölgesi
                map_area = pygame.Surface((GRID_COLS*GRID_SIZE, GRID_ROWS*GRID_SIZE))
                self._draw_grid(map_area)
                
                # Dekorasyonlar (basit)
                for cx, cy, dtype in self.deco:
                    px = cx*GRID_SIZE + GRID_SIZE//2
                    py = cy*GRID_SIZE + GRID_SIZE//2
                    if dtype == "rock":
                        pygame.draw.polygon(map_area, STONE, [(px,py-8),(px+10,py+6),(px-10,py+6)])
                    elif dtype == "crater":
                        pygame.draw.circle(map_area, DARK_SAND, (px,py), 12, 3)
                
                for u in self.enemy_units + self.units:
                    self._draw_unit(map_area, u)
                
                self._draw_particles(map_area)
                self.screen.blit(map_area, (0, 52))
                
                self._draw_hud(self.screen)
                self._draw_side_panel(self.screen)
                self._draw_battle_log(self.screen)
                self._draw_messages(self.screen)
                self._draw_mode_indicator(self.screen)
                
                # Hover bilgisi
                if self.hover_unit_info and self.hover_unit_info != self.selected_unit:
                    u = self.hover_unit_info
                    mx, my = pygame.mouse.get_pos()
                    tip = f"{u.defn.name} | HP:{u.hp}/{u.max_hp} | ATK:{u.defn.atk}"
                    tw = self.font_xs.size(tip)[0] + 12
                    tx = min(mx+10, SCREEN_W-tw-10)
                    ty = max(my-28, 55)
                    draw_rounded_rect(self.screen, (20,15,8,220), (tx-4,ty-4,tw,24), radius=4)
                    draw_text(self.screen, tip, tx, ty, self.font_xs, SAND2, shadow=False)
                
                if self.state == "game_over":
                    self._draw_game_over(self.screen)
            
            pygame.display.flip()


if __name__ == "__main__":
    game = DesertCommand()
    game.run()