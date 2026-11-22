"""Figure 2 (Prompt-to-Action Pipeline) for the SIGCSE 2027 PetoiX poster.

Labels match github.com/Birkenstack/robotic-dog-hsi (commit 3a01557):
  Box 2  call_llm(): keyword rules first, GPT-4o Mini otherwise, rule fallback
  Box 3  MAX_PLAN_STEPS = 3; SKILL_LIBRARY has 19 skills
  Box 4  validate_command(): allowlist + JOINT_LIMITS
  Trace  app.js "Decided by: AI model / keyword rules"
  Log    append_interaction_log(): JSONL with sentiment, latency_ms, outcome
Example "sit then wave" -> [sit, wave] -> ksit, khi is the logged run in demo_results.jsonl.

Icons: Lucide (lucide.dev), ISC license, in ./icons.
Renders with the installed Microsoft Edge through Playwright:
    python build_fig2.py
-> planning-pipeline-generated.png (2100x1011, same aspect as the original) and .pdf (vector)
"""
import os
import re
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1050, 505.5  # CSS px; x2 device scale = 2100 x 1011


def icon(name, cls="ic"):
    svg = open(os.path.join(HERE, "icons", f"{name}.svg"), encoding="utf-8").read()
    svg = re.sub(r"<!--.*?-->", "", svg, flags=re.S).strip()
    svg = re.sub(r'class="[^"]*"', f'class="{cls}"', svg, count=1)
    svg = re.sub(r'\s(width|height)="24"', "", svg)
    return svg


STAGES = [
    ("mic", "Student<br>Prompt", "speech → text<br>Web Speech API", "“sit then<br>wave”"),
    ("brain-circuit", "Interpret<br>Request", "GPT-4o Mini +<br>rule fallback", "steps:<br>[sit, wave]"),
    ("list-ordered", "Map to<br>Safe Skills", "1–3 skills from<br>19-skill library", "sit → ksit<br>wave → khi"),
    ("shield-check", "Validate<br>Commands", "allowlist +<br>joint limits", "ksit ✓&nbsp; khi ✓"),
    ("dog", "Robot<br>Execution", "serial commands<br>over Bluetooth", "sits, then<br>waves"),
]

cards = []
for i, (ic, title, sub, ex) in enumerate(STAGES):
    cards.append(f"""
    <div class="card">
      <div class="num">{i + 1}</div>
      <div class="tile">{icon(ic)}</div>
      <div class="title">{title}</div>
      <div class="rule"></div>
      <div class="sub">{sub}</div>
      <div class="ex">{ex}</div>
    </div>""")
    if i < len(STAGES) - 1:
        cards.append(f'<div class="link">{icon("arrow-right", "arr")}</div>')

