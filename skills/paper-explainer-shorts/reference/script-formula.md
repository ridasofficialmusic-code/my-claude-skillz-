# Retention script formula (45–55 s, loops)

Goal: **≥ 80% "viewed" (not swiped away)** and **> 100% average percentage viewed** (the loop). The swipe decision happens in roughly the first second, mostly on what the viewer *sees*, so the hook is designed visual-first.

Budget: **120–145 words**, 13–15 short lines. One idea per line. Spoken English, contractions, short words.

| Scene | Time | Job | Pattern |
|---|---|---|---|
| 0 hook | 0–6 s | Win the swipe, open a loop | **Frame 1 visual hook** + a **≤ 2.5 s spoken claim** + a context line (see below) |
| 1 reason #1 | 6–18 s | First payoff | "Reason number one: *[3–5 word headline]*." → mechanism in plain words (one term at most) → consequence |
| 2 turn | ~18–20 s | Pattern interrupt, re-hook | "But here's why it won't stop." / "But that's not what keeps it alive." |
| 3 reason #2 | 20–30 s | Second payoff | "Reason number two: *[headline]*." → what you do that makes it worse → the brain's "logic" |
| 4 fix | 30–44 s | Value + surprise | "So here's the fix." → named effect or study → one concrete, honest number → punchline |
| 5 CTA + loop | 44–51 s | Comments, then loop | A question about the viewer's own life + "Comment below." → **loop line** that runs into the first spoken line |

## The hook (the most important 2 seconds)

### Visual hook: frame 1 must have all four
1. **Text hook:** the topic as a question or bold claim in **≤ 4 words per line, 2 lines max**, huge, at the top (y 300–480). It must be readable on its own with the sound off: "SONG STUCK / IN YOUR HEAD?", "STILL CRINGING / AT 2AM?".
2. **A character mid-reaction** (`mood: shock` or `cringe`), not a neutral prop.
3. **Motion that starts on frame 1:** something odd already moving (`"from": [x, y]`, `"move_dur"`), e.g. an earworm crawling into an ear, a brain escaping a head, a clock spinning. Entrance pops don't count, because on frame 1 the element doesn't exist yet.
4. **The first caption word** is already on screen (automatic when the voice starts at ~0.05 s).

The engine adds a **punch-in zoom + shake** on frame 1 (`"hook": {"punch": 1.15}`) and a **boom + paper-rip** sound hit. Keep all hook art inside the central 87% of the frame, because the punch crops the edges for the first half-second.

### Spoken hook: the first line
- **≤ 2.5 s (about 10 words), no throat-clearing.** The voice starts at 0.05 s (`lead_in`) and runs a little faster (`"hook": {"speed": 1.12}`).
- The on-screen text gives the context, so the voice can go straight to the intrigue. Don't read the text hook out loud.
- Pick one archetype:

| Archetype | Example |
|---|---|
| **Contrarian claim** | "It's not random. Your brain is doing it on purpose." |
| **Direct callout** | "If you replay embarrassing moments at night, this is for you." |
| **Weird fact** | "Nine in ten people have this happen every single week." |
| **Hidden reason** | "There's a reason you forget why you walked into a room, and it's the door." |
| **Wrong-belief** | "You're not bad at sleeping. Your brain is doing this on purpose." |

- **Banned openers:** "Did you know", "Have you ever wondered", "Today", "In this video", long scene-setting ("You heard ten seconds of a song this morning…" took 5.6 s before the question: too slow).

### Hook scorecard (check before building; all must be yes)
- [ ] Frame 1 alone (no sound) tells you the topic and makes you curious.
- [ ] Something is moving on frame 1.
- [ ] The first spoken sentence ends by 2.5 s.
- [ ] The first sentence makes a claim or callout, not a setup.
- [ ] The viewer is in the sentence ("you", "your brain").
- [ ] The text hook and the spoken hook say different things.
- [ ] Frame 1 matches the thumbnail.

## Loop ending
End on a line that runs straight back into the first spoken line, and cut the video **0.3 s after the last word** (`duration` = last word end + 0.3). Don't add a "follow" voice line: show the pulsing FOLLOW button silently during the loop line.
- *"So next time a song gets stuck in your head, remember:"* → loops into *"It's not random. Your brain is doing it on purpose."*
- *"And the next time it's 2AM and your brain hits play,"* → *"it thinks it's helping you."*

## Retention devices to keep
- Numbered structure ("Reason number one/two") works as an implied progress bar.
- The turn line with the red background and shaking `BUT...`, plus an automatic punch-in on every scene change.
- A visual change every 2–4 s, anchored to keywords. Run `preview.py` and fix any frame that's empty.
- One surprising, honest number in the fix scene.
- A CTA question that asks for a personal story.

## Accuracy rules
- Only use explanations with real research behind them. Prefer textbook-level findings and well-known studies.
- Round honestly ("about a quarter"), and hedge where the science is debated.
- No medical advice. For mental-health-adjacent topics, keep it about normal everyday experience.
- Record 2–4 sources for the upload kit.

## Reference specs
- `examples/cringe-memories.json`: the original format (slow hook; kept for comparison).
- The v2 earworm spec in `AI CONTENT/testers/03-why-songs-get-stuck/v2-hook/script.json`: the current hook + loop format.
