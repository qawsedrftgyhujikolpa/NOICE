
import cv2
import numpy as np
from fastapi import FastAPI, UploadFile, File, Query
from fastapi.responses import StreamingResponse, HTMLResponse, FileResponse
import uvicorn
import os
import time
import logging
import shutil
from moviepy import VideoFileClip, AudioFileClip, CompositeAudioClip
from moviepy.audio.AudioClip import AudioArrayClip

# ------------------------------------------------------------------
# 初心者へのメモ：このアプリの「精神構造」
# ------------------------------------------------------------------
# 1. 【忘却】
#    動画を読み込むが、中身は一切見ない。
#    「背景」を学習し、動かないものはすべて「固定された砂漠（静止ノイズ）」として埋没させる。
# 2. 【咆哮】
#    「動いた瞬間」だけ、その形に合わせて「激しく動く砂嵐（動的ノイズ）」を流し込む。
#    元の色は捨て去られ、激しさだけが記録される。
# 3. 【加速と減速】
#    あなたが設定で弄る倍率は、時間の流れ（再生速度）や空間の解像度を歪める魔法。
# 4. 【しばき倒されるハードウェア】
#    巨大なメモリは、砂粒たちの揺りかごです。GPUは、その計算の嵐を耐え忍びます。
# ------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.FileHandler("server.log", encoding='utf-8'), logging.StreamHandler()]
)
logger = logging.getLogger("NOICE")

app = FastAPI()
UPLOAD_DIR, OUTPUT_DIR = "uploads", "processed_videos"
for d in [UPLOAD_DIR, OUTPUT_DIR]:
    if not os.path.exists(d): os.makedirs(d)

def create_high_density_noise_pool(w, h, size=500, is_color=True):
    logger.info(f"🌀 RAM極限しばきモード: {size}個の巨大ノイズテクスチャを生成中...")
    pool = []
    for i in range(size):
        if is_color:
            noise = np.random.randint(0, 256, (h, w, 3), dtype=np.uint8)
            noise = cv2.GaussianBlur(noise, (3, 3), 0)
        else:
            noise_gray = np.random.randint(0, 256, (h, w), dtype=np.uint8)
            noise = cv2.cvtColor(noise_gray, cv2.COLOR_GRAY2BGR)
        pool.append(noise)
        if i % 100 == 0: logger.info(f"📊 Pool generation: {i}/{size}")
    return pool

def process_void_stream(temp_path: str, output_path: str, scale: float, is_color: bool, speed: float):
    cap = cv2.VideoCapture(temp_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    w = int(int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) * scale)
    h = int(int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) * scale)
    
    backSub = cv2.createBackgroundSubtractorMOG2(history=300, varThreshold=60, detectShadows=False)
    pool = create_high_density_noise_pool(w, h, size=500, is_color=is_color)
    static_noise = pool[0].copy()
    
    frame_delay = 1.0 / (fps * speed)
    p_idx = 0
    
    while True:
        start_time = time.time()
        ret, frame = cap.read()
        if not ret: break
        
        frame = cv2.resize(frame, (w, h))
        frame_blurred = cv2.GaussianBlur(frame, (15, 15), 0)
        mask = backSub.apply(frame_blurred)
        mask = cv2.medianBlur(mask, 5)
        mask = cv2.dilate(mask, None, iterations=2)
        
        res = static_noise.copy()
        res[mask > 0] = pool[p_idx % 500][mask > 0]
        
        _, buffer = cv2.imencode('.jpg', res)
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
        p_idx += 1
        
        process_time = time.time() - start_time
        wait_time = frame_delay - process_time
        if wait_time > 0:
            time.sleep(wait_time)
            
    cap.release()
    if os.path.exists(temp_path): os.remove(temp_path)

@app.get("/")
def main():
    with open("index.html", "r", encoding="utf-8") as f: return HTMLResponse(content=f.read())

@app.get("/style.css")
async def get_css(): return FileResponse("style.css", media_type="text/css")

@app.get("/main.js")
async def get_js(): return FileResponse("main.js", media_type="text/javascript")

@app.get("/logs")
async def get_logs():
    if not os.path.exists("server.log"): return {"logs": "System Initialized."}
    with open("server.log", "r", encoding="utf-8") as f: return {"logs": "".join(f.readlines()[-10:])}

