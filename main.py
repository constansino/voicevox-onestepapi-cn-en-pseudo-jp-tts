import os
import re
import json
import logging
import requests
import uuid
from datetime import datetime
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Header, Depends, Request
from fastapi.responses import Response, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pypinyin import pinyin, Style
from sqlalchemy import Column, String, Integer, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# --- 数据库配置 ---
DB_URL = "sqlite:///./tts_management.db"
Base = declarative_base()
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class APIKeyRecord(Base):
    __tablename__ = "api_keys"
    key = Column(String, primary_key=True, index=True)
    credits = Column(Integer, default=50)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# --- 配置 ---
VOICEVOX_URL = os.getenv("VOICEVOX_BASE_URL", "http://127.0.0.1:800").rstrip("/")
ADMIN_KEY = "xingshuo_admin" # 用于管理后台的 Key

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_headers=["*"], allow_methods=["*"])

# --- 拼音映射表 ---
PINYIN_TO_KANA = {
    "a": "アー", "ai": "アイ", "an": "アン", "ang": "アン", "ao": "アオ",
    "ba": "バー", "bai": "バイ", "ban": "バン", "bang": "バン", "bao": "バオ", "bei": "ベイ", "ben": "ベン", "beng": "ベン", "bi": "ビー", "bian": "ビェン", "biao": "ビャオ", "bie": "ビェ", "bin": "ビン", "bing": "ビン", "bo": "ボ", "bu": "ブー",
    "ca": "ツァ", "cai": "ツァイ", "can": "ツァン", "cang": "ツァン", "cao": "ツァオ", "ce": "ツァ", "cen": "ツェン", "ceng": "ツェン", "ci": "ツー", "cong": "ツォン", "cou": "ツォウ", "cu": "ツー", "cuan": "ツァン", "cui": "ツイ", "cun": "ツン", "cuo": "ツォ",
    "cha": "チャー", "chai": "チャイ", "chan": "チャン", "chang": "チャン", "chao": "チャオ", "che": "チャー", "chen": "チェン", "cheng": "チェン", "chi": "チー", "chong": "チョン", "chou": "チョウ", "chu": "チュー", "chua": "チュア", "chuai": "チュアイ", "chuan": "チュアン", "chuang": "チュアン", "chui": "チュイ", "chun": "チュン", "chuo": "チュオ",
    "da": "ダー", "dai": "ダイ", "dan": "ダン", "dang": "ダン", "dao": "ダオ", "de": "ダ", "dei": "デイ", "den": "デン", "deng": "デン", "di": "ディー", "dia": "ディア", "dian": "ディェン", "diao": "ディアオ", "die": "ディェ", "ding": "ディン", "diu": "ディウ", "dong": "ドン", "dou": "ドウ", "du": "ドゥー", "duan": "ドゥアン", "dui": "ドゥイ", "dun": "ドゥン", "duo": "ドゥオ",
    "e": "アー", "ei": "エイ", "en": "エン", "eng": "エン", "er": "アル",
    "fa": "ファー", "fan": "ファン", "fang": "ファン", "fei": "フェイ", "fen": "フェン", "feng": "フェン", "fo": "フォ", "fou": "フォウ", "fu": "フー",
    "ga": "ガー", "gai": "ガイ", "gan": "ガン", "gang": "ガン", "gao": "ガオ", "ge": "ガ", "gei": "ゲイ", "gen": "ゲン", "geng": "ゲン", "gong": "ゴン", "gou": "ゴウ", "gu": "グー", "gua": "グア", "guai": "グアイ", "guan": "グアン", "guang": "グアン", "gui": "グイ", "gun": "グン", "guo": "グオ",
    "ha": "ハー", "hai": "ハイ", "han": "ハン", "hang": "ハン", "hao": "ハオ", "he": "ハ", "hei": "ヘイ", "hen": "ヘン", "heng": "ヘン", "hong": "ホン", "hou": "ホウ", "hu": "フー", "hua": "ファ", "huai": "ファイ", "huan": "ファン", "huang": "ファン", "hui": "フェイ", "hun": "フン", "huo": "フォ",
    "ji": "ジー", "jia": "ジャ", "jian": "ジェン", "jiang": "ジャン", "jiao": "ジャオ", "jie": "ジェ", "jin": "ジン", "jing": "ジン", "jiong": "ジォン", "jiu": "ジウ", "ju": "ジュー", "juan": "ジュェン", "jue": "ジュェ", "jun": "ジュン",
    "ka": "カー", "kai": "カイ", "kan": "カン", "kang": "カン", "kao": "カオ", "ke": "カ", "kei": "ケイ", "ken": "ケン", "keng": "ケン", "kong": "コン", "kou": "コウ", "ku": "クー", "kua": "クア", "kuai": "クアイ", "kuan": "クアン", "kuang": "クアン", "kui": "クイ", "kun": "クン", "kuo": "クオ",
    "la": "ラー", "lai": "ライ", "lan": "ラン", "lang": "ラン", "lao": "ラオ", "le": "ラ", "lei": "レイ", "leng": "レン", "li": "リー", "lia": "リア", "lian": "リェン", "liang": "リャン", "liao": "リャオ", "lie": "リェ", "lin": "リン", "ling": "リン", "liu": "リウ", "long": "ロン", "lou": "ロウ", "lu": "ルー", "lv": "リュー", "luan": "ルアン", "lue": "ルェ", "lun": "ルン", "luo": "ルオ",
    "ma": "マー", "mai": "マイ", "man": "マン", "mang": "マン", "mao": "马奥", "me": "マ", "mei": "メイ", "men": "メン", "meng": "メン", "mi": "ミー", "mian": "ミェン", "miao": "ミャオ", "mie": "ミェ", "min": "ミン", "ming": "ミン", "miu": "ミウ", "mo": "モ", "mou": "モウ", "mu": "ムー",
    "na": "ナー", "nai": "ナイ", "nan": "ナン", "nang": "ナン", "nao": "ナオ", "ne": "ナ", "nei": "ネイ", "nen": "ネン", "neng": "ネン", "ni": "ニー", "nian": "ニェン", "niang": "ニャン", "niao": "ニャオ", "nie": "ニェ", "nin": "ニン", "ning": "ニン", "niu": "ニウ", "nong": "ノン", "nou": "ノウ", "nu": "ヌー", "nv": "ニュー", "nuan": "ヌアン", "nue": "ニュェ", "nuo": "ヌ奥",
    "o": "オー", "ou": "オウ",
    "pa": "パー", "pai": "パイ", "pan": "パン", "pang": "パン", "pao": "パオ", "pei": "ペイ", "pen": "ペン", "peng": "ペン", "pi": "ピー", "pian": "ピェン", "piao": "ピャオ", "pie": "ピェ", "pin": "ピン", "ping": "ピン", "po": "ポ", "pou": "ポウ", "pu": "プー",
    "qi": "チー", "qia": "チャ", "qian": "チェン", "qiang": "チャン", "qiao": "チャオ", "qie": "チェ", "qin": "チン", "qing": "チン", "qiong": "チョン", "qiu": "チウ", "qu": "チュー", "quan": "チュェン", "que": "チュェ", "qun": "チュン",
    "ran": "ラン", "rang": "ラン", "rao": "ラオ", "re": "ラ", "ren": "レン", "reng": "レン", "ri": "リー", "rong": "ロン", "rou": "ロウ", "ru": "ルー", "ruan": "ルアン", "rui": "ルイ", "run": "ルン", "ruo": "ルオ",
    "sa": "サー", "sai": "サイ", "san": "サン", "sang": "サン", "sao": "サオ", "se": "サ", "sen": "セン", "seng": "セン", "si": "スー", "song": "ソン", "sou": "ソウ", "su": "スー", "suan": "スアン", "sui": "スイ", "sun": "スン", "suo": "スオ",
    "sha": "シャー", "shai": "シャイ", "shan": "シャン", "shang": "シャン", "shao": "シャオ", "she": "シェ", "shei": "シェイ", "shen": "シェン", "sheng": "シェン", "shi": "シー", "shou": "ショウ", "shu": "シュー", "shua": "シュア", "shuai": "シュアイ", "shuan": "シュアン", "shuang": "シュアン", "shui": "シュイ", "shun": "シュン", "shuo": "シュオ",
    "ta": "ター", "tai": "タイ", "tan": "タン", "tang": "タン", "tao": "タオ", "te": "タ", "teng": "テン", "ti": "ティー", "tian": "ティェン", "tiao": "ティアオ", "tie": "ティェ", "ting": "ティン", "tong": "トン", "tou": "トウ", "tu": "トゥー", "tuan": "トゥアン", "tui": "トゥイ", "tun": "トゥン", "tuo": "トゥオ",
    "wa": "ワー", "wai": "ワイ", "wan": "ワン", "wang": "ワン", "wei": "ウェイ", "wen": "ウェン", "weng": "ウェン", "wo": "ウォ", "wu": "ウー",
    "xi": "シー", "xia": "シア", "xian": "シェン", "xiang": "シャン", "xiao": "シャオ", "xie": "シェ", "xin": "シン", "xing": "シン", "xiong": "ション", "xiu": "シウ", "xu": "シュー", "xuan": "シュェン", "xue": "シュェ", "xun": "シュン",
    "ya": "ヤー", "yan": "イェン", "yang": "ヤン", "yao": "ヤオ", "ye": "イェ", "yi": "イー", "yin": "イン", "ying": "イン", "yong": "ヨン", "you": "ヨウ", "yu": "ユー", "yuan": "ユェン", "yue": "ユェ", "yun": "ユン",
    "za": "ザー", "zai": "ザイ", "zan": "ザン", "zang": "ザン", "zao": "ザオ", "ze": "ザ", "zei": "ゼイ", "zen": "ゼン", "zeng": "ゼン", "zi": "ツー", "zong": "ゾン", "zou": "ゾウ", "zu": "ズー", "zuan": "ズアン", "zui": "ズイ", "zun": "ズン", "zuo": "ズオ",
    "zha": "ジャー", "zhai": "ジャイ", "zhan": "ジャン", "zhang": "ジャン", "zhao": "ジャオ", "zhe": "ジャ", "zhei": "ジェイ", "zhen": "ジェン", "zheng": "ジェン", "zhi": "ジー", "zhong": "ジョン", "zhou": "ジョウ", "zhu": "ジュー", "zhua": "ジュ阿", "zhuai": "ジュアイ", "zhuan": "ジュアン", "zhuang": "ジュアン", "zhui": "ジュイ", "zhun": "ジュン", "zhuo": "ジュオ"
}

