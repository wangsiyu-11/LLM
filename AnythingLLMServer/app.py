"""AnythingLLMServer - 文件上传到第一个工作区并自动向量化嵌入。"""
import os
import httpx
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

ANYTHINGLLM_BASE = os.getenv("ANYTHINGLLM_BASE", "http://localhost:3001")
ANYTHINGLLM_KEY = os.getenv("ANYTHINGLLM_API_KEY", "264MW94-ACH4200-KN7XGKE-KB3NX4J")

PAGE = """
<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>文档上传 · AnythingLLM</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: -apple-system, "Segoe UI", "Microsoft YaHei", sans-serif;
    min-height: 100vh;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    display: flex; align-items: center; justify-content: center;
  }
  .card {
    background: #fff; border-radius: 16px; padding: 48px 40px;
    box-shadow: 0 20px 60px rgba(0,0,0,.2);
    width: 440px; max-width: 90vw;
  }
  h1 { font-size: 22px; color: #333; margin-bottom: 6px; }
  p.sub { color: #888; font-size: 14px; margin-bottom: 28px; }
  .drop {
    border: 2px dashed #c5cae9; border-radius: 12px;
    padding: 36px 20px; text-align: center; cursor: pointer;
    transition: all .2s; color: #666;
  }
  .drop:hover, .drop.drag { border-color: #667eea; background: #f5f6ff; }
  .drop .icon { font-size: 36px; margin-bottom: 8px; }
  .drop p { font-size: 14px; }
  #file-name { margin-top: 10px; font-size: 13px; color: #667eea; font-weight: 600; display: none; }
  button {
    width: 100%; margin-top: 24px; padding: 13px;
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: #fff; border: none; border-radius: 10px;
    font-size: 15px; font-weight: 600; cursor: pointer;
    transition: opacity .2s;
  }
  button:disabled { opacity: .5; cursor: not-allowed; }
  #result { margin-top: 20px; padding: 14px; border-radius: 8px;
    font-size: 14px; display: none; }
  #result.ok { background: #e8f5e9; color: #2e7d32; display: block; }
  #result.err { background: #ffebee; color: #c62828; display: block; }
</style>
</head>
<body>
  <div class="card">
    <h1>文档上传到 AnythingLLM</h1>
    <p class="sub">上传后自动加入第一个工作区并完成向量化嵌入</p>
    <div class="drop" id="drop">
      <div class="icon">📄</div>
      <p>点击选择文件，或拖拽文件到这里</p>
      <p id="file-name"></p>
    </div>
    <input type="file" id="file" hidden>
    <button id="btn" disabled>开始上传</button>
    <div id="result"></div>
  </div>
<script>
  const drop = document.getElementById('drop');
  const fileInput = document.getElementById('file');
  const fileName = document.getElementById('file-name');
  const btn = document.getElementById('btn');
  const result = document.getElementById('result');
  let selectedFile = null;

  drop.onclick = () => fileInput.click();
  fileInput.onchange = () => pick(fileInput.files[0]);
  drop.ondragover = e => { e.preventDefault(); drop.classList.add('drag'); };
  drop.ondragleave = () => drop.classList.remove('drag');
  drop.ondrop = e => { e.preventDefault(); drop.classList.remove('drag'); pick(e.dataTransfer.files[0]); };

  function pick(f) {
    if (!f) return;
    selectedFile = f;
    fileName.textContent = '已选择：' + f.name;
    fileName.style.display = 'block';
    btn.disabled = false;
  }

  btn.onclick = async () => {
    if (!selectedFile) return;
    btn.disabled = true; btn.textContent = '上传中…';
    result.className = ''; result.style.display = 'none';
    const fd = new FormData();
    fd.append('file', selectedFile);
    try {
      const r = await fetch('/upload', { method: 'POST', body: fd });
      const data = await r.json();
      if (r.ok && data.ok) {
        result.className = 'ok';
        result.textContent = '✅ 上传成功！' + data.message;
      } else {
        result.className = 'err';
        result.textContent = '❌ ' + (data.error || '上传失败');
      }
    } catch (e) {
      result.className = 'err';
      result.textContent = '❌ 网络错误：' + e.message;
    }
    btn.disabled = false; btn.textContent = '开始上传';
  };
</script>
</body>
</html>
"""


@app.get("/")
def index():
    return render_template_string(PAGE)


@app.post("/upload")
def upload():
    f = request.files.get("file")
    if not f:
        return jsonify(ok=False, error="没有选择文件"), 400

    headers = {"Authorization": f"Bearer {ANYTHINGLLM_KEY}"}
    with httpx.Client(base_url=ANYTHINGLLM_BASE, headers=headers, timeout=120) as client:
        # 1. 取第一个工作区
        ws = client.get("/api/v1/workspaces").json().get("workspaces", [])
        if not ws:
            return jsonify(ok=False, error="AnythingLLM 里没有工作区"), 500
        slug = ws[0]["slug"]
        name = ws[0].get("name", slug)

        # 2. 上传文件并直接加入该工作区（自动向量化嵌入）
        files = {"file": (f.filename, f.stream.read(), f.mimetype or "text/plain")}
        data = {"addToWorkspaces": slug}
        resp = client.post("/api/v1/document/upload", files=files, data=data)

    if resp.status_code >= 400:
        return jsonify(ok=False, error=f"AnythingLLM 返回 {resp.status_code}: {resp.text[:300]}"), 502

    docs = resp.json().get("documents", [])
    msg = f"文件「{f.filename}」已上传到工作区「{name}」，完成向量化嵌入。"
    if docs:
        msg += f"（{len(docs)} 个文档已处理）"
    return jsonify(ok=True, message=msg)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
