import os
import re
import json
import logging
import requests
import uuid
from datetime import datetime
from typing import Optional, List, Dict
from fastapi import FastAPI, HTTPException, Header, Depends, Request
from fastapi.responses import Response, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pypinyin import pinyin, Style
from sqlalchemy import Column, String, Integer, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# --- 汉化字典 ---
CN_NAME_MAP = {
    "四国めたん": "四国めたん (四国美谈)",
    "ずんだもん": "ずんだもん (俊达萌)",
    "春日部つむぎ": "春日部つむぎ (春日部紬)",
    "雨晴はう": "雨晴はう (雨晴羽)",
    "波音リツ": "波音リツ (波音律)",
    "玄野武宏": "玄野武宏",
    "白上虎太郎": "白上虎太郎",
    "青山龍星": "青山龙星",
    "冥鳴ひまり": "冥鸣向日葵",
    "九州そら": "九州空",
    "もち子さん": "饼子小姐",
    "剣崎雌雄": "剑崎雌雄",
    "WhiteCUL": "WhiteCUL",
    "後鬼": "后鬼",
    "No.7": "No.7",
    "ちび式じい": "智备爷爷",
    "櫻歌ミコ": "樱歌美子",
    "小夜/SAYO": "小夜/SAYO",
    "ナースロボ＿タイプＴ": "护士机器人Type-T",
    "†聖騎士 紅桜†": "†圣骑士 红樱†",
    "雀松朱司": "雀松朱司",
    "麒ヶ島宗麟": "麒岛宗麟",
    "春歌ナナ": "春歌七七",
    "猫使アル": "猫使阿露",
    "猫使ビィ": "猫使薇",
    "中国うさぎ": "中国兔",
    "栗田まろん": "栗田栗子",
    "あいえるたん": "IL-Tan",
    "满别花丸": "满别花丸",
    "琴詠ニア": "琴咏妮娅",
    "Voidoll": "Voidoll",
    "ぞん子": "僵尸子",
    "中部つるぎ": "中部剑"
}

CN_STYLE_MAP = {
    "ノーマル": "标准", "あまあま": "甜甜", "ツンツン": "傲娇", "セクシー": "性感",
    "ささやき": "低语", "ヒソヒソ": "悄悄话", "喜び": "喜悦", "悲しみ": "悲伤",
    "怒り": "愤怒", "のんびり": "悠哉", "熱血": "热血", "不機嫌": "不爽",
    "囁き": "私语", "たのしい": "快乐", "かなしい": "难过", "びえーん": "哭泣",
    "おこ": "生气", "びくびく": "害怕", "ヘロヘロ": "筋疲力尽", "なみだめ": "含泪",
    "ツンギレ": "暴走", "しっとり": "湿润", "ふつう": "普通", "わーい": "开心",
    "読み聞かせ": "讲故事", "アナウンス": "广播风", "第二形態": "第二形态",
    "ロリ": "萝莉", "楽々": "乐呵呵", "恐怖": "恐怖", "内緒话": "秘密话",
    "おちつき": "沉稳", "うきうき": "雀跃", "人見知り": "怕生", "おどろき": "惊讶",
    "こわがり": "胆小", "元気": "元气", "ぶりっ子": "装可爱", "ボーイ": "少年",
    "低血圧": "低血压", "覚醒": "觉醒", "実況風": "实况风", "おどおど": "战战兢兢"
}

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
ADMIN_KEY = "xingshuo_admin"

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_headers=["*"], allow_methods=["*"])

