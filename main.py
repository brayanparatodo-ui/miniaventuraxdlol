import random, math
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, Ellipse, Line, Triangle
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout

LEVELS = [
    {"name": "1 · Playa soleada", "sky": (0.28,0.78,0.98), "ground": (0.91,0.79,0.48), "top": (0.25,0.70,0.39), "enemy": "Cangrejos"},
    {"name": "2 · Cañón de espejismos", "sky": (0.96,0.60,0.36), "ground": (0.72,0.40,0.27), "top": (0.88,0.62,0.34), "enemy": "Aves"},
    {"name": "3 · Selva llena de vida", "sky": (0.47,0.82,0.60), "ground": (0.31,0.48,0.29), "top": (0.24,0.69,0.34), "enemy": "Monos"},
]
MASKS = {"default": ("Por defecto", (0.93,0.76,0.42)), "joker": ("Joker", (0.49,0.22,0.60)),
         "batman": ("Batman", (0.12,0.14,0.19)), "spiderman": ("Spider-Man", (0.83,0.15,0.20))}

class GameView(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.mode = "mobile"
        self.state = "menu"
        self.level_index = 0
        self.coins = 0
        self.score = 0
        self.lives = 5
        self.owned = {"default"}
        self.mask = "default"
        self.combo = []
        self.combo_used = False
        self.message = "Elige cómo quieres jugar"
        self.left = self.right = False
        self.attack_frames = 0
        self.cooldown = 0
        self.reset_level()
        Clock.schedule_interval(self.update, 1/60)

    def reset_level(self):
        self.px, self.py = 70.0, 0.0
        self.vy = 0
        self.grounded = False
        self.camera = 0
        self.gems = [{"x": x, "y": y, "got": False} for x,y in [(245,150),(450,210),(700,165),(925,220),(1160,155),(1390,200),(1620,160),(1850,215),(2010,170)]]
        self.enemies = [{"x": x, "alive": True, "dir": random.choice([-1,1])} for x in (340,590,810,1050,1280,1510,1740,1940)]
        self.drops = []
        self.combo = []
        self.combo_used = False
        self.state = "play"
        self.message = LEVELS[self.level_index]["name"]

    def on_touch_down(self, touch):
        x, y = touch.x, touch.y
        w, h = self.width, self.height
        if self.state == "menu":
            if y > h*0.35:
                self.state = "inventory"; self.message = "Elige una máscara y pulsa JUGAR"
            return True
        if self.state == "inventory":
            if y < h*0.22:
                if x < w*0.34:
                    self.mask = "default"
                elif x < w*0.55:
                    self.buy_mask("joker")
                elif x < w*0.76:
                    self.buy_mask("batman")
                else:
                    self.buy_mask("spiderman")
            else:
                self.reset_level()
            return True
        if self.state == "between":
            if x < w*0.5:
                self.state = "inventory"
            else:
                self.level_index += 1
                if self.level_index >= len(LEVELS):
                    self.state = "complete"
                else:
                    self.reset_level()
            return True
        if self.state in ("dead", "complete"):
            self.level_index = 0
            self.score = 0
            self.lives = 5
            self.reset_level()
            return True
        # Touch controls: left third moves left, middle third moves right,
        # upper-right jumps, lower-right attacks.
        if x < w*0.22:
            self.left = True
            self.combo_step("backward")
        elif x < w*0.44:
            self.right = True
            self.combo_step("forward")
        elif y > h*0.58:
            self.jump()
        else:
            self.attack()
        return True

    def on_touch_up(self, touch):
        self.left = self.right = False
        return True

    def buy_mask(self, name):
        if name in self.owned:
            self.mask = name
            self.message = "Máscara equipada"
        elif self.coins >= 7:
            self.coins -= 7
            self.owned.add(name)
            self.mask = name
            self.message = "¡Máscara desbloqueada!"
        else:
            self.message = "Necesitas 7 monedas"

    def jump(self):
        if self.state == "play" and self.grounded:
            self.vy = 9.5
            self.grounded = False

    def attack(self):
        if self.state == "play" and self.cooldown <= 0:
            self.attack_frames = 12
            self.cooldown = 80
            self.combo_step("hit")
            for en in self.enemies:
                if en["alive"] and abs(en["x"] - self.px) < 75:
                    en["alive"] = False
                    self.score += 2
                    if self.level_index == 0 and random.random() < .4:
                        self.drops.append({"x":en["x"], "got":False})
            if self.level_index == 0 and not self.combo_used and self.combo[-5:] == ["forward","forward","backward","backward","hit"]:
                for en in self.enemies:
                    en["alive"] = False
                self.drops.extend([{"x": self.px+100+i*35, "got":False} for i in range(3)])
                self.combo_used = True
                self.message = "¡COMBO ESPECIAL! Cangrejos derrotados; 3 monedas"
                self.combo = []

    def combo_step(self, step):
        self.combo.append(step)
        self.combo = self.combo[-5:]

    def update(self, dt):
        if self.state != "play":
            self.draw()
            return
        direction = (-1 if self.left else 0) + (1 if self.right else 0)
        self.px = max(15, min(2070, self.px + direction*4.0))
        self.vy -= 0.48
        self.py += self.vy
        if self.py <= 0:
            self.py = 0
            self.vy = 0
            self.grounded = True
        for gem in self.gems:
            if not gem["got"] and abs(gem["x"]-self.px) < 24 and abs(gem["y"]-(self.py+35)) < 45:
                gem["got"] = True
                self.score += 1
        for drop in self.drops:
            if not drop["got"] and abs(drop["x"]-self.px) < 28:
                drop["got"] = True
                self.coins += 1
                self.message = "¡Moneda recogida!"
        for en in self.enemies:
            if en["alive"]:
                en["x"] += en["dir"]*1.1
                if en["x"] < 300 or en["x"] > 2000:
                    en["dir"] *= -1
        if self.cooldown > 0: self.cooldown -= 1
        if self.attack_frames > 0: self.attack_frames -= 1
        if self.px > 2030:
            if all(g["got"] for g in self.gems):
                if self.level_index < 2:
                    self.state = "between"
                    self.message = "¡Nivel completado!"
                else:
                    self.state = "complete"
            else:
                self.px = 1995
                self.message = "Recoge todas las gemas para abrir el portal"
        self.camera = max(0, min(2100-self.width, self.px-self.width*0.35))
        self.draw()

    def draw(self):
        self.canvas.clear()
        with self.canvas:
            w,h = self.width,self.height
            if w <= 1 or h <= 1: return
            if self.state == "menu":
                Color(.08,.20,.30,1); Rectangle(pos=self.pos,size=self.size)
                Color(1,.92,.56,1); self.text("MINIAVENTURA", w*.5,h*.68, max(22,h*.08))
                Color(1,1,1,1); self.text("Toca la pantalla para comenzar", w*.5,h*.45,max(14,h*.035))
                self.text("3 mundos · máscaras · monedas", w*.5,h*.34,max(12,h*.028))
                return
            if self.state == "inventory":
                Color(.08,.15,.20,1); Rectangle(pos=self.pos,size=self.size)
                Color(1,.92,.56,1); self.text("INVENTARIO DE MÁSCARAS",w*.5,h*.82,max(18,h*.05))
                Color(1,1,1,1); self.text("Monedas: %d · Cada máscara cuesta 7"%self.coins,w*.5,h*.72,max(12,h*.03))
                names=list(MASKS.keys())
                for i,name in enumerate(names):
                    x=w*(.125+i*.25)
                    col=MASKS[name][1]
                    Color(*col,1); Ellipse(pos=(x-w*.045,h*.43),size=(w*.09,w*.09))
                    Color(1,1,1,1); self.text(MASKS[name][0],x,h*.34,max(10,h*.023))
                    self.text("EQUIPADA" if self.mask==name else ("DESBLOQUEADA" if name in self.owned else "7 monedas"),x,h*.28,max(8,h*.018))
                Color(.15,.55,.32,1); Rectangle(pos=(w*.32,h*.06),size=(w*.36,h*.12))
                Color(1,1,1,1); self.text("JUGAR",w*.5,h*.12,max(14,h*.035))
                return
            level = LEVELS[self.level_index]
            Color(*level["sky"],1); Rectangle(pos=self.pos,size=self.size)
            cam = self.camera
            ground_y = h*.20
            Color(*level["ground"],1); Rectangle(pos=(0,0),size=(w,ground_y))
            Color(*level["top"],1); Rectangle(pos=(0,ground_y),size=(w,h*.018))
            # Platforms
            for xx, yy, ww in [(200, .37,125),(405,.48,135),(650,.40,145),(880,.51,145),(1110,.37,145),(1340,.46,150),(1570,.37,150),(1800,.49,150)]:
                sx=xx-cam
                if -ww < sx < w:
                    Color(*level["ground"],1); Rectangle(pos=(sx,ground_y+(yy-.2)*h),size=(ww/2100*w*3,(.025*h)))
            # Gems
            for gem in self.gems:
                if not gem["got"]:
                    sx=(gem["x"]-cam)/2100*w*3
                    if -20<sx<w+20:
                        Color(.20,.88,1,1); Ellipse(pos=(sx,ground_y+gem["y"]*.55),size=(12,18))
            # Coin drops
            for drop in self.drops:
                if not drop["got"]:
                    sx=(drop["x"]-cam)/2100*w*3
                    if -20<sx<w+20:
                        Color(1,.75,.10,1); Ellipse(pos=(sx,ground_y+8),size=(16,16))
            # Enemies
            for en in self.enemies:
                if en["alive"]:
                    sx=(en["x"]-cam)/2100*w*3
                    if -30<sx<w+30:
                        Color(.90,.25,.22,1); Ellipse(pos=(sx,ground_y+8),size=(30,22))
                        Color(1,1,1,1); Ellipse(pos=(sx+7,ground_y+22),size=(6,6)); Ellipse(pos=(sx+19,ground_y+22),size=(6,6))
            # Player
            px=(self.px-cam)/2100*w*3
            py=ground_y+self.py+5
            Color(.93,.76,.42,1); Rectangle(pos=(px,py),size=(24,42))
            Color(*MASKS[self.mask][1],1); Rectangle(pos=(px-1,py+25),size=(26,10))
            Color(.12,.12,.12,1); Rectangle(pos=(px+5,py-5),size=(5,12)); Rectangle(pos=(px+15,py-5),size=(5,12))
            # HUD and overlays
            Color(.04,.09,.14,.85); Rectangle(pos=(5,h-58),size=(w-10,52))
            Color(1,1,1,1)
            self.text("%s  |  Puntos: %d  |  Gemas: %d/9  |  Monedas: %d  |  Vidas: %d" %
                      (level["name"],self.score,sum(g["got"] for g in self.gems),self.coins,self.lives),w*.5,h-32,max(9,h*.023))
            if self.state == "between":
                Color(.02,.04,.08,.88); Rectangle(pos=(0,0),size=(w,h))
                Color(1,1,1,1); self.text("¡NIVEL COMPLETADO!",w*.5,h*.68,max(20,h*.055))
                self.text("Monedas guardadas: %d"%self.coins,w*.5,h*.57,max(12,h*.03))
                self.text("Toca izquierda: máscaras   ·   Toca derecha: siguiente nivel",w*.5,h*.37,max(10,h*.024))
            elif self.state == "complete":
                Color(.02,.04,.08,.9); Rectangle(pos=(0,0),size=(w,h))
                Color(1,.92,.56,1); self.text("¡AVENTURA COMPLETADA!",w*.5,h*.58,max(20,h*.055))
                Color(1,1,1,1); self.text("Toca para volver a jugar",w*.5,h*.40,max(12,h*.03))
            elif self.state == "dead":
                Color(.02,.04,.08,.9); Rectangle(pos=(0,0),size=(w,h))
                Color(1,1,1,1); self.text("FIN DE LA PARTIDA · toca para reiniciar",w*.5,h*.5,max(14,h*.035))

    def text(self, s, x, y, size):
        from kivy.core.text import Label as CoreLabel
        lab = CoreLabel(text=s, font_size=size, halign="center", valign="middle")
        lab.refresh()
        tex = lab.texture
        Rectangle(texture=tex, pos=(x-tex.width/2,y-tex.height/2), size=tex.size)

class MiniAventuraApp(App):
    def build(self):
        Window.clearcolor = (0.05,0.1,0.15,1)
        root = FloatLayout()
        self.game = GameView(size_hint=(1,1))
        root.add_widget(self.game)
        # Touch regions are handled by GameView. These labels explain controls.
        hint = Label(text="IZQUIERDA ◀     DERECHA ▶     ZONA SUPERIOR: SALTO     ZONA INFERIOR: ATAQUE",
                     size_hint=(1,.07), pos_hint={"x":0,"y":0}, font_size="10sp",
                     color=(1,1,1,.9))
        root.add_widget(hint)
        return root

if __name__ == "__main__":
    MiniAventuraApp().run()
