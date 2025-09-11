#!/usr/bin/env python3
"""
You vs QuickSort, a gamified sorting visualizer.

Left panel: YOU
- Click a bar to select it, then click another bar to swap.
- Goal: sort ascending.

Right panel: QuickSort (Lomuto partition)
- Visualized step-by-step at a steady pace.

Controls
--------
R : restart with a fresh shuffled array (same array for both sides)
1 : small  (12 items)
2 : medium (24 items)
3 : large  (36 items)
SPACE : pause/resume the algorithm side (you can still play)
ESC or Q : quit

Win Condition
-------------
As soon as either side is fully sorted, we stop the clock for that side.
When both sides are done (or time is up), a results overlay appears.

Built with Python 3.10+ and Pygame.
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Generator, List, Optional, Tuple

import pygame


# -------------------------------- Config -------------------------------- #

WIDTH, HEIGHT = 1100, 640
MARGIN = 16
PANEL_GAP = 12

BG = (18, 18, 22)
INK = (235, 235, 235)
INK_DIM = (165, 165, 175)
GREEN = (56, 200, 120)
RED = (230, 80, 90)
AMBER = (250, 190, 80)
BLUE = (120, 160, 255)
PURPLE = (155, 120, 255)
GREY_BAR = (70, 72, 80)

FPS = 60

# Algorithm stepping speed (visual pacing)
ALGO_STEPS_PER_SEC = 24  # higher = faster QuickSort animation
HIGHLIGHT_FADE_SEC = 0.30

# Difficulty presets (array sizes)
SIZES = {
    pygame.K_1: 12,
    pygame.K_2: 24,
    pygame.K_3: 36,
}

FONT_NAME = "fira mono, consolas, menlo, monospace"


# ------------------------------ Utilities ------------------------------ #

def is_sorted(arr: List[int]) -> bool:
    return all(arr[i] <= arr[i + 1] for i in range(len(arr) - 1))


def new_array(n: int) -> List[int]:
    """Create distinct values so bar order is unambiguous."""
    # 10..(10 + n*5) spaced for nice height differences
    values = list(range(10, 10 + n * 5, 5))
    random.shuffle(values)
    return values


# ------------------------ QuickSort step generator ---------------------- #

@dataclass
class Step:
    """Represents a single visualization step of QuickSort."""
    array: List[int]
    i: Optional[int] = None
    j: Optional[int] = None
    pivot_index: Optional[int] = None
    action: str = ""  # "compare", "swap", "partition", "pivot"


def quicksort_steps(data: List[int]) -> Generator[Step, None, None]:
    """
    Lomuto partition QuickSort, yielding Step objects frequently for visualization.
    We copy the working array when yielding so the UI can render the exact frame.
    """
    arr = data[:]  # local working copy

    def _partition(lo: int, hi: int) -> Generator[Step, None, int]:
        pivot = arr[hi]
        i = lo - 1
        # announce pivot
        yield Step(arr[:], pivot_index=hi, action="pivot")
        for j in range(lo, hi):
            # comparison step
            yield Step(arr[:], i=i, j=j, pivot_index=hi, action="compare")
            if arr[j] <= pivot:
                i += 1
                if i != j:
                    arr[i], arr[j] = arr[j], arr[i]
                    # swap step
                    yield Step(arr[:], i=i, j=j, pivot_index=hi, action="swap")
        # put pivot in correct place
        if i + 1 != hi:
            arr[i + 1], arr[hi] = arr[hi], arr[i + 1]
            yield Step(arr[:], i=i + 1, j=hi, pivot_index=hi, action="partition")
        return i + 1

    def _quicksort(lo: int, hi: int):
        if lo < hi:
            # partition and recurse
            p = yield from _partition(lo, hi)
            yield from _quicksort(lo, p - 1)
            yield from _quicksort(p + 1, hi)

    if arr:
        yield from _quicksort(0, len(arr) - 1)
    # final state
    yield Step(arr[:], action="done")


# ------------------------------ Rendering ------------------------------ #

@dataclass
class Panel:
    rect: pygame.Rect
    title: str
    accent: Tuple[int, int, int]


class Drawer:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.font_small = pygame.font.SysFont(FONT_NAME, 18)
        self.font = pygame.font.SysFont(FONT_NAME, 22, bold=True)
        self.font_big = pygame.font.SysFont(FONT_NAME, 36, bold=True)

    def draw_panel_frame(self, p: Panel):
        pygame.draw.rect(self.screen, (28, 28, 34), p.rect, border_radius=10)
        inner = p.rect.inflate(-8, -8)
        pygame.draw.rect(self.screen, (36, 36, 44), inner, border_radius=10)
        title_surf = self.font.render(p.title, True, INK)
        self.screen.blit(title_surf, (inner.x + 12, inner.y + 8))

    def bars(self, p: Panel, arr: List[int], highlight: Step | None, selected_idx: Optional[int]):
        inner = p.rect.inflate(-24, -56)
        inner.y += 12
        inner.h -= 12

        n = len(arr)
        if n == 0:
            return

        w = inner.w / n
        unit = (inner.h - 8) / (max(arr) - min(arr) + 1)

        for idx, val in enumerate(arr):
            x = inner.x + idx * w
            h = (val - min(arr) + 1) * unit
            y = inner.bottom - h
            r = pygame.Rect(int(x + 2), int(y), max(1, int(w - 4)), int(h))

            color = GREY_BAR
            # Selection highlight (player side)
            if selected_idx is not None and idx == selected_idx:
                color = BLUE

            # Algorithm highlights (algo side)
            if highlight:
                if idx == highlight.pivot_index and highlight.action != "done":
                    color = AMBER
                if idx == highlight.i:
                    color = PURPLE
                if idx == highlight.j:
                    color = p.accent  # accent color for active compare/swap

            pygame.draw.rect(self.screen, color, r, border_radius=3)

        # axis baseline
        pygame.draw.line(self.screen, (80, 80, 90), (inner.x, inner.bottom), (inner.right, inner.bottom), 1)

    def hud(self, p: Panel, time_sec: float, moves: int, done: bool):
        inner = p.rect.inflate(-24, -56)
        text = f"⏱ {time_sec:5.2f}s   •   ↔ swaps {moves}"
        if done:
            text += "   •   ✅ done"
        surf = self.font_small.render(text, True, INK_DIM if not done else GREEN)
        self.screen.blit(surf, (inner.x, p.rect.bottom - 32))

    def overlay_results(self, winner_text: str, subtext: str):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        t1 = self.font_big.render(winner_text, True, INK)
        t2 = self.font.render(subtext, True, INK_DIM)
        self.screen.blit(t1, t1.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 12)))
        self.screen.blit(t2, t2.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 28)))

    def footer(self):
        msg = "R = restart   1/2/3 = size   SPACE = pause algo   ESC/Q = quit"
        surf = self.font_small.render(msg, True, INK_DIM)
        self.screen.blit(surf, (MARGIN, HEIGHT - MARGIN - 18))


# ------------------------------ Game State ----------------------------- #

@dataclass
class SideState:
    arr: List[int]
    start_time: float = 0.0
    finish_time: Optional[float] = None
    moves: int = 0
    selected: Optional[int] = None  # for player side


class YouVsQuickSort:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("You vs QuickSort — interactive visualizer")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.drawer = Drawer(self.screen)

        # panels
        total_inner_w = WIDTH - 2 * MARGIN - PANEL_GAP
        panel_w = total_inner_w // 2
        panel_h = HEIGHT - 2 * MARGIN
        left_rect = pygame.Rect(MARGIN, MARGIN, panel_w, panel_h)
        right_rect = pygame.Rect(MARGIN + panel_w + PANEL_GAP, MARGIN, panel_w, panel_h)
        self.player_panel = Panel(left_rect, "You", accent=GREEN)
        self.algo_panel = Panel(right_rect, "QuickSort", accent=RED)

        # runtime
        self.size = SIZES[pygame.K_2]  # default medium
        self.paused_algo = False
        self._algo_step_timer = 0.0

        # highlights
        self._last_step_time = 0.0
        self._current_step: Optional[Step] = None

        # init arrays
        self.reset(full=True)

    # ------------------------- Lifecycle ------------------------- #

    def reset(self, *, full: bool):
        base = new_array(self.size)
        self.player = SideState(arr=base[:], start_time=time.perf_counter())
        self.algo = SideState(arr=base[:], start_time=time.perf_counter())

        # algorithm generator
        self._gen = quicksort_steps(self.algo.arr)
        self._current_step = None
        self._algo_step_timer = 0.0
        self._last_step_time = 0.0
        self.paused_algo = False

    # --------------------------- Events -------------------------- #

    def handle_events(self) -> bool:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return False
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_ESCAPE, pygame.K_q):
                    return False
                if e.key == pygame.K_r:
                    self.reset(full=True)
                if e.key in SIZES:
                    self.size = SIZES[e.key]
                    self.reset(full=True)
                if e.key == pygame.K_SPACE:
                    self.paused_algo = not self.paused_algo

            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                self._handle_click(e.pos)

        return True

    def _index_at_pos(self, p: Panel, arr: List[int], pos: Tuple[int, int]) -> Optional[int]:
        inner = p.rect.inflate(-24, -56)
        inner.y += 12
        inner.h -= 12
        if not inner.collidepoint(pos):
            return None
        n = len(arr)
        if n == 0:
            return None
        w = inner.w / n
        rel_x = pos[0] - inner.x
        idx = int(rel_x // w)
        return max(0, min(n - 1, idx))

    def _handle_click(self, pos: Tuple[int, int]):
        # only the left panel is interactive
        idx = self._index_at_pos(self.player_panel, self.player.arr, pos)
        if idx is None or self.player.finish_time is not None:
            return
        if self.player.selected is None:
            self.player.selected = idx
        else:
            if idx != self.player.selected:
                self.player.arr[self.player.selected], self.player.arr[idx] = (
                    self.player.arr[idx],
                    self.player.arr[self.player.selected],
                )
                self.player.moves += 1
                if is_sorted(self.player.arr) and self.player.finish_time is None:
                    self.player.finish_time = time.perf_counter()
            # clear selection either way
            self.player.selected = None

    # --------------------------- Update -------------------------- #

    def update_algo(self, dt: float):
        if self.algo.finish_time is not None or self.paused_algo:
            return

        # pace generator by steps per sec
        self._algo_step_timer += dt
        step_interval = 1.0 / ALGO_STEPS_PER_SEC
        while self._algo_step_timer >= step_interval:
            self._algo_step_timer -= step_interval
            try:
                step = next(self._gen)
                self.algo.arr = step.array[:]  # sync
                self._current_step = step
                self._last_step_time = time.perf_counter()
                if step.action == "done" and self.algo.finish_time is None:
                    self.algo.finish_time = time.perf_counter()
            except StopIteration:
                if self.algo.finish_time is None:
                    self.algo.finish_time = time.perf_counter()
                break

    # --------------------------- Draw ---------------------------- #

    def draw(self):
        self.screen.fill(BG)

        # frames
        self.drawer.draw_panel_frame(self.player_panel)
        self.drawer.draw_panel_frame(self.algo_panel)

        # highlight fades shortly after a step to keep UI lively
        highlight = None
        if self._current_step:
            if time.perf_counter() - self._last_step_time <= HIGHLIGHT_FADE_SEC:
                highlight = self._current_step

        # bars
        self.drawer.bars(self.player_panel, self.player.arr, None, self.player.selected)
        self.drawer.bars(self.algo_panel, self.algo.arr, highlight, None)

        # HUDs
        now = time.perf_counter()
        p_time = (self.player.finish_time or now) - self.player.start_time
        a_time = (self.algo.finish_time or now) - self.algo.start_time
        self.drawer.hud(self.player_panel, p_time, self.player.moves, self.player.finish_time is not None)
        self.drawer.hud(self.algo_panel, a_time, 0, self.algo.finish_time is not None)

        # footer
        self.drawer.footer()

        # results overlay when both finished
        if self.player.finish_time is not None and self.algo.finish_time is not None:
            winner = "You win! 🎉" if (p_time < a_time) else ("QuickSort wins! 🤖" if a_time < p_time else "It’s a tie! ⚖")
            details = f"You: {p_time:.2f}s, {self.player.moves} swaps   •   QuickSort: {a_time:.2f}s"
            self.drawer.overlay_results(winner, details)

        pygame.display.flip()

    # --------------------------- Loop ---------------------------- #

    def run(self):
        while True:
            if not self.handle_events():
                break
            dt = self.clock.tick(FPS) / 1000.0
            self.update_algo(dt)

            # if player finishes later, capture finish time
            if self.player.finish_time is None and is_sorted(self.player.arr):
                self.player.finish_time = time.perf_counter()

            self.draw()

        pygame.quit()


# --------------------------------- Main -------------------------------- #

if __name__ == "__main__":
    YouVsQuickSort().run()
