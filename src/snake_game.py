# -*- coding: utf-8 -*-
"""
经典像素贪吃蛇  ——  YITALE™ TaletaleGAMES
- 启动画面：蓝色楷体大字 YITALE™ TaletaleGAMES，按任意键开始
- 游戏：像素块、黑底+淡灰网格、黑色蛇身、#222 蛇头、蓝色食物
- 窗口/任务栏图标：Win10 风格圆润灰色设置齿轮（图标内嵌，单文件即可显示）
"""
import os
import sys
import random
import base64
import tempfile
import tkinter as tk

# ==================== 内嵌图标 (gear_win10.ico, base64) ====================
GEAR_ICO_B64 = "AAABAAEAEBAAAAAAIABpAwAAFgAAAIlQTkcNChoKAAAADUlIRFIAAAAQAAAAEAgGAAAAH/P/YQAAAzBJREFUeJyVk71PI1cUxc97b2AcssYjRusZhGVscJNgoaRb5AYLN2znSFaqlIitoi3SOFEaN4nQFtukS/4BlMhAgWy5CpBBcggycaAhYGvixJ6xB9uYjTSej5dmrZAyR7rS/V1d6RbnHuCROOfkMddqtU/29/efPZ7t7u6yxyxMmrOzsylCiHN4ePg0Eom8oJQ+55w/U1V1XK/Xf/E8r9Tr9b7LZDJ/cs4pIcQHADK5aprmu91u93vHcT7wfV+5ublBt9v1GWNUlmXEYjEEAoF+r9fbSafTX1NK4fs+COdcIIS4mqblZFnevbi4gK7rbjgcpqqqUgC80+lw0zT9aDQqJJNJmKb58fr6+kEulyMCIcStVCqhmZmZb+r1ut9qtXgqlRJEUYSu6wBAkskksW2bnp6e+owxLCwsfJtKpZ4DOCW6rs/d3d19OR6PXx4dHXmpVIqNRiMUi0VYlgUAkGUZ2WwWs7OzODk5cdPptNDv97/KZDKf09Fo9OH09PTLq6srX1EUFggEUCwWMRgMEIlEEIlEMBgMUCwWIYoiFEWh19fXfG5uLlepVGR6fn7+82g0MhzHoeFwmDebTViWBVVV4bouXNeFqqqwLAvNZhPhcJjc398T27aflkqlWRoKhaYJIQLnHP9HnHNeLpffo+12e8gYu5EkiRuGwWOxGGRZRqfTgSAIEAQBnU4HEysNw+CSJHHHcYxms3lPt7e3HQA/JhIJYpqmb9s2stksJElCq9VCq9WCJEnIZrOwbRuGYfDl5WWi67r28PDwq8A5JwcHBz8lEokXi4uLM5qm+Wtra3Rra2tiI6LRKGzbhqZpfiwWw9TU1N/VavU3RVE8wjlnhBCvWq1+FAwGf7i8vESj0fAURSGKohAAMAyDG4bB4/E4W1lZwd7e3hf5fL4UDAZF8vadQQh5UigUPtvc3PwUgNRoNDAYDAAAkiQhHo+DMWaVy+XX+Xy+LIriE9u2/03f0tJS6Pb29k2hUIhvbGy8IoQsvi0+Ho//Gg6H/Z2dnVfHx8e/z8/PG+122wGA/8SXMQbP8yb4/urq6hKl1KvVan8AEAG8EwqFHobDYW2y9A9Zq4+a0f42JwAAAABJRU5ErkJggg=="


def load_icon():
    """解码内嵌 ico，返回临时文件路径（进程结束时自动清理）"""
    if not GEAR_ICO_B64 or GEAR_ICO_B64 == "__BASE64__":
        return None
    try:
        data = base64.b64decode(GEAR_ICO_B64)
        if len(data) < 4:
            return None
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".ico")
        tmp.write(data)
        tmp.close()
        return tmp.name
    except Exception:
        return None


# ==================== 游戏常量 ====================
CELL_SIZE = 20
GRID_W = 30
GRID_H = 22
WIDTH = CELL_SIZE * GRID_W
HEIGHT = CELL_SIZE * GRID_H

BG = "#FFFFFF"    # 背景：白色
GRID = "#000000"   # 网格线：黑色

