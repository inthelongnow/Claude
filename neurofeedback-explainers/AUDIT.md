# Audit of the original explainer pages

Reviewed November 2026. Five files were supplied: three pages built for the practice (Brainwave Prism, What Moves Your Brainwaves, Heartbeat Live) and two saved web pages from learningeeg.com.

Scientific claims were checked against published reviews and controlled studies using Consensus (about 40 searches), and method descriptions against the books in the "Neurofeedback Books" Drive folder. The Drive reader returned only the opening chapters of each book, so the how-to chapters could not be checked. Paper links are in the "Sources and notes" list at the foot of each section of the rebuilt guide.

## Problems shared by all three practice pages

| Area | Finding |
|---|---|
| Branding | Practice name in the title and footer, logo in the header, brand purple and teal, and a QR code with "Free 15-minute consultation". The embedded logo is about 86 KB of each 100 KB file. |
| Built for a lobby screen | Idle timers change the page under you: the Prism starts drifting by itself after 120 seconds and What Moves resets to baseline after 180 seconds. In a session, a two-minute explanation is enough to trigger both. There is no pause. |
| Layout | Fixed 1920x1080 stage scaled with CSS zoom (What Moves), absolutely positioned captions (Prism), `overflow: hidden` everywhere. On a laptop or in a shared meeting window, text shrinks or overlaps. |
| Legibility | 12 to 13 px uppercase grey labels on near-black, glow effects, emoji as icons, most text drawn inside canvas (cannot be selected, enlarged or read by a screen reader), colour as the only cue, no keyboard access, no reduced-motion handling. |
| Structure | Three unrelated files with copied code and no navigation between them. |
| Coverage | Nothing on neurofeedback itself: how it works, what a session is, the approaches used, safety, or the evidence. |

## Brainwave Prism

- **Keep:** the prism analogy is accurate and memorable. The footer already says the signal is simplified.
- **Fast rhythms were drawn wrongly.** Beta and gamma were sampled at about three points per wave, which produces a jagged pattern that is a drawing artifact, not what those rhythms look like.
- **"Stressed / wired: high beta and gamma, little alpha"** is not a reliable signature. A review of 184 resting-state studies found the same patterns recurring across different conditions, and many anxious people show no extra beta. Removed.
- **One band, one meaning.** Lines such as "too much while awake feels like fog" and "too much = tension, racing mind" teach that each band has a fixed meaning. Location and context decide that.
- **"That's what a brain map measures"** undersells a brain map, which compares many sites with a reference database.
- **Percentages on the beams** read as measurements. They were arbitrary.
- **Missing for this practice:** the infra-slow range (the basis of ILF work) and SMR.

## What Moves Your Brainwaves

This page carried the most risk, because each tile states a direction of change as fact.

| Tile | Page said | Evidence | Verdict |
|---|---|---|---|
| Caffeine | Less alpha, more beta | Less alpha is solid (48-study review). Beta is inconsistent. | Partly right |
| Alcohol, a drink or two | More alpha and theta | Supported: more theta and slow alpha | Right |
| Alcohol, heavy and long-term | More delta; baseline alpha weakens | Best-replicated long-term finding is extra beta (n=614). Human evidence for the delta claim was thin. | Partly right |
| Cannabis | More alpha and theta | Mixed. A 16-study review found no consistent direction and recent work shows theta going down. | Not supported |
| Nicotine | More beta and gamma, less theta and alpha | Alpha speeds up and fast alpha rises. Theta falls. No gamma evidence. | Wrong on alpha |
| "Stimulants (Adderall, cocaine)" | More fast beta and gamma, less delta and theta; "severe anxiety or paranoia" | Prescribed stimulants: beta may rise and theta may fall, modestly and inconsistently (44-study review). No gamma evidence. | Overstated, and pairs a prescription many clients take with cocaine |
| Mindfulness | More alpha, theta, synchronised gamma | Alpha and theta often rise (56-study review). Gamma is inconsistent. | Partly right |
| Aerobic exercise | More alpha; "that is the runner's high" | Alpha is higher on average, other bands rise too. No support for the runner's-high link. | Partly right |
| Screens and social media | More high beta, "chronic alertness", "dopamine hits" | No established lasting EEG pattern. The solid finding is that evening screens delay sleep. | Not supported |
| Slow breathing | More alpha and theta, less beta | HRV rises reliably. Alpha often rises. The main review found theta going down. | Mixed |
| Deep sleep | Delta, growth hormone, glymphatic "rinse" | Delta and growth hormone are solid. Waste clearance in humans is indirect evidence. | Mostly right |