HTML = f"""<!doctype html>
<html><head><meta charset="utf-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&family=JetBrains+Mono:wght@500&display=block" rel="stylesheet">
<style>
  :root {{
    --navy: #1d3b6f;
    --ink: #111827;
    --muted: #374151;
    --tint: #eaf0f9;
    --line: #1d3b6f;
  }}
  @page {{ size: {W}px {H}px; margin: 0; }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html, body {{ width: {W}px; height: {H}px; background: #fff; }}
  body {{ font-family: Inter, Arial, sans-serif; color: var(--ink);
         -webkit-font-smoothing: antialiased; }}
  #fig {{ width: {W}px; height: {H}px; padding: 10px 12px 10px;
         display: flex; flex-direction: column; gap: 12px; }}

  .row {{ display: flex; align-items: stretch; height: 318px; }}
  .card {{ position: relative; flex: 1 1 0; border: 2.5px solid var(--line);
          border-radius: 16px; background: #fff;
          display: flex; flex-direction: column; align-items: center;
          padding: 14px 6px 8px; text-align: center; }}
  .num {{ position: absolute; top: 9px; left: 9px; width: 26px; height: 26px;
         border-radius: 50%; background: var(--navy); color: #fff;
         font: 700 16px/26px Inter, Arial, sans-serif; }}
  .tile {{ width: 58px; height: 58px; border-radius: 14px; background: var(--tint);
          display: grid; place-items: center; }}
  .ic {{ width: 36px; height: 36px; color: var(--navy); stroke-width: 1.9; }}
  .title {{ margin-top: 10px; font-weight: 700; font-size: 25px; line-height: 1.08;
           letter-spacing: -0.2px; }}
  .rule {{ width: 82%; height: 2px; background: var(--line); margin: 11px 0 10px;
          opacity: .85; }}
  .sub {{ font-size: 19.5px; line-height: 1.22; color: var(--muted); white-space: nowrap;
          letter-spacing: -0.15px; }}
  .ex {{ margin-top: auto; width: 100%; min-height: 64px; border-radius: 10px;
        background: var(--tint); display: grid; place-items: center;
        font: 500 18.5px/1.2 "JetBrains Mono", Consolas, monospace; color: var(--navy);
        white-space: nowrap;
        padding: 6px 4px; }}
  .link {{ flex: 0 0 26px; display: grid; place-items: center; }}
  .arr {{ width: 28px; height: 28px; color: var(--navy); stroke-width: 3; }}

  .trace {{ height: 92px; margin: 0 30px; border: 2.5px solid var(--line);
           border-radius: 14px; background: var(--tint);
           display: flex; align-items: center; gap: 18px; padding: 0 24px; }}
  .trace .eye {{ width: 46px; height: 46px; color: var(--navy); stroke-width: 1.9;
                flex: 0 0 auto; }}
  .trace .body {{ flex: 1; text-align: center; }}
  .trace .lbl {{ font-weight: 700; font-size: 25px; color: var(--navy); }}
  .chain {{ margin-top: 7px; display: flex; justify-content: center; align-items: center;
           gap: 9px; font-size: 19px; color: var(--ink); white-space: nowrap; }}
  .pill {{ background: #fff; border: 1.5px solid #9fb3d4; border-radius: 999px;
          padding: 2px 12px; }}
  .chain .to {{ color: var(--navy); font-weight: 700; }}

  .log {{ align-self: center; height: 50px; border: 2px dashed var(--line);
         border-radius: 12px; display: flex; align-items: center; gap: 12px;
         padding: 0 22px; font-size: 20px; color: var(--muted); }}
  .log .doc {{ width: 28px; height: 28px; color: var(--navy); stroke-width: 1.9; }}
</style></head>
<body><div id="fig">
  <div class="row">{''.join(cards)}</div>
  <div class="trace">
    {icon("eye", "eye")}
    <div class="body">
      <div class="lbl">Student-visible trace</div>
      <div class="chain">
        <span class="pill">prompt</span><span class="to">→</span>
        <span class="pill">plan</span><span class="to">→</span>
        <span class="pill">decided by: AI model / keyword rules</span><span class="to">→</span>
        <span class="pill">execution result</span>
      </div>
    </div>
    <div style="width:46px;flex:0 0 auto"></div>
  </div>
  <div class="log">{icon("file-text", "doc")}<span>JSONL interaction log: sentiment · latency · outcome</span></div>
</div></body></html>
"""

html_path = os.path.join(HERE, "fig2.html")
with open(html_path, "w", encoding="utf-8") as f:
    f.write(HTML)

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge")
    page = browser.new_page(viewport={"width": W, "height": int(H + 1)}, device_scale_factor=2)
    page.goto("file:///" + html_path.replace("\\", "/"))
    page.wait_for_load_state("networkidle")
    page.evaluate("document.fonts.ready")
    fonts = page.evaluate("[...document.fonts].filter(f => f.status === 'loaded').map(f => f.family)")
    print("fonts loaded:", sorted(set(fonts)))
    page.screenshot(path=os.path.join(HERE, "planning-pipeline-generated.png"),
                    clip={"x": 0, "y": 0, "width": W, "height": H})
    page.pdf(path=os.path.join(HERE, "planning-pipeline-generated.pdf"),
             width=f"{W}px", height=f"{H}px", print_background=True,
             margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
    browser.close()
print("saved to", HERE)
