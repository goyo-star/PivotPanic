# 🎯 PivotPanic - You vs. QuickSort

> Mate, fancy a proper challenge? This isn’t your nan’s sorting visualiser - it’s you vs. QuickSort in a full‑on race.

<p align="center">
<img src="demo.gif" alt="Gameplay demo" width="720" />
</p>

---

## 🎮 What’s the Craic?

I got bored of just *watching* arrays get sorted - so I thought, why not jump in and have a go myself?
In **PivotPanic**, you’re on the left panel, swapping bars with your mouse, trying to beat QuickSort running on the right.

You’ve got a timer, you’ve got swaps to count, and you’ve got bragging rights if you finish first. 🏆

---

## 🕹 Controls

| Key / Action      | What It Does                                       |
| ----------------- | -------------------------------------------------- |
| 🖱 Click two bars | Swap ’em. Nice and simple.                         |
| **R**             | Restart with a fresh shuffle (same for both sides) |
| **1 / 2 / 3**     | Pick your poison: 12 / 24 / 36 bars                |
| **SPACE**         | Pause QuickSort if you need a cheeky breather      |
| **ESC / Q**       | Bail out                                           |

> ✅ As soon as either side’s sorted, the clock stops — winner takes the glory.

---

## 🚀 Getting Started

Right, here’s what you do:

```bash
git clone https://github.com/Rayaan2009/PivotPanic.git
cd PivotPanic

python -m venv .venv && source .venv/bin/activate  # optional but tidy

pip install pygame

python pivotpanic.py
```

Runs on Python 3.10+, no fuss.

---

## 🔧 Under the Bonnet

* QuickSort’s running Lomuto partition under the hood, step‑by‑step.
* Each compare / swap / pivot is yielded for a smooth animation.
* Pygame’s doing all the graphics and input magic at 60 FPS.
* Tracks your time and swaps, then throws up a results screen when it’s all over.

---

## 🗺 Future Shenanigans

* Add sound effects & flashy particles when you swap (make it feel *spicy*)
* Bigger arrays for absolute chaos
* Maybe throw in MergeSort, HeapSort, BubbleSort just for a laugh
* Global leaderboard? Let’s make this competitive 👀

---

## 📝 License

MIT — go wild, just don’t nick the credit.

---

<p align="center">
Made with ❤️ by <strong>Rayaan2009</strong>
</p>

Now get in there and show QuickSort who’s boss. And no sulking if it beats you, alright? 😉