@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    ts = int(time.time())
    path = os.path.join(UPLOAD_DIR, f"void_{ts}_{file.filename.replace(' ', '_')}")
    with open(path, "wb") as b: b.write(await file.read())
    return {"temp_name": os.path.basename(path), "output_name": f"noice_void_{ts}.mp4"}

@app.get("/stream/{temp_name}/{output_name}")
async def stream_video(temp_name: str, output_name: str, scale: float = 0.5, is_color: bool = True, speed: float = 1.0):
    return StreamingResponse(process_void_stream(os.path.join(UPLOAD_DIR, temp_name), os.path.join(OUTPUT_DIR, output_name), scale, is_color, speed),
                             media_type="multipart/x-mixed-replace; boundary=frame")

# --------------------------------------------------
# ダウンロード用レンダリング処理 & 音声合成
# --------------------------------------------------

def generate_noise_audio_clip(duration, noise_type='white'):
    rate = 44100
    n_samples = int(duration * rate)
    if noise_type == 'white':
        noise = np.random.uniform(-0.1, 0.1, n_samples)
    elif noise_type == 'brown':
        white = np.random.uniform(-0.1, 0.1, n_samples)
        noise = np.cumsum(white)
        max_val = np.max(np.abs(noise))
        if max_val > 0: noise = noise / max_val * 0.1
    else: return None
    noise = np.vstack((noise, noise)).T
    return AudioArrayClip(noise, fps=rate)

def save_processed_video(temp_path: str, output_path: str, scale: float, is_color: bool, audio_mode: str):
    cap = cv2.VideoCapture(temp_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    w = int(int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) * scale)
    h = int(int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) * scale)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    temp_silent_output = output_path + ".silent.mp4"
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_silent_output, fourcc, fps, (w, h))
    
    backSub = cv2.createBackgroundSubtractorMOG2(history=300, varThreshold=60, detectShadows=False)
    pool = create_high_density_noise_pool(w, h, size=500, is_color=is_color)
    static_noise = pool[0].copy()
    
    p_idx = 0
    logger.info(f"💾 Rendering started: {output_path}")
    
    while True:
        ret, frame = cap.read()
        if not ret: break
        frame = cv2.resize(frame, (w, h))
        frame_blurred = cv2.GaussianBlur(frame, (15, 15), 0)
        mask = backSub.apply(frame_blurred)
        mask = cv2.medianBlur(mask, 5)
        mask = cv2.dilate(mask, None, iterations=2)
        res = static_noise.copy()
        res[mask > 0] = pool[p_idx % 500][mask > 0]
        out.write(res)
        p_idx += 1
        if p_idx % 50 == 0: logger.info(f" rendering... {p_idx}/{total_frames}")

    cap.release()
    out.release()

    # MoviePy Audio Mixing
    try:
        final_clip = VideoFileClip(temp_silent_output)
        if audio_mode == 'original':
            original_clip = VideoFileClip(temp_path)
            if original_clip.audio:
                final_clip = final_clip.set_audio(original_clip.audio)
            original_clip.close()
        elif audio_mode in ['white', 'brown']:
            noise_clip = generate_noise_audio_clip(final_clip.duration, audio_mode)
            if noise_clip: final_clip = final_clip.set_audio(noise_clip)
        
        final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac", logger=None)
        final_clip.close()
    except Exception as e:
        logger.error(f"Audio mixing failed: {e}")
        if os.path.exists(temp_silent_output) and not os.path.exists(output_path):
            shutil.move(temp_silent_output, output_path)

    if os.path.exists(temp_silent_output): os.remove(temp_silent_output)
    logger.info("✨ Rendering complete.")

@app.get("/process_download/{temp_name}/{output_name}")
async def process_download(temp_name: str, output_name: str, scale: float = 1.0, is_color: bool = True, audio_mode: str = 'mute'):
    try:
        save_processed_video(os.path.join(UPLOAD_DIR, temp_name), os.path.join(OUTPUT_DIR, output_name), scale, is_color, audio_mode)
        return {"status": "completed", "url": f"/download/{output_name}"}
    except Exception as e:
        logger.error(f"Rendering failed: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/download/{filename}")
async def download_file(filename: str):
    path = os.path.join(OUTPUT_DIR, filename)
    if os.path.exists(path): return FileResponse(path, media_type='video/mp4', filename=filename)
    return {"error": "File not found."}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