# --- 核心：伪日语转换逻辑 (包含 PINYIN_TO_KANA) ---
# (为了节省篇幅，这里使用了之前定义的 PINYIN_TO_KANA)
PINYIN_TO_KANA = {
    "a": "アー", "ai": "アイ", "an": "アン", "ang": "アン", "ao": "アオ",
    "ba": "バー", "bai": "バイ", "ban": "バン", "bang": "バン", "bao": "バオ", "bei": "ベイ", "ben": "ベン", "beng": "ベン", "bi": "ビー", "bian": "ビェン", "biao": "ビャ奥", "bie": "ビェ", "bin": "ビン", "bing": "ビン", "bo": "ボ", "bu": "ブー",
    "ca": "ツァ", "cai": "ツァイ", "can": "ツァン", "cang": "ツァン", "cao": "ツァオ", "ce": "ツァ", "cen": "ツェン", "ceng": "ツェン", "ci": "ツー", "cong": "ツォン", "cou": "ツォウ", "cu": "ツー", "cuan": "ツァン", "cui": "ツイ", "cun": "ツン", "cuo": "ツォ",
    "cha": "チャー", "chai": "チャイ", "chan": "チャン", "chang": "チャン", "chao": "チャオ", "che": "チャー", "chen": "チェン", "cheng": "チェン", "chi": "チー", "chong": "チョン", "chou": "チョウ", "chu": "チュー", "chua": "チュア", "chuai": "チュアイ", "chuan": "チュアン", "chuang": "チュアン", "chui": "チュイ", "chun": "チュン", "chuo": "チュオ",
    "da": "ダー", "dai": "ダイ", "dan": "ダン", "dang": "ダン", "dao": "ダオ", "de": "ダ", "dei": "デイ", "den": "デン", "deng": "デン", "di": "ディー", "dia": "ディア", "dian": "ディェン", "diao": "ディアオ", "die": "ディェ", "ding": "ディン", "diu": "ディウ", "dong": "ドン", "dou": "ドウ", "du": "ドゥー", "duan": "ドゥアン", "dui": "ドゥイ", "dun": "ドゥン", "duo": "ドゥオ",
    "e": "アー", "ei": "エイ", "en": "エン", "eng": "エン", "er": "アル",
    "fa": "ファー", "fan": "ファン", "fang": "ファン", "fei": "フェイ", "fen": "フェン", "feng": "フェン", "fo": "フォ", "fou": "フォウ", "fu": "フー",
    "ga": "ガー", "gai": "ガイ", "gan": "ガン", "gang": "ガン", "gao": "ガオ", "ge": "ガ", "gei": "ゲイ", "gen": "ゲン", "geng": "ゲン", "gong": "ゴン", "gou": "ゴウ", "gu": "グー", "gua": "グ亚", "guai": "グアイ", "guan": "グアン", "guang": "グアン", "gui": "グイ", "gun": "グン", "guo": "グオ",
    "ha": "ハー", "hai": "ハイ", "han": "ハン", "hang": "ハン", "hao": "ハオ", "he": "ハ", "hei": "ヘイ", "hen": "ヘン", "heng": "ヘン", "hong": "ホン", "hou": "ホウ", "hu": "フー", "hua": "ファ", "huai": "ファイ", "huan": "ファン", "huang": "ファン", "hui": "フェイ", "hun": "フン", "huo": "フォ",
    "ji": "ジー", "jia": "ジャ", "jian": "ジェン", "jiang": "ジャン", "jiao": "ジャオ", "jie": "ジェ", "jin": "ジン", "jing": "ジン", "jiong": "ジォン", "jiu": "ジウ", "ju": "ジュー", "juan": "ジュェン", "jue": "ジュェ", "jun": "ジュン",
    "ka": "カー", "kai": "カイ", "kan": "カン", "kang": "カン", "kao": "カオ", "ke": "カ", "kei": "ケイ", "ken": "ケン", "keng": "ケン", "kong": "コン", "kou": "コウ", "ku": "クー", "kua": "クア", "kuai": "クアイ", "kuan": "クアン", "kuang": "クアン", "kui": "クイ", "kun": "クン", "kuo": "クオ",
    "la": "ラー", "lai": "ライ", "lan": "ラン", "lang": "ラン", "lao": "ラオ", "le": "ラ", "lei": "レイ", "leng": "レン", "li": "リー", "lia": "リア", "lian": "リェン", "liang": "リャン", "liao": "リャオ", "lie": "リェ", "lin": "リン", "ling": "リン", "liu": "リウ", "long": "ロン", "lou": "ロウ", "lu": "ルー", "lv": "リュー", "luan": "ルアン", "lue": "ルェ", "lun": "ルン", "luo": "ルオ",
    "ma": "マー", "mai": "マイ", "man": "マン", "mang": "マン", "mao": "マオ", "me": "マ", "mei": "メイ", "men": "メン", "meng": "メン", "mi": "ミー", "mian": "ミェン", "miao": "ミャオ", "mie": "ミェ", "min": "ミン", "ming": "ミン", "miu": "ミウ", "mo": "モ", "mou": "モウ", "mu": "ムー",
    "na": "ナー", "nai": "ナイ", "nan": "ナン", "nang": "ナン", "nao": "ナオ", "ne": "ナ", "nei": "ネイ", "nen": "ネン", "neng": "ネン", "ni": "ニー", "nian": "ニェン", "niang": "ニャン", "niao": "ニャオ", "nie": "ニェ", "nin": "ニン", "ning": "ニン", "niu": "ニウ", "nong": "ノン", "nou": "ノウ", "nu": "ヌー", "nv": "ニュー", "nuan": "ヌアン", "nue": "ニュェ", "nuo": "ヌオ",
    "o": "オー", "ou": "オウ",
    "pa": "パー", "pai": "パイ", "pan": "パン", "pang": "パン", "pao": "パ奥", "pei": "ペイ", "pen": "ペン", "peng": "ペン", "pi": "ピー", "pian": "ピェン", "piao": "ピャオ", "pie": "ピェ", "pin": "ピン", "ping": "ピン", "po": "ポ", "pou": "ポウ", "pu": "プー",
    "qi": "チー", "qia": "チャ", "qian": "チェン", "qiang": "チャン", "qiao": "チャオ", "qie": "チェ", "qin": "チン", "qing": "チン", "qiong": "チョン", "qiu": "チウ", "qu": "チュー", "quan": "チュェン", "que": "チュェ", "qun": "チュン",
    "ran": "ラン", "rang": "ラン", "rao": "ラオ", "re": "ラ", "ren": "レン", "reng": "レン", "ri": "リー", "rong": "ロン", "rou": "ロウ", "ru": "ルー", "ruan": "ルアン", "rui": "ルイ", "run": "ルン", "ruo": "ルオ",
    "sa": "サー", "sai": "サイ", "san": "サン", "sang": "サン", "sao": "サオ", "se": "サ", "sen": "セン", "seng": "セン", "si": "スー", "song": "ソン", "sou": "ソウ", "su": "スー", "suan": "スアン", "sui": "スイ", "sun": "スン", "suo": "スオ",
    "sha": "シャー", "shai": "シャイ", "shan": "シャン", "shang": "シャン", "shao": "シャオ", "she": "シェ", "shei": "シェイ", "shen": "シェン", "sheng": "シェン", "shi": "シー", "shou": "ショウ", "shu": "シュー", "shua": "シュア", "shuai": "シュアイ", "shuan": "シュアン", "shuang": "シュアン", "shui": "シュイ", "shun": "シュン", "shuo": "シュオ",
    "ta": "ター", "tai": "タイ", "tan": "タン", "tang": "タン", "tao": "タオ", "te": "タ", "teng": "テン", "ti": "ティー", "tian": "ティェン", "tiao": "ティアオ", "tie": "ティェ", "ting": "ティン", "tong": "トン", "tou": "トウ", "tu": "トゥー", "tuan": "トゥアン", "tui": "トゥイ", "tun": "トゥン", "tuo": "トゥオ",
    "wa": "ワー", "wai": "ワイ", "wan": "ワン", "wang": "ワン", "wei": "ウェイ", "wen": "ウェン", "weng": "ウェン", "wo": "ウォ", "wu": "ウー",
    "xi": "シー", "xia": "シア", "xian": "シェン", "xiang": "シャン", "xiao": "シャオ", "xie": "シェ", "xin": "シン", "xing": "シン", "xiong": "ション", "xiu": "シウ", "xu": "シュー", "xuan": "シュェン", "xue": "シュェ", "xun": "シュン",
    "ya": "ヤー", "yan": "イェン", "yang": "ヤン", "yao": "ヤオ", "ye": "イェ", "yi": "イー", "yin": "イン", "ying": "イン", "yong": "ヨン", "you": "ヨウ", "yu": "ユー", "yuan": "ユェン", "yue": "ユェ", "yun": "ユン",
    "za": "ザー", "zai": "ザイ", "zan": "ザン", "zang": "ザン", "zao": "ザオ", "ze": "ザ", "zei": "ゼイ", "zen": "ゼン", "zeng": "ゼン", "zi": "ツー", "zong": "ゾン", "zou": "ゾウ", "zu": "ズー", "zuan": "ズアン", "zui": "ズイ", "zun": "ズン", "zuo": "ズオ",
    "zha": "ジャー", "zhai": "ジャイ", "zhan": "ジャン", "zhang": "ジャン", "zhao": "ジャオ", "zhe": "ジャ", "zhei": "ジェイ", "zhen": "ジェン", "zheng": "ジェン", "zhi": "ジー", "zhong": "ジョン", "zhou": "ジョウ", "zhu": "ジュー", "zhua": "ジュア", "zhuai": "ジュアイ", "zhuan": "ジュアン", "zhuang": "ジュアン", "zhui": "ジュイ", "zhun": "ジュン", "zhuo": "ジュオ"
}

