from __future__ import annotations
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from .config import SuiteConfig
from .prompts import load_prompts, pick_prompts, write_prompt_manifest
from .utils import ensure_dir, write_text


def make_app(cfg: SuiteConfig) -> FastAPI:
    app = FastAPI(title="Piper Voice Studio")

    ensure_dir(cfg.paths.recordings_dir)
    takes_dir = cfg.paths.recordings_dir / "takes"
    ensure_dir(takes_dir)

    all_prompts = load_prompts(cfg.prompts.file)
    picked = pick_prompts(all_prompts, cfg.prompts.count, cfg.prompts.randomize)
    manifest = write_prompt_manifest(cfg.paths.recordings_dir, picked)

    # Save a small session file for reproducibility
    session_file = cfg.paths.recordings_dir / "session.txt"
    write_text(session_file, f"voice_id={cfg.voice_id}\nmanifest={manifest}\ncount={len(picked)}\n")

    html = _render_html(cfg.voice_id)

    @app.get("/", response_class=HTMLResponse)
    def index():
        return html

    @app.get("/api/prompts")
    def get_prompts():
        return {"voice_id": cfg.voice_id, "prompts": [{"idx": p.idx, "text": p.text} for p in picked]}

    @app.post("/api/upload")
    async def upload_take(
        idx: int = Form(...),
        text: str = Form(...),
        file: UploadFile = Form(...),
    ):
        # Store as <idx>.wav and <idx>.txt
        wav_path = takes_dir / f"{idx}.wav"
        txt_path = takes_dir / f"{idx}.txt"

        content = await file.read()
        wav_path.write_bytes(content)
        write_text(txt_path, text.strip() + "\n")

        return {"ok": True, "saved": str(wav_path.name)}

    @app.post("/api/finalize")
    def finalize():
        # Just a marker file; dataset build step uses takes/ folder.
        marker = cfg.paths.recordings_dir / "FINALIZED"
        write_text(marker, "ok\n")
        return {"ok": True, "message": "Finalized. You can now run: pvs dataset build ..."}

    return app


def run_studio(cfg: SuiteConfig, host: str = "127.0.0.1", port: int = 7860) -> None:
    app = make_app(cfg)
    print(f"🎙️ Piper Voice Studio: http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")


def _render_html(voice_id: str) -> str:
    # Minimal inline UI (no external deps)
    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>Piper Voice Studio — {voice_id}</title>
  <style>
    body {{ font-family: system-ui, Arial; margin: 20px; max-width: 1000px; }}
    .row {{ display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }}
    .card {{ border: 1px solid #ddd; border-radius: 12px; padding: 12px; margin: 12px 0; }}
    button {{ padding: 10px 14px; border-radius: 10px; border: 1px solid #333; background: #fff; cursor: pointer; }}
    button:disabled {{ opacity: 0.5; cursor: not-allowed; }}
    .mono {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }}
    .ok {{ color: #0a7; }}
    .bad {{ color: #c30; }}
    audio {{ width: 100%; }}
  </style>
</head>
<body>
  <h1>Piper Voice Studio</h1>
  <p>Voice: <span class="mono">{voice_id}</span></p>
  <div class="card">
    <div class="row">
      <button id="btnInit">Enable Mic</button>
      <button id="btnRec" disabled>Record</button>
      <button id="btnStop" disabled>Stop</button>
      <button id="btnUpload" disabled>Upload Take</button>
      <button id="btnFinalize">Finalize Session</button>
    </div>
    <p id="status" class="mono">status: idle</p>
    <audio id="player" controls></audio>
  </div>

  <div class="card">
    <h2>Prompt</h2>
    <p><b>Index:</b> <span id="pIdx" class="mono">-</span></p>
    <p id="pText" style="font-size: 1.15rem;"></p>
    <div class="row">
      <button id="btnPrev">Prev</button>
      <button id="btnNext">Next</button>
      <span id="progress" class="mono"></span>
    </div>
  </div>

  <script>
    let prompts = [];
    let cur = 0;

    let stream = null;
    let mediaRecorder = null;
    let chunks = [];
    let blob = null;

    const statusEl = document.getElementById('status');
    const player = document.getElementById('player');
    const pIdx = document.getElementById('pIdx');
    const pText = document.getElementById('pText');
    const progress = document.getElementById('progress');

    const btnInit = document.getElementById('btnInit');
    const btnRec = document.getElementById('btnRec');
    const btnStop = document.getElementById('btnStop');
    const btnUpload = document.getElementById('btnUpload');
    const btnFinalize = document.getElementById('btnFinalize');
    const btnPrev = document.getElementById('btnPrev');
    const btnNext = document.getElementById('btnNext');

    function setStatus(s) {{
      statusEl.textContent = 'status: ' + s;
    }}

    function showPrompt() {{
      if (!prompts.length) return;
      const p = prompts[cur];
      pIdx.textContent = p.idx;
      pText.textContent = p.text;
      progress.textContent = `prompt ${cur+1} / ${prompts.length}`;
      blob = null;
      player.src = '';
      btnUpload.disabled = true;
    }}

    async function loadPrompts() {{
      const r = await fetch('/api/prompts');
      const j = await r.json();
      prompts = j.prompts || [];
      cur = 0;
      showPrompt();
    }}

    btnPrev.onclick = () => {{
      if (cur > 0) cur--;
      showPrompt();
    }};
    btnNext.onclick = () => {{
      if (cur < prompts.length - 1) cur++;
      showPrompt();
    }};

    btnInit.onclick = async () => {{
      stream = await navigator.mediaDevices.getUserMedia({{ audio: true }});
      btnRec.disabled = false;
      setStatus('mic ready');
    }};

    btnRec.onclick = () => {{
      chunks = [];
      blob = null;
      mediaRecorder = new MediaRecorder(stream);
      mediaRecorder.ondataavailable = e => chunks.push(e.data);
      mediaRecorder.onstop = () => {{
        blob = new Blob(chunks, {{ type: 'audio/wav' }});
        player.src = URL.createObjectURL(blob);
        btnUpload.disabled = false;
        setStatus('recorded');
      }};
      mediaRecorder.start();
      btnRec.disabled = true;
      btnStop.disabled = false;
      setStatus('recording...');
    }};

    btnStop.onclick = () => {{
      mediaRecorder.stop();
      btnStop.disabled = true;
      btnRec.disabled = false;
    }};

    btnUpload.onclick = async () => {{
      if (!blob) return;
      const p = prompts[cur];
      const fd = new FormData();
      fd.append('idx', p.idx);
      fd.append('text', p.text);
      fd.append('file', blob, `${p.idx}.wav`);
      setStatus('uploading...');
      const r = await fetch('/api/upload', {{ method: 'POST', body: fd }});
      const j = await r.json();
      if (j.ok) {{
        setStatus('uploaded ✅ ' + j.saved);
      }} else {{
        setStatus('upload failed ❌');
      }}
    }};

    btnFinalize.onclick = async () => {{
      const r = await fetch('/api/finalize', {{ method: 'POST' }});
      const j = await r.json();
      setStatus(j.message || 'finalized');
    }};

    loadPrompts();
  </script>
</body>
</html>
"""