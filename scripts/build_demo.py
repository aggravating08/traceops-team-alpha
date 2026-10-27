#!/usr/bin/env python3
"""Build the public browser sample from the application UI and fictional fixtures."""
import csv
import json
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parents[1]
TARGET=ROOT/'docs'/'demo'
TARGET.mkdir(parents=True,exist_ok=True)
html=(ROOT/'web/index.html').read_text().replace('<html lang="en">','<html lang="en" data-runtime="browser">').replace('href="/style.css"','href="./style.css"').replace('src="/app.js"','src="./app.js"').replace('href="/" class="brand"','href="./" class="brand"')
(TARGET/'index.html').write_text(html)
for name in ('style.css','app.js','sample-engine.js'):
    shutil.copyfile(ROOT/'web'/name,TARGET/name)
sources={}
for table in ('orders','inventory','tickets'):
    with (ROOT/'data'/f'{table}.csv').open(newline='') as f:
        sources[table]=list(csv.DictReader(f))
(TARGET/'sample-data.json').write_text(json.dumps(sources,indent=2))
(ROOT/'docs'/'index.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta http-equiv="refresh" content="0; url=./demo/"><title>TraceOps</title><a href="./demo/">Open TraceOps browser sample</a></html>')
(ROOT/'docs'/'.nojekyll').touch()
print(TARGET)

video=ROOT/'output'/'TraceOps-Walkthrough.mp4'
if video.exists():
    shutil.copyfile(video,TARGET/'walkthrough.mp4')
