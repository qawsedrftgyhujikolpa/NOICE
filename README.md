# NOICE - The Digital Void

## 存在の消去による意思の可視化

**NOICE** は、動画から「形」と「色」を意図的に剥ぎ取り、そこに残る純粋な「動き（エネルギー）」だけを抽出して可視化するデジタル・アート・ツールです。

背景は静止したノイズ（虚無）に置換され、動体は激しい動的ノイズとして表現されます。
また、視覚だけでなく聴覚的にも「虚無」を体験できるよう、ホワイトノイズやブラウンノイズの生成・合成機能を備えています。

![NOICE Interface](https://via.placeholder.com/800x450/000000/ffffff?text=NOICE+Interface)

## Features

- **Void Engine**: 背景差分法を用いた動体抽出アルゴリズム。
- **Audio Synthesis**:
    - **Silence**: 完全な静寂。
    - **Original**: 元動画の音声をそのまま使用。
    - **White Noise**: 全周波数帯域のノイズ。
    - **Brown Noise**: 低周波成分の強い、深淵のノイズ。
- **High Performance Emulation**: PCのリソース（メモリ・GPU）を最大限に「しばき倒す」ような挙動とログ出力（演出）。
- **Video Download**: 処理結果をMP4ファイルとしてダウンロード可能（音声合成対応）。

## Requirements

- Windows 10/11
- Python 3.8+
- Anaconda (推奨)
- FFmpeg (Optional: なくてもMoviePyで動作します)

## Usage

1. **Launch**: `run_noice.bat` をダブルクリックして起動します。
2. **Access**: ブラウザが自動的に開き `http://127.0.0.1:8000` にアクセスします。
3. **Upload**: 動画ファイル(MP4/WebM)を画面にドラッグ＆ドロップします。
4. **Control**:
    - **Scale**: 解像度調整 (High/Mid/Low)
    - **Speed**: 再生速度調整
    - **Audio**: 音声モード選択
5. **Download**: "PROCESS & DOWNLOAD" ボタンを押して、虚無をファイルとして保存します。

## Tech Stack

- **Backend**: Python (FastAPI, OpenCV, NumPy, MoviePy)
- **Frontend**: Vanilla JS, CSS (Premium Void Design)

## Author

qawsedrftgyhujikolpa
