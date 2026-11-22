# Prompt Debugging — 45-minute classroom activity

This is the activity described in Section 3 of the paper. Students write a
natural-language instruction, predict what the robot will do, then use the
PetoiX trace to find out why the robot did (or did not) match their
prediction.

**Grade level:** middle school · **Group size:** 2–3 students per robot ·
**Materials:** one Petoi Bittle X, one laptop running PetoiX, worksheet below

## Before class (teacher)

1. Start the server (`python server.py`) and open `http://localhost:8080`.
2. Check the robot responds to **Manual Mode → Stand**.
3. Run the four **Demo Prompts** once so you have seen each outcome.

## 1. Predict (10 min)

Students write one instruction in everyday language, for example
*"Act like a sleepy puppy and take a rest"*, and predict which skills the
robot will run, in order. The robot knows 19 skills (stand, sit, rest,
stretch, wave, walk forward/backward/left/right, crawl, trot, push-up,
play dead, rotate, celebrate, check around, the 6-7 routine, stop, and
joint status) and runs at most **3** per prompt.

## 2. Inspect (15 min)

Submit the prompt by voice or text, then read the **Interpreted Plan and
Result** card and the **Learning Trace**:

| Trace field | Question for students |
|---|---|
| Transcribed text | Did speech recognition hear what you said? |
| Decided by | Was the plan chosen by the **AI model** (GPT-4o Mini) or by **keyword rules**? |
| Plan (steps) | Which of the 19 skills were chosen, and in what order? |
| Commands | Which firmware commands were sent (e.g. `ksit`, `khi`)? |
| Result | Did every command run, or was any blocked by the safety allowlist? |

## 3. Debug & reflect (20 min)

If the robot did something different from the prediction, decide where it
went wrong:

- **Speech recognition** — the transcribed text is different from what was said.
- **Phrasing ambiguity** — the words could mean more than one skill.
- **Skill mapping limits** — the action is not one of the 19 skills (e.g. "do a backflip").

Rewrite the prompt to fix it, run it again, and record both versions.

## Worksheet

| # | My prompt | My predicted skills | Actual plan | Decided by | Matched? | Where it went wrong | Revised prompt |
|---|---|---|---|---|---|---|---|
| 1 | | | | AI model / rules | Y / N | | |
| 2 | | | | AI model / rules | Y / N | | |
| 3 | | | | AI model / rules | Y / N | | |

## Data collected

Each command is appended to `interaction_logs.jsonl` (prompt, sentiment,
plan, planner source, commands, robot replies, latency). The file is ignored
by git. Remove or anonymize it before sharing, because it contains student
prompts.
