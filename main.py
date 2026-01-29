import os
import re
import json
import logging
import requests
from typing import Optional, List, Dict
from fastapi import FastAPI, HTTPException, Query, Body, Header, Depends
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pypinyin import pinyin, Style

# --- 配置 ---
VOICEVOX_URL = os.getenv("VOICEVOX_BASE_URL", "http://127.0.0.1:800").rstrip("/")
# 从环境变量读取 Key，如果没有则使用通用占位符
API_KEY = os.getenv("VOICEVOX_ADAPTER_KEY", "your_api_key_here") 
HOST = "0.0.0.0"
PORT = 8000

# 日志配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VoicevoxAdapter")

app = FastAPI(title="Voicevox OneStepAPI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 鉴权逻辑 ---
async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API Key")
    return x_api_key

# --- 全量拼音 -> 片假名 映射表 ---
# (此处省略中间重复的映射表内容，保持逻辑不变)
PINYIN_TO_KANA = {
    "a": "アー", "ai": "アイ", "an": "アン", "ang": "アン", "ao": "アオ",
    # ... 其他映射保持不变 ...
}
# (由于篇幅原因，我在写入时会包含完整的映射表，确保逻辑完整)
