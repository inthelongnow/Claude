# Neurofeedback Client Guide

An unbranded, interactive walk-through for explaining neurofeedback and heart-rate variability biofeedback to adult clients, in the office or over a shared screen.

## Using it

Open `dist/neurofeedback-guide.html` in Chrome or Edge. It is one self-contained file: it works offline and can be copied anywhere.

- The menu on the left lists the sections. Left and right arrow keys also move between them.
- **Hide menu**, **Larger text** and **Full screen** are for presenting. **Light / dark** switches theme.
- Every moving figure has a **Pause** button.
- For a live heart-rate trace, open the saved file in Chrome or Edge on a computer, go to Heart and breath, and choose **Chest strap**. Any strap that sends beat-to-beat intervals over the standard Bluetooth heart-rate profile should work.

## Sections

| Section | What it covers |
|---|---|
| Start here | What neurofeedback is, in three points, and the list of questions |
| Brain rhythms | One signal separated into rhythms; states; a zoomed-out view that reveals the infra-slow range |
| Sensors and signal | The 10-20 map, a training pair or a full brain map, and what blinks and jaw tension do to the signal |
| What shifts them | Sleep, caffeine, alcohol, medication and practices, each with how solid the evidence is |
| How training works | The feedback loop, with a try-it demo of target-based and continuous feedback |
| Kinds of training | Brain map, infra-low frequency, frequency-band, synchrony and Alpha-Theta on one scale |
| Your sessions | The hour, the path from first meeting, a block planner, what to notice, the client's part |
| What research says | Evidence by concern and by method, where research is heading |
| Heart and breath | Live or simulated heart rate, a breathing pacer, and a log for finding a pace |

## Editing

The page is assembled from the files in `src/`:

- `src/modules/*.html` holds one file per section (text, styles and behaviour together).
- `src/app.css` holds the shared look, including all colours at the top.
- `src/core.js` holds navigation, theme and the simulated EEG.

After changing anything, rebuild:

```bash
python3 build.py
```

To add a section (for example Z-score training), copy an existing module file, give its `<section>` a new `id`, `data-nav` and `data-group`, and rebuild. Files are included in name order, which sets the menu order.

`AUDIT.md` records what was wrong with the original pages and what to check before using this one with clients.