# --- 逻辑类 ---
class PseudoConverter:
    def __init__(self):
        pass
    def is_chinese(self, char): return '\u4e00' <= char <= '\u9fff'
    def process_chinese(self, text):
        py_list = pinyin(text, style=Style.NORMAL, errors='default')
        return "".join([PINYIN_TO_KANA.get(p[0].lower().replace("ü", "v"), p[0]) for p in py_list])
    def process_english(self, text):
        text = text.lower()
        replacements = [("th", "s"), ("ph", "f"), ("v", "b"), ("l", "r"), ("tion", "shon"), ("si", "shi"), ("tu", "chu"), ("ti", "chi")]
        for old, new in replacements: text = text.replace(old, new)
        if text[-1] not in "aeiou": text += "o" if text[-1] in "td" else "u"
        return text
    def convert(self, text):
        tokens = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z0-9]+|[^a-zA-Z0-9\u4e00-\u9fff]+', text)
        return "".join([self.process_chinese(t) if self.is_chinese(t[0]) else (self.process_english(t) if re.match(r'[a-zA-Z]+', t) else t) for t in tokens])

converter = PseudoConverter()

# --- 数据库操作 ---
def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

# --- 请求模型 ---
class TTSRequest(BaseModel):
    text: str
    speaker: int
    mode: Optional[str] = "pseudo_jp"
    speedScale: Optional[float] = 1.1
    pitchScale: Optional[float] = 0.0
    intonationScale: Optional[float] = 1.0

