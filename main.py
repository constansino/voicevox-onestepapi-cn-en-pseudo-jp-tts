import os
import re
import json
import logging
import requests
from typing import Optional, List, Dict
from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pypinyin import pinyin, Style

# --- 配置 ---
VOICEVOX_URL = os.getenv("VOICEVOX_BASE_URL", "http://127.0.0.1:800").rstrip("/")
HOST = "0.0.0.0"
PORT = 8000

# 日志配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VoicevoxAdapter")

app = FastAPI(title="Voicevox Pseudo-JP Adapter")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 全量拼音 -> 片假名 映射表 (伪中国语调校版) ---
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
    "ma": "マー", "mai": "マイ", "man": "マン", "mang": "マン", "mao": "マオ", "me": "マ", "mei": "メイ", "men": "メン", "meng": "メン", "mi": "ミー", "mian": "ミェン", "miao": "ミャオ", "mie": "ミェ", "min": "ミン", "ming": "ミン", "miu": "ミウ", "mo": "モ", "mou": "モウ", "mu": "ムー",
    "na": "ナー", "nai": "ナイ", "nan": "ナン", "nang": "ナン", "nao": "ナオ", "ne": "ナ", "nei": "ネイ", "nen": "ネン", "neng": "ネン", "ni": "ニー", "nian": "ニェン", "niang": "ニャン", "niao": "ニャオ", "nie": "ニェ", "nin": "ニン", "ning": "ニン", "niu": "ニウ", "nong": "ノン", "nou": "ノウ", "nu": "ヌー", "nv": "ニュー", "nuan": "ヌアン", "nue": "ニュェ", "nuo": "ヌオ",
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
    "zha": "ジャー", "zhai": "ジャイ", "zhan": "ジャン", "zhang": "ジャン", "zhao": "ジャオ", "zhe": "ジャ", "zhei": "ジェイ", "zhen": "ジェン", "zheng": "ジェン", "zhi": "ジー", "zhong": "ジョン", "zhou": "ジョウ", "zhu": "ジュー", "zhua": "ジュア", "zhuai": "ジュアイ", "zhuan": "ジュアン", "zhuang": "ジュアン", "zhui": "ジュイ", "zhun": "ジュン", "zhuo": "ジュオ"
}

class PseudoConverter:
    def __init__(self, dict_path="/root/voicevox-adapter/custom_dict.json"):
        self.dict_path = dict_path
        self.custom_dict = {}
        
    def _load_dict(self):
        if os.path.exists(self.dict_path):
            try:
                with open(self.dict_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load dictionary: {e}")
        return {}

    def is_chinese(self, char):
        return '\u4e00' <= char <= '\u9fff'

    def process_chinese(self, text):
        # 1. 转拼音 (无声调)
        py_list = pinyin(text, style=Style.NORMAL, errors='default')
        result = []
        for py in py_list:
            s = py[0].lower().replace("ü", "v")
            # 2. 查表替换为片假名
            kana = PINYIN_TO_KANA.get(s, s) 
            # 3. 容错：如果找不到，比如 'ng' 这种残留，尝试首字母大写再找
            if kana == s:
                kana = PINYIN_TO_KANA.get(s.lower(), s)
            result.append(kana)
        return "".join(result)

    def process_english(self, text):
        text = text.lower()
        replacements = [
            ("th", "s"), ("ph", "f"), ("v", "b"), ("l", "r"),
            ("tion", "shon"), ("si", "shi"), ("tu", "chu"), ("ti", "chi")
        ]
        for old, new in replacements:
            text = text.replace(old, new)
        
        if text[-1] not in "aeiou":
            if text[-1] in "td":
                text += "o"
            else:
                text += "u"
        return text

    def convert(self, text):
        self.custom_dict = self._load_dict()
        for k, v in self.custom_dict.items():
            pattern = re.compile(re.escape(k), re.IGNORECASE)
            text = pattern.sub(v, text)

        tokens = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z0-9]+|[^a-zA-Z0-9\u4e00-\u9fff]+', text)
        converted_parts = []
        for token in tokens:
            if not token.strip():
                converted_parts.append(token)
                continue
            
            if self.is_chinese(token[0]):
                converted_parts.append(self.process_chinese(token))
            elif re.match(r'[a-zA-Z]+', token):
                converted_parts.append(self.process_english(token))
            else:
                converted_parts.append(token)
                
        return "".join(converted_parts)

converter = PseudoConverter()

class TTSRequest(BaseModel):
    text: str
    speaker: int
    mode: Optional[str] = "pseudo_jp"
    speedScale: Optional[float] = None
    pitchScale: Optional[float] = None
    intonationScale: Optional[float] = None
    volumeScale: Optional[float] = None
    prePhonemeLength: Optional[float] = None
    postPhonemeLength: Optional[float] = None

@app.get("/voices")
def get_voices():
    try:
        r = requests.get(f"{VOICEVOX_URL}/speakers")
        r.raise_for_status()
        return [
            {"speaker_id": s["id"], "speaker_name": c["name"], "style_name": s["name"]} 
            for c in r.json() for s in c.get("styles", [])
        ]
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"VOICEVOX error: {str(e)}")

@app.post("/tts")
def text_to_speech(req: TTSRequest):
    target_text = req.text
    if req.mode == "pseudo_jp":
        target_text = converter.convert(req.text)
        logger.info(f"Convert: {req.text} -> {target_text}")

    try:
        r_query = requests.post(
            f"{VOICEVOX_URL}/audio_query", 
            params={"text": target_text, "speaker": req.speaker}
        )
        if r_query.status_code != 200:
            raise HTTPException(status_code=400, detail=f"Query failed: {r_query.text}")

        query_data = r_query.json()
        
        for k in ["speedScale", "pitchScale", "intonationScale", "volumeScale", "prePhonemeLength", "postPhonemeLength"]:
            if getattr(req, k) is not None:
                query_data[k] = getattr(req, k)

        r_synth = requests.post(
            f"{VOICEVOX_URL}/synthesis",
            params={"speaker": req.speaker},
            json=query_data,
            headers={"Content-Type": "application/json"}
        )
        if r_synth.status_code != 200:
            raise HTTPException(status_code=500, detail="Synthesis failed")

        return Response(content=r_synth.content, media_type="audio/wav")

    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
