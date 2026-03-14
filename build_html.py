#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_html.py
Reads all chapter .md files from d:/Claude/小說_替身/
and generates a single self-contained HTML reader.
"""

import glob
import os
import re
import json
import html

# ── 1. Collect & sort chapter files ─────────────────────────────────────────

BASE_DIR = "d:/Claude/小說_替身"
pattern = os.path.join(BASE_DIR, "第*章_*.md")
files = glob.glob(pattern)

def extract_chapter_num(path):
    """Extract numeric chapter number from filename like 第01章_... or 第100章_..."""
    basename = os.path.basename(path)
    m = re.match(r"第(\d+)章", basename)
    return int(m.group(1)) if m else 9999

files.sort(key=extract_chapter_num)
print(f"Found {len(files)} chapter files.")

# ── 2. Parse each file ───────────────────────────────────────────────────────

def md_to_html_body(raw_text):
    """
    Convert markdown body text to HTML paragraphs.
    - Remove leading # / ## / ### from lines
    - Split on blank lines to get paragraphs
    - Wrap each paragraph in <p> tags
    - Escape HTML special characters
    """
    # Remove the first ## title line (we already use it as chapter title)
    lines = raw_text.split('\n')

    # Strip heading markers from ALL lines (# ## ### etc.)
    stripped_lines = []
    for line in lines:
        cleaned = re.sub(r'^#{1,6}\s*', '', line)
        stripped_lines.append(cleaned)

    text = '\n'.join(stripped_lines)

    # Split on double newlines (paragraph breaks)
    paragraphs = re.split(r'\n{2,}', text)

    html_parts = []
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        # Escape HTML characters
        para_escaped = html.escape(para)
        # Convert single newlines inside a paragraph to <br>
        para_escaped = para_escaped.replace('\n', '<br>')
        html_parts.append(f'<p>{para_escaped}</p>')

    return '\n'.join(html_parts)


chapters = []

for fpath in files:
    with open(fpath, 'r', encoding='utf-8') as f:
        raw = f.read()

    lines = raw.split('\n')

    # Find title: first line starting with ##
    title = ''
    title_line_idx = -1
    for i, line in enumerate(lines):
        if line.startswith('##'):
            title = re.sub(r'^#{1,6}\s*', '', line).strip()
            title_line_idx = i
            break

    if not title:
        # Fallback: use filename
        basename = os.path.basename(fpath)
        title = basename.replace('.md', '')

    # Body: everything after the title line
    if title_line_idx >= 0:
        body_lines = lines[title_line_idx + 1:]
    else:
        body_lines = lines

    body_raw = '\n'.join(body_lines)
    body_html = md_to_html_body(body_raw)

    chapters.append({
        'title': title,
        'content': body_html,
    })

print(f"Parsed {len(chapters)} chapters.")

# ── 3. Build the HTML ────────────────────────────────────────────────────────

# Serialize chapters to a JS-safe JSON string
chapters_json = json.dumps(chapters, ensure_ascii=False)

html_template = f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>《替身無極》閱讀器</title>
  <style>
    *, *::before, *::after {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}

    body {{
      background: #FFF8E7;
      color: #3D2B1F;
      font-family: 'Microsoft JhengHei', '微軟正黑體', 'PingFang TC', sans-serif;
      font-size: 20px;
      line-height: 1.9;
      min-height: 100vh;
    }}

    /* ── Top bar ── */
    #topbar {{
      position: sticky;
      top: 0;
      z-index: 100;
      background: #FEF0C7;
      border-bottom: 2px solid #C8860A;
      padding: 10px 16px;
      display: flex;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
      box-shadow: 0 2px 8px rgba(139,69,19,0.10);
    }}

    #book-title {{
      font-size: 22px;
      font-weight: bold;
      color: #8B4513;
      letter-spacing: 2px;
      flex-shrink: 0;
      margin-right: 8px;
    }}

    #chapter-select {{
      flex: 1 1 180px;
      min-width: 140px;
      max-width: 340px;
      padding: 6px 10px;
      font-size: 15px;
      font-family: inherit;
      background: #FFF8E7;
      color: #3D2B1F;
      border: 1.5px solid #C8860A;
      border-radius: 8px;
      cursor: pointer;
      outline: none;
    }}
    #chapter-select:focus {{
      border-color: #8B4513;
    }}

    #counter {{
      font-size: 15px;
      color: #8B4513;
      flex-shrink: 0;
      min-width: 110px;
      text-align: right;
    }}

    .nav-btn {{
      padding: 6px 18px;
      font-size: 15px;
      font-family: inherit;
      background: #C8860A;
      color: #FFF8E7;
      border: none;
      border-radius: 8px;
      cursor: pointer;
      font-weight: bold;
      transition: background 0.18s;
      flex-shrink: 0;
    }}
    .nav-btn:hover {{
      background: #A0680A;
    }}
    .nav-btn:disabled {{
      background: #D4B896;
      cursor: default;
    }}

    /* ── Content area ── */
    #content-wrap {{
      max-width: 800px;
      margin: 0 auto;
      padding: 36px 24px 80px;
    }}

    .chapter-section {{
      display: none;
    }}
    .chapter-section.active {{
      display: block;
    }}

    .chapter-title {{
      font-size: 26px;
      font-weight: bold;
      color: #8B4513;
      line-height: 1.5;
      margin-bottom: 28px;
      padding-bottom: 12px;
      border-bottom: 2px solid #E8D5A3;
      letter-spacing: 1px;
    }}

    .chapter-body p {{
      margin-bottom: 1.2em;
      text-indent: 2em;
    }}

    /* ── Bottom navigation ── */
    #bottomnav {{
      max-width: 800px;
      margin: 0 auto;
      padding: 20px 24px 48px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
    }}

    #bottom-counter {{
      font-size: 15px;
      color: #8B4513;
      text-align: center;
      flex: 1;
    }}

    /* ── Scroll-to-top button ── */
    #scroll-top {{
      position: fixed;
      bottom: 28px;
      right: 24px;
      width: 44px;
      height: 44px;
      background: #C8860A;
      color: #FFF8E7;
      border: none;
      border-radius: 50%;
      font-size: 22px;
      cursor: pointer;
      display: none;
      align-items: center;
      justify-content: center;
      box-shadow: 0 2px 8px rgba(139,69,19,0.25);
      z-index: 200;
      transition: background 0.18s;
    }}
    #scroll-top:hover {{
      background: #A0680A;
    }}
    #scroll-top.visible {{
      display: flex;
    }}

    /* ── Responsive ── */
    @media (max-width: 600px) {{
      body {{ font-size: 18px; }}
      .chapter-title {{ font-size: 22px; }}
      #book-title {{ font-size: 18px; }}
      #content-wrap {{ padding: 24px 14px 60px; }}
      .nav-btn {{ padding: 6px 12px; font-size: 14px; }}
      #counter {{ font-size: 13px; }}
    }}
  </style>
</head>
<body>

<!-- Top navigation bar -->
<div id="topbar">
  <span id="book-title">《替身無極》</span>
  <button class="nav-btn" id="btn-prev-top" onclick="changeChapter(currentIdx - 1)">&#8592; 上一章</button>
  <select id="chapter-select" onchange="changeChapter(this.value)"></select>
  <button class="nav-btn" id="btn-next-top" onclick="changeChapter(currentIdx + 1)">下一章 &#8594;</button>
  <span id="counter"></span>
</div>

<!-- Chapter content -->
<div id="content-wrap">
</div>

<!-- Bottom navigation -->
<div id="bottomnav">
  <button class="nav-btn" id="btn-prev-bot" onclick="changeChapter(currentIdx - 1)">&#8592; 上一章</button>
  <span id="bottom-counter"></span>
  <button class="nav-btn" id="btn-next-bot" onclick="changeChapter(currentIdx + 1)">下一章 &#8594;</button>
</div>

<!-- Scroll to top -->
<button id="scroll-top" onclick="window.scrollTo({{top:0,behavior:'smooth'}})" title="回到頂部">&#8679;</button>

<script>
// ── Chapter data ──────────────────────────────────────────────────────────
const CHAPTERS = {chapters_json};
const TOTAL = CHAPTERS.length;
let currentIdx = 0;

// ── Build DOM ─────────────────────────────────────────────────────────────
(function buildDOM() {{
  const wrap = document.getElementById('content-wrap');
  const sel = document.getElementById('chapter-select');

  CHAPTERS.forEach(function(ch, i) {{
    // Section
    const sec = document.createElement('section');
    sec.className = 'chapter-section';
    sec.id = 'ch-' + i;
    sec.innerHTML =
      '<h2 class="chapter-title">' + escHtml(ch.title) + '</h2>' +
      '<div class="chapter-body">' + ch.content + '</div>';
    wrap.appendChild(sec);

    // Dropdown option
    const opt = document.createElement('option');
    opt.value = i;
    opt.textContent = (i + 1) + '. ' + ch.title;
    sel.appendChild(opt);
  }});
}})();

function escHtml(s) {{
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}}

// ── Navigate ──────────────────────────────────────────────────────────────
function changeChapter(idx) {{
  idx = parseInt(idx, 10);
  if (idx < 0 || idx >= TOTAL) return;

  // Hide old
  const old = document.getElementById('ch-' + currentIdx);
  if (old) old.classList.remove('active');

  currentIdx = idx;

  // Show new
  const sec = document.getElementById('ch-' + currentIdx);
  if (sec) sec.classList.add('active');

  // Sync dropdown
  document.getElementById('chapter-select').value = currentIdx;

  // Update counters
  const label = '第 ' + (currentIdx + 1) + ' 章 / ' + TOTAL;
  document.getElementById('counter').textContent = label;
  document.getElementById('bottom-counter').textContent = label;

  // Update buttons
  document.getElementById('btn-prev-top').disabled = (currentIdx === 0);
  document.getElementById('btn-prev-bot').disabled = (currentIdx === 0);
  document.getElementById('btn-next-top').disabled = (currentIdx === TOTAL - 1);
  document.getElementById('btn-next-bot').disabled = (currentIdx === TOTAL - 1);

  // Scroll to top smoothly
  window.scrollTo({{ top: 0, behavior: 'smooth' }});
}}

// ── Init ──────────────────────────────────────────────────────────────────
changeChapter(0);

// ── Scroll-to-top button visibility ──────────────────────────────────────
window.addEventListener('scroll', function() {{
  const btn = document.getElementById('scroll-top');
  if (window.scrollY > 300) {{
    btn.classList.add('visible');
  }} else {{
    btn.classList.remove('visible');
  }}
}});
</script>
</body>
</html>
"""

# ── 4. Write output ──────────────────────────────────────────────────────────

output_path = os.path.join(BASE_DIR, "替身無極_閱讀器.html")
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(html_template)

size_kb = os.path.getsize(output_path) // 1024
print(f"HTML written to: {output_path}")
print(f"File size: {size_kb} KB")
print("Done!")