Other points: "The state neurofeedback helps the brain find on its own" is a marketing line. Benzodiazepines (reliable extra beta) and sleep loss (extra theta) matter most for reading a client's recording and were absent. The wine, champagne and cigarette emoji are the wrong tone for a clinical room.

## Heartbeat Live

- **Keep:** the concept, the live strap connection, the pacer, and the 4.5 to 7 breaths-a-minute range.
- **"A jagged or flat line usually means the body is braced."** This interprets a client's live physiology on thin grounds. A small swing is normal with age (about 10 beats a minute in inactive men in their sixties against about 22 in young men), and a jagged line is often a skipped beat or a strap glitch.
- **No over-breathing caution.** Paced slow breathing can cause light-headedness in beginners who breathe too deeply. In one trial, an instruction to breathe shallowly and naturally roughly halved the drop in CO2.
- **"A few minutes a day ... recover from stress faster and sleep better."** The benefit is real but small to moderate (58 trials), strongest for anxiety and mood and weakest for sleep.
- **Beat timing.** Beats were stamped with their arrival time. Bluetooth delivers them in batches about once a second, so the trace was smeared and points stacked.
- **Straps without beat-to-beat data.** The page invented one beat per notification and still showed an RMSSD figure that meant nothing.
- **Swing figure.** Taken from a single breath, so one stray beat distorted it.
- **No way to compare paces**, although finding a personal pace is the point of the exercise.
- Windows-only wording, and no statement that this is not a medical device.

## The two Learning EEG pages

These are saved copies of chapters from learningeeg.com, a clinician-level EEG atlas. They are someone else's published work, so I did not rework them. The copies were saved without their image folder, so pictures and interactive steps do not load. The material (spikes, seizures, phase reversals, filter settings) is written for people learning to read hospital EEGs and would alarm more clients than it helps. They remain a good personal reference on the live site. The rebuilt guide has an original, client-level "Sensors and signal" section in their place.

## What the rebuild changes

One unbranded file with nine sections and shared navigation: Start here, Brain rhythms (the Prism), Sensors and signal, What shifts them (What Moves), How training works, Kinds of training, Your sessions, What research says, Heart and breath (Heartbeat Live).

- No logo, QR code, practice name or brand colours. Light and dark themes, larger-text mode, full screen, hide-menu for presenting, arrow keys to move between sections.
- No idle timers. Every moving figure has Pause.
- Real text throughout, works from phone width to a projector, keyboard accessible, honours reduced-motion settings.
- Every factual claim carries a source, and uncertain ones are marked as uncertain.

## Points to check before using it with clients

1. **The research section is candid.** ADHD and sleep in particular are less favourable than most neurofeedback material suggests. Read it first and decide how you want to talk it through.
2. **0.01 Hz synchrony.** Your books confirm 10 Hz and 40 Hz synchrony. I could not find 0.01 Hz synchrony in the chapters I could reach, so that figure rests on what you told me.
3. **Session wording.** "Sensors go on with a little paste", "I stay with you", the review step and the preparation advice for a brain map are reasonable defaults written in your voice. Adjust anything that is not how you work.
4. **Starting sensor sites.** The map lets you show any pair but names no standard starting sites, because I could not confirm them from the books.
5. **Chest strap.** The live strap connection could not be tested here (no Bluetooth). The demonstration signal and all the calculations were tested.
