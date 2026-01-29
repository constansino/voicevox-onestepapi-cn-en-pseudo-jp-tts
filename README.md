# VOICEVOX OneStepAPI (CN/EN/Pseudo-JP TTS)

[English](#english) | [日本語](#japanese) | [中文](#chinese)

---

<a name="english"></a>
## 🇬🇧 English

### Introduction
This is a lightweight middleware server (FastAPI) that acts as a bridge between your application and the **VOICEVOX** engine. It enables VOICEVOX characters (like Zundamon) to read **Chinese** (and English) text by converting it into "Pseudo-Japanese" (Pseudo-Chinese / 偽中国語) pronunciation using Katakana.

**Why?**
VOICEVOX natively only supports Japanese. If you send Chinese text, it remains silent or reads incorrectly. This adapter automatically converts:
*   **Chinese** -> Pinyin -> Katakana (optimized for "Pseudo-Chinese" accent)
*   **English** -> Katakana-like pronunciation

It also simplifies the API into a **single step**: just send text + speaker ID, and get a WAV file back.

### Features
*   **One-Step TTS**: No need to call `audio_query` then `synthesis`. Just POST `/tts`.
*   **Pseudo-Chinese Support**: Built-in dictionary mapping 400+ Pinyin sounds to natural-sounding Katakana (e.g., "你好" -> "ニーハオ").
*   **English Support**: Basic rule-based conversion for English words.
*   **Custom Dictionary**: Easily fix specific words via `custom_dict.json`.
*   **CORS Ready**: Can be called directly from browser frontends.

### Usage

#### 1. Requirements
*   Python 3.9+
*   A running [VOICEVOX Engine](https://github.com/VOICEVOX/voicevox_engine) (e.g., via Docker)

#### 2. Install & Run
```bash
# Clone repo
git clone https://github.com/constansino/voicevox-onestepapi-cn-en-pseudo-jp-tts.git
cd voicevox-onestepapi-cn-en-pseudo-jp-tts

# Install dependencies
pip install fastapi uvicorn requests pypinyin

# Set VOICEVOX engine URL (default: localhost:50021)
export VOICEVOX_BASE_URL="http://127.0.0.1:50021"

# Run server
python main.py
```

#### 3. API Examples

**Get available speakers:**
```bash
curl http://localhost:8000/voices
```

**Synthesize Speech (TTS):**
```bash
curl -X POST "http://localhost:8000/tts" \
     -H "Content-Type: application/json" \
     -d '{ "text": "你好世界, this is a test.", "speaker": 3, "speedScale": 1.1 }' \
     --output output.wav
```

---

<a name="japanese"></a>
## 🇯🇵 日本語

### はじめに
これは、**VOICEVOX** エンジンのための軽量ミドルウェア（FastAPI）です。ずんだもんなどのキャラクターに、**中国語**（および英語）を「偽中国語」（日本語読みの中国語）として喋らせることができます。

**仕組み**
通常、VOICEVOXに中国語を送っても読み上げられません。このアダプターは以下のように自動変換します：
*   **中国語** -> ピンイン -> カタカナ（「偽中国語」風の発音に最適化）
*   **英語** -> 日本語なまりの英語読み

また、API呼び出しを**ワンステップ**に簡略化します（`audio_query` + `synthesis` を内部で処理）。

### 機能
*   **ワンステップ TTS**: テキストと話者IDを送るだけで WAV が返ってきます。
*   **偽中国語対応**: 400以上のピンインを、より自然に聞こえるカタカナにマッピング（例：「你好」 -> 「ニーハオ」）。
*   **英語対応**: 簡単なルールベースで英語をカタカナ読み変換。
*   **辞书機能**: `custom_dict.json` で単語の読み方を自由に修正可能。

### 使い方

#### 1. 前提条件
*   Python 3.9以上
*   [VOICEVOX Engine](https://github.com/VOICEVOX/voicevox_engine) が起動していること

#### 2. インストールと実行
```bash
# リポジトリをクローン
git clone https://github.com/constansino/voicevox-onestepapi-cn-en-pseudo-jp-tts.git
cd voicevox-onestepapi-cn-en-pseudo-jp-tts

# 依存ライブラリのインストール
pip install fastapi uvicorn requests pypinyin

# VOICEVOXエンジンのURLを設定 (デフォルト: localhost:50021)
export VOICEVOX_BASE_URL="http://127.0.0.1:50021"

# サーバー起動
python main.py
```

#### 3. API 利用例

**話者リストの取得:**
```bash
curl http://localhost:8000/voices
```

**音声合成 (TTS):**
```bash
curl -X POST "http://localhost:8000/tts" \
     -H "Content-Type: application/json" \
     -d '{ "text": "你好世界, this is a test.", "speaker": 3, "speedScale": 1.1 }' \
     --output output.wav
```

---

<a name="chinese"></a>
## 🇨🇳 中文

### 简介
这是一个为 **VOICEVOX** 引擎设计的轻量级中间件（基于 FastAPI）。它让 Zundamon（ずんだもん）等角色能够通过“伪日语”（Pseudo-Japanese）的方式朗读**中文**。

**核心原理**
VOICEVOX 原生仅支持日语。如果您直接发送中文，它无法识别。本插件会自动完成以下转换：
*   **中文** -> 拼音 -> 片假名（经过精心调校，听感接近日式中文/伪中国语）
*   **英文** -> 简单的日式英语发音规则

同时，它将原本复杂的两步调用（查询+合成）封装为**一步调用**接口。

### 功能特点
*   **一步合成**: 无需客户端分别调用 `audio_query` 和 `synthesis`，直接 POST `/tts` 即可获得 WAV 音频。
*   **伪中国语支持**: 内置全量拼音映射表，将中文转换为地道的“君日本语本当上手”风格（如：“你好” -> “ニーハオ”）。
*   **英文支持**: 简单的英文单词转片假名规则。
*   **自定义词典**: 可通过 `custom_dict.json` 修正特定单词的读法。
*   **跨域支持**: 内置 CORS，前端网页可直接调用。

### 部署指南

#### 1. 环境要求
*   Python 3.9+
*   已运行的 [VOICEVOX Engine](https://github.com/VOICEVOX/voicevox_engine)

#### 2. 安装与运行
```bash
# 克隆仓库
git clone https://github.com/constansino/voicevox-onestepapi-cn-en-pseudo-jp-tts.git
cd voicevox-onestepapi-cn-en-pseudo-jp-tts

# 安装依赖
pip install fastapi uvicorn requests pypinyin

# 设置 VOICEVOX 引擎地址 (默认: localhost:50021)
export VOICEVOX_BASE_URL="http://127.0.0.1:50021"

# 启动服务
python main.py
```

#### 3. 接口调用

**获取可用角色列表:**
```bash
curl http://localhost:8000/voices
```

**语音合成:**
```bash
curl -X POST "http://localhost:8000/tts" \
     -H "Content-Type: application/json" \
     -d '{ "text": "你好世界, 这是一个测试。", "speaker": 3, "speedScale": 1.1 }' \
     --output output.wav
```