class PseudoConverter:
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

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

# --- 接口模型 ---
class TTSRequest(BaseModel):
    text: str
    speaker: int
    mode: Optional[str] = "pseudo_jp"
    speedScale: Optional[float] = 1.1
    pitchScale: Optional[float] = 0.0
    intonationScale: Optional[float] = 1.0

# --- API ---

@app.get("/voices")
def get_voices():
    r = requests.get(f"{VOICEVOX_URL}/speakers").json()
    grouped = {}
    for char in r:
        raw_name = char["name"]
        display_name = CN_NAME_MAP.get(raw_name, raw_name)
        styles = []
        for s in char["styles"]:
            styles.append({
                "id": s["id"],
                "name": CN_STYLE_MAP.get(s["name"], s["name"])
            })
        grouped[raw_name] = {
            "name": display_name,
            "uuid": char["speaker_uuid"],
            "styles": styles
        }
    return list(grouped.values())

@app.get("/check_key")
def check_key(key: str, db: Session = Depends(get_db)):
    record = db.query(APIKeyRecord).filter(APIKeyRecord.key == key).first()
    if not record: raise HTTPException(status_code=404, detail="Key not found")
    return {"credits": record.credits}

@app.post("/tts")
def tts(req: TTSRequest, x_api_key: str = Header(...), db: Session = Depends(get_db)):
    record = db.query(APIKeyRecord).filter(APIKeyRecord.key == x_api_key).first()
    if not record or record.credits <= 0: raise HTTPException(status_code=401, detail="Invalid key or no credits")
    target_text = converter.convert(req.text) if req.mode == "pseudo_jp" else req.text
    q = requests.post(f"{VOICEVOX_URL}/audio_query", params={"text": target_text, "speaker": req.speaker}).json()
    q["speedScale"], q["pitchScale"], q["intonationScale"] = req.speedScale, req.pitchScale, req.intonationScale
    audio = requests.post(f"{VOICEVOX_URL}/synthesis", params={"speaker": req.speaker}, json=q).content
    record.credits -= 1
    db.commit()
    return Response(content=audio, media_type="audio/wav")