SNAKE_HEAD = "#222222"   # 蛇头：深灰（比纯黑亮一档，辨认朝向）
SNAKE_BODY = "#000000"   # 蛇身：纯黑
FOOD = "#2266ff"         # 食物：蓝色

SPEED_START = 120  # ms/帧


class SnakeGame:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("贪吃蛇  YITALE\u2122 TaletaleGAMES")
        self.root.resizable(False, False)

        # 图标
        self._icon_path = load_icon()
        if self._icon_path and os.path.exists(self._icon_path):
            try:
                self.root.iconbitmap(self._icon_path)
            except Exception:
                pass

        self.canvas = tk.Canvas(self.root, width=WIDTH, height=HEIGHT,
                                bg=BG, highlightthickness=0)
        self.canvas.pack()

        self.snake = []
        self.dir = (1, 0)
        self.pending = (1, 0)
        self.food = (0, 0)
        self.score = 0
        self.high_score = self._load_high()
        self.running = False
        self.paused = False
        self.game_over = False
        self._splash = False
        self._after_id = None

        self._bind_keys()
        self._show_splash()

        # 退出时清理临时 ico
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ---------------- 持久化 ----------------
    def _hs_path(self):
        base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base, "snake_highscore.txt")

    def _load_high(self):
        try:
            with open(self._hs_path(), "r", encoding="utf-8") as f:
                return int(f.read().strip() or 0)
        except Exception:
            return 0

    def _save_high(self):
        try:
            with open(self._hs_path(), "w", encoding="utf-8") as f:
                f.write(str(self.high_score))
        except Exception:
            pass

    # ---------------- 启动画面 ----------------
    def _show_splash(self):
        self.canvas.delete("all")
        cx, cy = WIDTH // 2, HEIGHT // 2
        self.canvas.create_text(cx, cy - 30, text="YITALE\u2122",
                                font=("KaiTi", 48, "bold"), fill="#2266ff")
        self.canvas.create_text(cx, cy + 28, text="TaletaleGAMES",
                                font=("KaiTi", 30, "bold"), fill="#2266ff")
        self.canvas.create_text(cx, HEIGHT - 40, text="按WASD、↑↓←→开始",
                                font=("微软雅黑", 13), fill="#888888")
        self._splash = True

    def _start_from_splash(self, event=None):
        if not self._splash:
            return
        self._splash = False
        self.reset()
        self.running = True
        self._tick()

    # ---------------- 重置 / 开始 ----------------
    def reset(self):
        cx, cy = GRID_W // 2, GRID_H // 2
        self.snake = [(cx - 2, cy), (cx - 1, cy), (cx, cy)]
        self.dir = (1, 0)
        self.pending = (1, 0)
        self.score = 0
        self.paused = False
        self.game_over = False
        self._spawn_food()

    def _spawn_food(self):
        occupied = set(self.snake)
        empty = [(x, y) for x in range(GRID_W) for y in range(GRID_H)
                 if (x, y) not in occupied]
        self.food = random.choice(empty) if empty else (0, 0)

    # ---------------- 输入 ----------------
    def _bind_keys(self):
        binds = {
            "<Left>": lambda e: self._set_dir((-1, 0)),
            "<Right>": lambda e: self._set_dir((1, 0)),
            "<Up>": lambda e: self._set_dir((0, -1)),
            "<Down>": lambda e: self._set_dir((0, 1)),
            "<a>": lambda e: self._set_dir((-1, 0)),
            "<d>": lambda e: self._set_dir((1, 0)),
            "<w>": lambda e: self._set_dir((0, -1)),
            "<s>": lambda e: self._set_dir((0, 1)),
            "<A>": lambda e: self._set_dir((-1, 0)),
            "<D>": lambda e: self._set_dir((1, 0)),
            "<W>": lambda e: self._set_dir((0, -1)),
            "<S>": lambda e: self._set_dir((0, 1)),
            "<p>": lambda e: self.toggle_pause(),
            "<P>": lambda e: self.toggle_pause(),
            "<r>": lambda e: self._restart(),
            "<R>": lambda e: self._restart(),
            "<q>": lambda e: self._on_close(),
            "<Q>": lambda e: self._on_close(),
        }
        for key, fn in binds.items():
            self.root.bind(key, fn, add="+")

    def _set_dir(self, d):
        if self._splash:
            self._start_from_splash()
            return
        if self.game_over:
            return
        if not self.running or self.paused:
            return
        # 禁止 180° 回头
        if (d[0] != -self.dir[0] or d[1] != -self.dir[1]):
            self.pending = d

    def toggle_pause(self):
        if self.game_over or not self.running:
            return
        self.paused = not self.paused

    def _restart(self):
        if not self.game_over:
            return
        self.reset()
        self.running = True
        self._tick()

    # ---------------- 主循环 ----------------
    def _tick(self):
        if self._after_id:
            self.root.after_cancel(self._after_id)
        if not self.running or self.paused or self.game_over:
            return
        self.dir = self.pending
        hx, hy = self.snake[-1]
        nx, ny = hx + self.dir[0], hy + self.dir[1]

        # 撞墙 / 咬自己
        if (nx < 0 or ny < 0 or nx >= GRID_W or ny >= GRID_H or (nx, ny) in self.snake):
            self._game_over()
            return

        self.snake.append((nx, ny))
        if (nx, ny) == self.food:
            self.score += 10
            if self.score > self.high_score:
                self.high_score = self.score
                self._save_high()
            self._spawn_food()
        else:
            self.snake.pop(0)

        self._draw()
        delay = max(40, SPEED_START - (self.score // 50) * 10)
        self._after_id = self.root.after(delay, self._tick)

    def _draw(self):
        self.canvas.delete("all")
        # 淡灰网格
        for x in range(0, WIDTH, CELL_SIZE):
            self.canvas.create_line(x, 0, x, HEIGHT, fill=GRID)
        for y in range(0, HEIGHT, CELL_SIZE):
            self.canvas.create_line(0, y, WIDTH, y, fill=GRID)

        # 食物（蓝色方块，无边框）
        fx, fy = self.food
        self.canvas.create_rectangle(
            fx * CELL_SIZE, fy * CELL_SIZE,
            (fx + 1) * CELL_SIZE, (fy + 1) * CELL_SIZE,
            fill=FOOD, outline="")

        # 蛇身（黑色，无边框）
        for (sx, sy) in self.snake[:-1]:
            self.canvas.create_rectangle(
                sx * CELL_SIZE, sy * CELL_SIZE,
                (sx + 1) * CELL_SIZE, (sy + 1) * CELL_SIZE,
                fill=SNAKE_BODY, outline="")

        # 蛇头（#222，无边框）
        hx, hy = self.snake[-1]
        self.canvas.create_rectangle(
            hx * CELL_SIZE, hy * CELL_SIZE,
            (hx + 1) * CELL_SIZE, (hy + 1) * CELL_SIZE,
            fill=SNAKE_HEAD, outline="")

        # HUD
        self.canvas.create_text(8, 6, anchor="nw",
                               text="分数: {}   最高: {}".format(self.score, self.high_score),
                               font=("Courier", 12), fill="#aaaaaa")

        if self.paused:
            self.canvas.create_text(WIDTH // 2, HEIGHT // 2, text="暂停",
                                    font=("微软雅黑", 28), fill="#ffffff")

    def _game_over(self):
        self.game_over = True
        self.running = False
        self._draw()
        self.canvas.create_rectangle(WIDTH // 2 - 110, HEIGHT // 2 - 60,
                                     WIDTH // 2 + 110, HEIGHT // 2 + 60,
                                     fill="#111111", outline="#ffffff")
        self.canvas.create_text(WIDTH // 2, HEIGHT // 2 - 28, text="GAME OVER",
                                font=("Courier", 22, "bold"), fill="#ff3333")
        self.canvas.create_text(WIDTH // 2, HEIGHT // 2 + 2,
                                text="分数: {}".format(self.score),
                                font=("Courier", 14), fill="#ffffff")
        self.canvas.create_text(WIDTH // 2, HEIGHT // 2 + 26,
                                text="R 重开   Q 退出",
                                font=("Courier", 12), fill="#aaaaaa")

    # ---------------- 退出 ----------------
    def _on_close(self):
        try:
            if self._icon_path and os.path.exists(self._icon_path):
                os.unlink(self._icon_path)
        except Exception:
            pass
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    SnakeGame().run()
