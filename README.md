# VOICEVOX OneStepAPI (CN/EN/Pseudo-JP TTS)

[English](#english) | [日本語](#japanese) | [中文](#chinese)

---

<a name="english"></a>
## 🇬🇧 English

### Authentication
All API requests require an API Key passed in the request header.
*   **Header Name**: `X-API-Key`
*   **Default Key**: `xingshuo` (Can be changed via `VOICEVOX_ADAPTER_KEY` environment variable)

### API Usage

#### 1. Get Voices
**Endpoint**: `GET /voices`  
**Header**: `X-API-Key: xingshuo`

#### 2. Synthesize Speech
**Endpoint**: `POST /tts`  
**Header**: `X-API-Key: xingshuo`
**Request Body (JSON)**:
```json
{
  "text": "Hello world",
  "speaker": 3
}
```

---

<a name="chinese"></a>
## 🇨🇳 中文

### 鉴权说明
所有 API 请求均需要在 Header 中携带 API Key。
*   **Header 名称**: `X-API-Key`
*   **默认 Key**: `xingshuo` (可以通过环境变量 `VOICEVOX_ADAPTER_KEY` 自定义)

### 接口调用指南

#### 1. 获取音色列表
**接口**: `GET /voices`  
**Header**: `X-API-Key: xingshuo`

#### 2. 语音合成接口
**接口**: `POST /tts`  
**Header**: `X-API-Key: xingshuo`
**请求体 (JSON)**:
```json
{
  "text": "你好世界",
  "speaker": 3
}
```

**JavaScript 调用示例**:
```javascript
const response = await fetch("https://your-domain.com/tts", {
  method: "POST",
  headers: { 
    "Content-Type": "application/json",
    "X-API-Key": "xingshuo" 
  },
  body: JSON.stringify({
    text: "你好世界",
    speaker: 3
  })
});
```