@app.get("/", response_class=HTMLResponse)
def index():
    return """
<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Voicevox 一步到位 API - 伪中国语合成站</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>
    <style>
        .character-card { transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); cursor: pointer; border-width: 2px; }
        .character-card:hover { transform: translateY(-4px); box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); }
        .character-card.active { border-color: #3b82f6; background-color: #f0f7ff; }
        .avatar-img { background: linear-gradient(135deg, #e0e7ff 0%, #ede9fe 100%); }
        [v-cloak] { display: none; }
    </style>
</head>
<body class="bg-slate-50 text-slate-900 font-sans">
    <div id="app" v-cloak class="max-w-6xl mx-auto px-4 py-8">
        <header class="flex flex-col md:flex-row justify-between items-center mb-12 gap-6">
            <div class="text-center md:text-left">
                <h1 class="text-4xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-600">Voicevox OneStep</h1>
                <p class="text-slate-500 mt-2 font-medium">中英日混读 · 拟音合成 · 伪中国语</p>
            </div>
            <div class="bg-white p-4 rounded-2xl shadow-sm border border-slate-200 flex items-center gap-4">
                <div class="relative">
                    <input v-model="apiKey" type="password" placeholder="输入 API Key" 
                           class="bg-slate-50 border-none rounded-lg px-4 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none w-48">
                </div>
                <button @click="checkKey" class="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-bold hover:bg-blue-700 transition-colors">查询额度</button>
                <div v-if="credits !== null" class="text-sm font-bold text-slate-700">余额: <span class="text-blue-600">{{ credits }}</span></div>
            </div>
        </header>

        <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
            <!-- 左侧角色面板 -->
            <section class="lg:col-span-8 bg-white rounded-3xl p-6 shadow-sm border border-slate-200">
                <div class="flex items-center justify-between mb-6">
                    <h2 class="text-xl font-bold flex items-center gap-2">
                        <span class="w-2 h-6 bg-blue-600 rounded-full"></span>
                        选择角色
                    </h2>
                    <span class="text-sm text-slate-400">已聚合 {{ characters.length }} 位角色</span>
                </div>
                
                <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4 overflow-y-auto max-h-[600px] pr-2 custom-scrollbar">
                    <div v-for="char in characters" :key="char.uuid"
                         @click="selectChar(char)"
                         :class="['character-card p-4 rounded-2xl text-center border-slate-100', selectedChar.uuid === char.uuid ? 'active' : 'bg-white']">
                        <div class="avatar-img w-16 h-16 rounded-2xl mx-auto mb-3 flex items-center justify-center text-blue-600 text-2xl font-black shadow-inner">
                            {{ char.name[0] }}
                        </div>
                        <div class="font-bold text-sm text-slate-800 mb-1">{{ char.name }}</div>
                        <div class="text-[10px] text-slate-400 bg-slate-50 py-1 px-2 rounded-full inline-block">{{ char.styles.length }} 种配置</div>
                    </div>
                </div>
            </section>

            <!-- 右侧配置面板 -->
            <section class="lg:col-span-4 space-y-6">
                <div class="bg-white rounded-3xl p-6 shadow-sm border border-slate-200">
                    <h2 class="text-xl font-bold mb-6">合成配置</h2>
                    
                    <div class="mb-6">
                        <label class="block text-sm font-bold text-slate-700 mb-3">当前音色</label>
                        <select v-model="selectedStyleId" class="w-full bg-slate-50 border-none rounded-xl px-4 py-3 text-sm font-medium focus:ring-2 focus:ring-blue-500">
                            <option v-for="s in selectedChar.styles" :key="s.id" :value="s.id">{{ s.name }}</option>
                        </select>
                    </div>

                    <div class="space-y-4 mb-8">
                        <div>
                            <div class="flex justify-between text-xs font-bold text-slate-400 mb-2">
                                <span>语速 (Speed)</span>
                                <span class="text-blue-600">{{ params.speed }}</span>
                            </div>
                            <input type="range" v-model="params.speed" min="0.5" max="1.5" step="0.1" class="w-full h-1.5 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-blue-600">
                        </div>
                        <div>
                            <div class="flex justify-between text-xs font-bold text-slate-400 mb-2">
                                <span>语调 (Intonation)</span>
                                <span class="text-blue-600">{{ params.intonation }}</span>
                            </div>
                            <input type="range" v-model="params.intonation" min="0" max="2" step="0.1" class="w-full h-1.5 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-blue-600">
                        </div>
                    </div>

                    <div class="bg-slate-50 rounded-2xl p-4 border border-dashed border-slate-200">
                        <p class="text-xs text-slate-400 leading-relaxed">
                            💡 <b>提示</b>：默认开启“伪中国语”转换，系统会自动将中文转为日式发音。如需调整，请联系管理员。
                        </p>
                    </div>
                </div>
            </section>

            <!-- 底部输入面板 -->
            <section class="lg:col-span-12">
                <div class="bg-white rounded-3xl p-8 shadow-sm border border-slate-200">
                    <textarea v-model="text" rows="3" placeholder="在这里输入文字..." 
                              class="w-full bg-slate-50 border-none rounded-2xl px-6 py-4 text-lg focus:ring-2 focus:ring-blue-500 outline-none mb-6"></textarea>
                    
                    <div class="flex flex-col md:flex-row items-center gap-6">
                        <button @click="synthesize" :disabled="loading || !selectedStyleId" 
                                class="w-full md:w-64 py-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-2xl font-bold text-lg shadow-lg shadow-blue-200 hover:scale-[1.02] active:scale-95 transition-all disabled:opacity-50 disabled:scale-100">
                            <span v-if="loading">合成中...</span>
                            <span v-else>立即合成语音</span>
                        </button>
                        
                        <div v-if="audioUrl" class="flex-1 w-full bg-slate-50 rounded-2xl p-3 flex items-center gap-4 animate-in fade-in slide-in-from-bottom-2">
                            <audio :src="audioUrl" id="player" controls class="flex-1 h-10"></audio>
                            <a :href="audioUrl" download="voice.wav" class="bg-white text-slate-700 px-6 py-2 rounded-xl font-bold text-sm shadow-sm hover:bg-slate-100 transition-colors">下载 WAV</a>
                        </div>
                    </div>
                </div>
            </section>
        </div>

        <footer class="mt-20 text-center text-slate-400 pb-10">
            <div class="flex justify-center gap-8 mb-4 text-sm font-medium">
                <a href="/docs" class="hover:text-blue-600 transition-colors">API 文档</a>
                <a href="#" class="hover:text-blue-600 transition-colors">购买额度</a>
                <a href="#" class="hover:text-blue-600 transition-colors">用户协议</a>
            </div>
            <p class="text-xs">&copy; 2026 Voicevox OneStep API Service. 为中文用户优化的拟音合成解决方案。</p>
        </footer>
    </div>

    <script>
        const { createApp, ref, onMounted, watch } = Vue;
        createApp({
            setup() {
                const characters = ref([]);
                const selectedChar = ref({ styles: [] });
                const selectedStyleId = ref(null);
                const text = ref("现在就算告诉我AI能操我也不稀奇。");
                const apiKey = ref(localStorage.getItem('vv_key') || "");
                const credits = ref(null);
                const audioUrl = ref(null);
                const loading = ref(false);
                const params = ref({ speed: 1.1, intonation: 1.2 });

                onMounted(async () => {
                    const res = await fetch('/voices');
                    characters.value = await res.json();
                    if (characters.value.length) selectChar(characters.value[0]);
                });

                const selectChar = (char) => {
                    selectedChar.value = char;
                    selectedStyleId.value = char.styles[0].id;
                };

                const checkKey = async () => {
                    if(!apiKey.value) return alert('请输入 API Key');
                    try {
                        const res = await fetch(`/check_key?key=${apiKey.value}`);
                        if(!res.ok) throw new Error();
                        const data = await res.json();
                        credits.value = data.credits;
                        localStorage.setItem('vv_key', apiKey.value);
                    } catch { alert('Key 错误或余额不足'); }
                };

                const synthesize = async () => {
                    if (!apiKey.value) return alert('请先输入 API Key');
                    loading.value = true;
                    try {
                        const res = await fetch('/tts', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json', 'X-API-Key': apiKey.value },
                            body: JSON.stringify({
                                text: text.value,
                                speaker: selectedStyleId.value,
                                speedScale: parseFloat(params.value.speed),
                                intonationScale: parseFloat(params.value.intonation)
                            })
                        });
                        if (!res.ok) {
                            const err = await res.json();
                            throw new Error(err.detail || '合成失败');
                        }
                        const blob = await res.blob();
                        if (audioUrl.value) URL.revokeObjectURL(audioUrl.value);
                        audioUrl.value = URL.createObjectURL(blob);
                        setTimeout(() => document.getElementById('player').play(), 100);
                        if(credits.value !== null) credits.value--;
                    } catch (e) { alert(e.message); }
                    finally { loading.value = false; }
                };

                return { characters, selectedChar, selectedStyleId, text, apiKey, credits, audioUrl, loading, params, checkKey, selectChar, synthesize };
            }
        }).mount('#app');
    </script>
</body>
</html>
    """

# (省略后续 /docs 接口等代码，保持与之前逻辑一致)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