# --- API 接口 ---

@app.get("/voices")
def get_voices():
    r = requests.get(f"{VOICEVOX_URL}/speakers")
    return [{"id": s["id"], "name": c["name"], "style": s["name"]} for c in r.json() for s in c["styles"]]

@app.get("/check_key")
def check_key(key: str, db: Session = Depends(get_db)):
    record = db.query(APIKeyRecord).filter(APIKeyRecord.key == key).first()
    if not record: raise HTTPException(status_code=404, detail="Key not found")
    return {"credits": record.credits}

@app.post("/tts")
def tts(req: TTSRequest, x_api_key: str = Header(...), db: Session = Depends(get_db)):
    # 鉴权扣费
    record = db.query(APIKeyRecord).filter(APIKeyRecord.key == x_api_key).first()
    if not record or record.credits <= 0: raise HTTPException(status_code=401, detail="Invalid key or no credits")
    
    target_text = converter.convert(req.text) if req.mode == "pseudo_jp" else req.text
    
    # VOICEVOX 流程
    q = requests.post(f"{VOICEVOX_URL}/audio_query", params={"text": target_text, "speaker": req.speaker}).json()
    q["speedScale"], q["pitchScale"], q["intonationScale"] = req.speedScale, req.pitchScale, req.intonationScale
    
    audio = requests.post(f"{VOICEVOX_URL}/synthesis", params={"speaker": req.speaker}, json=q).content
    
    record.credits -= 1
    db.commit()
    return Response(content=audio, media_type="audio/wav")

