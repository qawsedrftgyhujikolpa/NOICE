
document.addEventListener('DOMContentLoaded', () => {
    const elements = {
        dropzone: document.getElementById('dropzone'),
        fileInput: document.getElementById('fileInput'),
        viewer: document.getElementById('viewer'),
        voidImage: document.getElementById('voidImage'),
        statusText: document.getElementById('statusText'),
        logConsole: document.getElementById('logConsole'),
        resetBtn: document.getElementById('resetBtn'),
        scale: document.getElementById('settingScale'),
        speed: document.getElementById('settingSpeed'),
        audio: document.getElementById('settingAudio')
    };

    let currentTempName = null;
    let currentOutputName = null;

    // オーディオ・コンテキスト関連
    let audioCtx = null;
    let noiseSource = null;
    let noiseGain = null;
    let originalAudioElement = null;

    // ノイズ生成器 (White/Brown)
    function playNoise(type) {
        stopAudio(); // 既存の音を停止

        if (type === 'mute') return;

        // 原音再生の場合
        if (type === 'original' && elements.fileInput.files.length > 0) {
            if (!originalAudioElement) {
                originalAudioElement = new Audio(URL.createObjectURL(elements.fileInput.files[0]));
                originalAudioElement.loop = true;
            }
            originalAudioElement.playbackRate = parseFloat(elements.speed.value);
            originalAudioElement.play().catch(e => console.log("Audio play failed (user interaction needed)", e));
            return;
        }

        // ノイズ生成 (Web Audio API)
        if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();

        // ContextがSuspendされている場合の対策
        if (audioCtx.state === 'suspended') {
            audioCtx.resume();
        }

        const bufferSize = 2 * audioCtx.sampleRate;
        const noiseBuffer = audioCtx.createBuffer(1, bufferSize, audioCtx.sampleRate);
        const output = noiseBuffer.getChannelData(0);
        let lastOut = 0; // for brown noise

        for (let i = 0; i < bufferSize; i++) {
            if (type === 'white') {
                output[i] = Math.random() * 2 - 1;
            } else if (type === 'brown') {
                const white = Math.random() * 2 - 1;
                output[i] = (lastOut + (0.02 * white)) / 1.02;
                lastOut = output[i];
                output[i] *= 3.5; // Gain correction
            }
        }

        noiseSource = audioCtx.createBufferSource();
        noiseSource.buffer = noiseBuffer;
        noiseSource.loop = true;

        noiseGain = audioCtx.createGain();
        noiseGain.gain.value = 0.1; // 音量は控えめに

        noiseSource.connect(noiseGain);
        noiseGain.connect(audioCtx.destination);
        noiseSource.start();
    }

    function stopAudio() {
        if (noiseSource) {
            try { noiseSource.stop(); } catch (e) { }
            noiseSource = null;
        }
        if (originalAudioElement) {
            originalAudioElement.pause();
            originalAudioElement.currentTime = 0;
        }
    }

    // --------------------------------------------------
    // ログ更新 (初心者のあなた：サーバーの呟きを拾っています)
    // --------------------------------------------------
    async function updateLogs() {
        try {
            const res = await fetch('/logs');
            const data = await res.json();
            if (data.logs) {
                elements.logConsole.textContent = data.logs;
                elements.logConsole.scrollTop = elements.logConsole.scrollHeight;
            }
        } catch (e) { }
    }
    setInterval(updateLogs, 2000);

    // --------------------------------------------------
    // アップロード & ストリーム開始
    // --------------------------------------------------
    elements.fileInput.addEventListener('change', async (e) => {
        if (e.target.files.length === 0) return;

        const file = e.target.files[0];
        elements.dropzone.classList.add('hidden');
        elements.viewer.classList.remove('hidden');
        updateStatus('抽出し、消去中...', '◈');

        const formData = new FormData();
        formData.append('file', file);

        try {
            const res = await fetch('/upload', { method: 'POST', body: formData });
            if (!res.ok) throw new Error(`Upload failed: ${res.status} ${res.statusText}`);

            const data = await res.json();
            currentTempName = data.temp_name;
            currentOutputName = data.output_name;

            startStreaming();
        } catch (err) {
            updateStatus('エラーが発生しました', '⚠');
            console.error("Upload Error Details:", err);
            elements.logConsole.textContent += `\n[CLIENT ERROR] Upload failed: ${err.message}`;
        }
    });

    function startStreaming() {
        if (!currentTempName) return;

        const params = new URLSearchParams({
            scale: elements.scale.value,
            is_color: 'true',
            speed: elements.speed.value
        });

        // タイムスタンプを付けてキャッシュを回避
        elements.voidImage.src = `/stream/${currentTempName}/${currentOutputName}?${params.toString()}&t=${Date.now()}`;
        updateStatus('虚無を投影中', '✯');

        // オーディオ再生開始
        playNoise(elements.audio.value);
    }

    // 設定変更時に再ストリーミング / オーディオ更新
    elements.scale.onchange = startStreaming;

    elements.speed.onchange = () => {
        startStreaming();
        if (originalAudioElement) {
            originalAudioElement.playbackRate = parseFloat(elements.speed.value);
        }
    };

    elements.audio.onchange = () => {
        playNoise(elements.audio.value);
    };

    elements.resetBtn.onclick = () => location.reload();

    // --------------------------------------------------
    // ダウンロード & レンダリング処理
    // --------------------------------------------------
    const downloadBtn = document.getElementById('downloadBtn');
    downloadBtn.onclick = async () => {
        if (!currentTempName) return;

        // UIロック
        downloadBtn.disabled = true;
        downloadBtn.querySelector('.btn-text').textContent = "RENDERING TO DISK...";
        updateStatus('MP4へ具現化中 (Wait)...', '💾');
        elements.voidImage.style.filter = "grayscale(100%) blur(5px)"; // 処理中の演出

        const params = new URLSearchParams({
            scale: elements.scale.value,
            is_color: 'true',
            audio_mode: elements.audio.value
        });

        try {
            // バックエンドでレンダリング実行
            const res = await fetch(`/process_download/${currentTempName}/${currentOutputName}?${params.toString()}`);
            const data = await res.json();

            if (data.status === 'completed') {
                // ダウンロードリンクを生成してクリック
                const link = document.createElement('a');
                link.href = data.url;
                link.download = currentOutputName;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);

                updateStatus('虚無の保存完了', '✔');
            } else {
                updateStatus('保存失敗', '✕');
            }
        } catch (e) {
            console.error(e);
            updateStatus('通信エラー', '⚠');
        } finally {
            // UI復帰
            downloadBtn.disabled = false;
            downloadBtn.querySelector('.btn-text').textContent = "PROCESS & DOWNLOAD";
            elements.voidImage.style.filter = "none";
        }
    };

    function updateStatus(text, icon) {
        elements.statusText.textContent = text;
        document.getElementById('statusIcon').textContent = icon;
    }

    // ドラッグ＆ドロップの視覚効果（初心者のあなた：おしゃれ用です）
    ['dragenter', 'dragover'].forEach(name => {
        elements.dropzone.addEventListener(name, () => elements.dropzone.style.borderColor = '#fff', false);
    });
    ['dragleave', 'drop'].forEach(name => {
        elements.dropzone.addEventListener(name, () => elements.dropzone.style.borderColor = 'var(--accent)', false);
    });
    elements.dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            elements.fileInput.files = files;
            elements.fileInput.dispatchEvent(new Event('change'));
        }
    }, false);
});
