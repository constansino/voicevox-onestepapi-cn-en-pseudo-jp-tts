# VOICEVOX OneStepAPI (CN/EN/Pseudo-JP TTS)

[English](#english) | [日本語](#japanese) | [中文](#chinese)

---

<a name="english"></a>
## 🇬🇧 English

### Introduction
This is a lightweight middleware server (FastAPI) that acts as a bridge between your application and the **VOICEVOX** engine. It enables VOICEVOX characters (like Zundamon) to read **Chinese** (and English) text by converting it into "Pseudo-Japanese" (Pseudo-Chinese / 偽中国語) pronunciation using Katakana.

### Features
*   **One-Step TTS**: No need to call `audio_query` then `synthesis`. Just POST `/tts`.
*   **Pseudo-Chinese Support**: Built-in dictionary mapping 400+ Pinyin sounds to natural-sounding Katakana (e.g., "你好" -> "ニーハオ").
*   **English Support**: Basic rule-based conversion for English words.
*   **Custom Dictionary**: Easily fix specific words via `custom_dict.json`.
*   **CORS Ready**: Can be called directly from browser frontends.

### API Usage

#### 1. Get Voices
**Endpoint**: `GET /voices`  
Returns a list of all available speakers and their IDs.

#### 2. Synthesize Speech
**Endpoint**: `POST /tts`  
**Request Body (JSON)**:
```json
{
  "text": "Hello world, 你好世界。",
  "speaker": 3,
  "mode": "pseudo_jp",
  "speedScale": 1.1,
  "pitchScale": 0.0,
  "intonationScale": 1.2,
  "volumeScale": 1.0
}
```
**Parameters**:
*   `text` (string, required): The text to be spoken.
*   `speaker` (int, required): The ID of the speaker (get from `/voices`).
*   `mode` (string): `pseudo_jp` (default, converts to Katakana) or `raw` (sends text directly).
*   `speedScale` (float): Speed (0.5 to 2.0).
*   `pitchScale` (float): Pitch (-0.15 to 0.15).
*   `intonationScale` (float): Intonation (0.0 to 2.0).
*   `volumeScale` (float): Volume.

---

<a name="japanese"></a>
## 🇯🇵 日本語

### はじめに
これは、**VOICEVOX** エンジンのための軽量ミドルウェア（FastAPI）です。ずんだもんなどのキャラクターに、**中国語**（および英語）を「偽中国語」（日本語読みの中国語）として喋らせることができます。

### 機能
*   **ワンステップ TTS**: テキストと話者IDを送るだけで WAV が返ってきます。
*   **偽中国語対応**: 400以上のピンインを、より自然に聞こえるカタカナにマッピング。
*   **英語対応**: 簡単なルールベースで英語をカタカナ読み変換。
*   **辞書機能**: `custom_dict.json` で単語の読み方を自由に修正可能。

### API の使い方

#### 1. 話者リストの取得
**エンドポイント**: `GET /voices`  
利用可能なすべての話者とそのIDを返します。

#### 2. 音声合成
**エンドポイント**: `POST /tts`  
**リクエストボディ (JSON)**:
```json
{
  "text": "こんにちは世界、你好世界。",
  "speaker": 3,
  "mode": "pseudo_jp",
  "speedScale": 1.1,
  "pitchScale": 0.0,
  "intonationScale": 1.2,
  "volumeScale": 1.0
}
```
**パラメータ**:
*   `text` (string, 必須): 喋らせたいテキスト。
*   `speaker` (int, 必須): 話者ID (`/voices` で取得)。
*   `mode` (string): `pseudo_jp` (デフォルト、カタカナ変換あり) または `raw` (変換なし)。
*   `speedScale` (float): 話速 (0.5 - 2.0)。
*   `pitchScale` (float): ピッチ (-0.15 - 0.15)。
*   `intonationScale` (float): 抑揚 (0.0 - 2.0)。

---

<a name="chinese"></a>
## 🇨🇳 中文

### 简介
这是一个为 **VOICEVOX** 引擎设计的轻量级中间件（基于 FastAPI）。它让 Zundamon（ずんだもん）等角色能够通过“伪日语”（Pseudo-Japanese）的方式朗读**中文**。

### 功能特点
*   **一步合成**: 无需客户端分别调用 `audio_query` 和 `synthesis`，直接 POST `/tts` 即可获得 WAV 音频。
*   **伪中国语支持**: 内置全量拼音映射表，将中文转换为地道的“日式中文”风格。
*   **英文支持**: 简单的英文单词转片假名规则。
*   **自定义词典**: 可通过 `custom_dict.json` 修正特定单词的读法。

### 接口调用指南

#### 1. 获取音色列表
**接口**: `GET /voices`  
返回所有可用的角色及其对应的 `speaker_id`。

#### 2. 语音合成接口
**接口**: `POST /tts`  
**请求体 (JSON)**:
```json
{
  "text": "你好世界，这才是正宗的伪中国语！",
  "speaker": 3,
  "mode": "pseudo_jp",
  "speedScale": 1.1,
  "pitchScale": 0.0,
  "intonationScale": 1.2,
  "volumeScale": 1.0
}
```
**详细参数说明**:
*   `text` (字符串, 必填): 需要合成的文本。
*   `speaker` (整数, 必填): 角色 ID（从 `/voices` 获取）。
*   `mode` (字符串): `pseudo_jp`（默认，开启拟音转换）或 `raw`（直接发送原始文本）。
*   `speedScale` (浮点数): 语速（建议范围 0.5 - 2.0）。
*   `pitchScale` (浮点数): 音高（建议范围 -0.15 - 0.15）。
*   `intonationScale` (浮点数): 抑扬顿挫/语调（建议范围 0.0 - 2.0）。
*   `volumeScale` (浮点数): 音量。

**JavaScript 调用示例 (浏览器控制台)**:
```javascript
const response = await fetch("https://your-domain.com/tts", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    text: "你好世界",
    speaker: 3
  })
});
const blob = await response.blob();
new Audio(URL.createObjectURL(blob)).play();
```