# --- 管理接口 ---
@app.post("/admin/generate_key")
def generate_key(admin_key: str, credits: int = 50, db: Session = Depends(get_db)):
    if admin_key != ADMIN_KEY: raise HTTPException(status_code=403)
    new_key = "vv-" + str(uuid.uuid4())[:8]
    db.add(APIKeyRecord(key=new_key, credits=credits))
    db.commit()
    return {"key": new_key, "credits": credits}

# --- 前端界面 (index.html) ---
@app.get("/", response_class=HTMLResponse)
def index():
    return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Voicevox OneStep - 伪中国语合成</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>
    <style>
        .avatar-card { transition: all 0.2s; cursor: pointer; }
        .avatar-card.active { border-color: #3b82f6; background: #eff6ff; transform: scale(1.05); }
    </style>
</head>
<body class="bg-gray-50 min-h-screen">
    <div id="app" class="max-w-4xl mx-auto py-10 px-4">
        <header class="text-center mb-10">
            <h1 class="text-4xl font-bold text-gray-800 mb-2">Voicevox OneStep</h1>
            <p class="text-gray-600">中英日三语拟音合成 · 伪中国语大师</p>
        </header>

        <main class="grid grid-cols-1 md:grid-cols-3 gap-8">
            <!-- 左侧：角色选择 -->
            <div class="md:col-span-2">
                <div class="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                    <h2 class="text-lg font-semibold mb-4">1. 选择声线</h2>
                    <div class="grid grid-cols-3 sm:grid-cols-4 gap-4 overflow-y-auto max-h-[400px] pr-2">
                        <div v-for="v in voices" :key="v.id" 
                             @click="selectedSpeaker = v"
                             :class="['avatar-card p-3 rounded-xl border-2 text-center', selectedSpeaker.id == v.id ? 'active' : 'border-gray-50']">
                            <div class="w-12 h-12 bg-blue-100 rounded-full mx-auto mb-2 flex items-center justify-center text-blue-500 font-bold">
                                {{ v.name[0] }}
                            </div>
                            <div class="text-xs font-medium truncate">{{ v.name }}</div>
                            <div class="text-[10px] text-gray-400">{{ v.style }}</div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 右侧：控制与额度 -->
            <div class="space-y-6">
                <div class="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                    <h2 class="text-lg font-semibold mb-4">账户</h2>
                    <input v-model="apiKey" type="password" placeholder="输入 API Key" class="w-full p-2 border rounded-lg mb-2 text-sm">
                    <div class="flex justify-between items-center text-sm">
                        <button @click="checkKey" class="text-blue-500 hover:underline">查询额度</button>
                        <span class="text-gray-500" v-if="credits !== null">剩余: {{ credits }}</span>
                    </div>
                    <a href="#" class="block mt-4 text-center text-xs text-gray-400 hover:text-blue-500">获取更多额度? 联系管理员</a>
                </div>

                <div class="bg-blue-600 p-6 rounded-2xl shadow-lg text-white">
                    <h2 class="text-lg font-semibold mb-2">当前选择</h2>
                    <p class="text-sm opacity-90">{{ selectedSpeaker.name || '未选择' }} - {{ selectedSpeaker.style }}</p>
                </div>
            </div>

            <!-- 底部：输入与预览 -->
            <div class="md:col-span-3">
                <div class="bg-white p-8 rounded-2xl shadow-sm border border-gray-100">
                    <textarea v-model="text" rows="3" placeholder="输入文字（支持中、英、日混写）..." 
                              class="w-full p-4 border rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none mb-4"></textarea>
                    
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                        <div>
                            <label class="text-xs text-gray-400 block mb-1">语速: {{ params.speed }}</label>
                            <input type="range" v-model="params.speed" min="0.5" max="1.5" step="0.1" class="w-full">
                        </div>
                        <div>
                            <label class="text-xs text-gray-400 block mb-1">抑扬: {{ params.intonation }}</label>
                            <input type="range" v-model="params.intonation" min="0" max="2" step="0.1" class="w-full">
                        </div>
                    </div>

                    <div class="flex flex-col md:flex-row gap-4 items-center">
                        <button @click="synthesize" :disabled="loading" 
                                class="w-full md:w-auto px-10 py-3 bg-blue-600 text-white rounded-xl font-bold hover:bg-blue-700 disabled:bg-gray-300 transition-all shadow-lg shadow-blue-200">
                            {{ loading ? '合成中...' : '立即合成' }}
                        </button>
                        
                        <div v-if="audioUrl" class="flex-1 flex items-center gap-4 bg-gray-50 p-2 rounded-xl w-full">
                            <audio :src="audioUrl" controls class="flex-1 h-10"></audio>
                            <a :href="audioUrl" download="voice.wav" class="text-blue-500 hover:text-blue-700 font-medium px-4">下载</a>
                        </div>
                    </div>
                </div>
            </div>
        </main>

        <footer class="mt-20 border-t pt-10 text-center text-gray-400 text-sm">
            <div class="space-x-6 mb-4">
                <a href="/docs" class="hover:text-gray-600">API文档</a>
                <a href="#" class="hover:text-gray-600">GitHub</a>
                <a href="#" class="hover:text-gray-600">词典维护</a>
            </div>
            <p>&copy; 2026 Voicevox OneStep API. All rights reserved.</p>
        </footer>
    </div>

    <script>
        const { createApp, ref, onMounted } = Vue;
        createApp({
            setup() {
                const voices = ref([]);
                const selectedSpeaker = ref({});
                const text = ref("现在就算告诉我AI能操我也不稀奇");
                const apiKey = ref(localStorage.getItem('vv_key') || "xingshuo");
                const credits = ref(null);
                const audioUrl = ref(null);
                const loading = ref(false);
                const params = ref({ speed: 1.1, intonation: 1.2 });

                onMounted(async () => {
                    const res = await fetch('/voices');
                    voices.value = await res.json();
                    if (voices.value.length) selectedSpeaker.value = voices.value[0];
                });

                const checkKey = async () => {
                    try {
                        const res = await fetch(`/check_key?key=${apiKey.value}`);
                        const data = await res.json();
                        credits.value = data.credits;
                        localStorage.setItem('vv_key', apiKey.value);
                    } catch { alert('Key 错误或不存在'); }
                };

                const synthesize = async () => {
                    if (!apiKey.value) return alert('请输入 API Key');
                    loading.value = true;
                    try {
                        const res = await fetch('/tts', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json', 'X-API-Key': apiKey.value },
                            body: JSON.stringify({
                                text: text.value,
                                speaker: selectedSpeaker.value.id,
                                speedScale: parseFloat(params.value.speed),
                                intonationScale: parseFloat(params.value.intonation)
                            })
                        });
                        if (!res.ok) throw new Error(await res.text());
                        const blob = await res.blob();
                        if (audioUrl.value) URL.revokeObjectURL(audioUrl.value);
                        audioUrl.value = URL.createObjectURL(blob);
                        credits.value--; 
                    } catch (e) { alert('合成失败: ' + e.message); }
                    finally { loading.value = false; }
                };

                return { voices, selectedSpeaker, text, apiKey, credits, audioUrl, loading, params, checkKey, synthesize };
            }
        }).mount('#app');
    </script>
</body>
</html>
    """

# --- 文档接口 ---
@app.get("/docs", response_class=HTMLResponse)
def docs():
    return """
    <div style="font-family:sans-serif; max-width:800px; margin:50px auto; line-height:1.6;">
        <h1>API 文档</h1>
        <p>所有接口均需在 Header 中携带 <code>X-API-Key</code>。</p>
        <h3>1. 合成接口</h3>
        <code>POST /tts</code><br>
        <pre>{ "text": "...", "speaker": 3, "speedScale": 1.1 }</pre>
        <h3>2. 获取角色</h3>
        <code>GET /voices</code>
        <p>每个 Key 默认 50 次额度，消耗完请联系管理员。</p>
        <a href="/">返回首页</a>
    </div>
    """

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)