# -*- coding: utf-8 -*-
"""
车小智 · 后端 API 服务
====================================================
零第三方依赖，只用 Python 标准库（http.server / urllib / json / threading）。

启动：
    python server.py                 # 默认 http://127.0.0.1:8000
    python server.py --port 8080 --open

接口一览：
    GET  /                     页面（车小智.html）
    GET  /assets/...           静态资源
    GET  /api/health           健康检查 + 当前模式
    GET  /api/config           读取配置（api_key 打码）
    POST /api/config           保存配置（可在线填 API Key）
    GET  /api/knowledge        离线知识库覆盖范围
    POST /api/diagnose         故障诊断（结构化结果）
    POST /api/can-analyze      BD-CAN 总线参数判定
    POST /api/chat             智能对话（stream=true 走 SSE 流式）

双模说明：
    未配置 API Key  → 走内置离线诊断知识库（断网可用，比赛现场稳）
    已配置 API Key  → 走 OpenAI 兼容大模型接口，流式返回（并注入知识库做参考）
"""

import argparse
import json
import os
import sys
import time
import threading
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import knowledge as KB

# ------------------------------------------------------------------ 路径常量
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)                 # 车小智.html 所在目录
# 静态资源目录：优先用与页面同级的 assets/，这样页面里的相对路径
# （assets/cyber/xxx.svg）在 file:// 直开与 http:// 托管两种方式下都能命中
SITE_ASSETS_DIR = os.path.join(BASE_DIR, "assets")
LEGACY_ASSETS_DIR = os.path.join(SCRIPT_DIR, "assets")
ASSETS_DIR = SITE_ASSETS_DIR if os.path.isdir(SITE_ASSETS_DIR) else LEGACY_ASSETS_DIR
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.json")
PAGE_FILE = "车小智.html"

VERSION = "1.0.0"
SERVICE = "chexiaozhi-api"

DEFAULT_CONFIG = {
    "server": {"host": "127.0.0.1", "port": 8000},
    "llm": {
        "enabled": False,
        "base_url": "https://api.siliconflow.cn/v1",
        "api_key": "",
        "model": "deepseek-ai/DeepSeek-V3",
        "temperature": 0.6,
        "max_tokens": 1200,
        "timeout": 60,
    },
    "system_prompt": (
        "你是「车小智」，一名新能源汽车智能网联车诊断专家。"
        "面向车主与维修技师，用简洁、专业、可执行的中文回答。"
        "回答请遵循：1) 先给出最可能的故障判断和严重程度；"
        "2) 再给分步骤的排查流程（每条写清操作要点与判断标准）；"
        "3) 最后给维修/使用建议与安全提醒。"
        "涉及高压系统时必须提示由具备资质的人员操作。"
        "不要编造具体车型的零件编号；不确定时明确说明需要读取故障码确认。"
    ),
}

MIME = {
    ".html": "text/html; charset=utf-8",
    ".htm": "text/html; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".mjs": "application/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
    ".woff": "font/woff",
    ".woff2": "font/woff2",
    ".ttf": "font/ttf",
    ".mp4": "video/mp4",
    ".txt": "text/plain; charset=utf-8",
    ".md": "text/plain; charset=utf-8",
}

_config_lock = threading.Lock()


# ------------------------------------------------------------------ 配置读写
def load_config():
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))       # deep copy
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                user = json.load(f)
            for section, value in user.items():
                if isinstance(value, dict) and isinstance(cfg.get(section), dict):
                    cfg[section].update(value)
                else:
                    cfg[section] = value
        except Exception as exc:                        # 配置坏了也不能拦住服务
            print("  [警告] config.json 解析失败，使用默认配置：%s" % exc)
    # 环境变量可以覆盖 API Key（方便临时切换，不必改文件）
    env_key = os.environ.get("CHXZ_API_KEY")
    if env_key:
        cfg["llm"]["api_key"] = env_key
        cfg["llm"]["enabled"] = True
    return cfg


def save_config(cfg):
    with _config_lock:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)


def mask_key(key):
    if not key:
        return ""
    if len(key) <= 10:
        return key[:2] + "*" * max(len(key) - 2, 0)
    return key[:6] + "*" * 8 + key[-4:]


def key_looks_valid(key):
    """粗略但够用的 API Key 形状校验。

    ★为什么需要：原来 mode 只判 `enabled and bool(api_key)` —— **"有值"不等于"有效"**。
      实测踩过：api_key 被误填成一个 file:/// 预览地址，非空 → 页面显示「在线大模型」，
      但真调用时鉴权失败、静默退回本地知识库，对外宣称和实际行为不一致。
      这里挡掉明显不是 key 的东西（URL、路径、空格、过短）。
    """
    k = (key or "").strip()
    if len(k) < 16:
        return False
    if any(ch.isspace() for ch in k):
        return False
    low = k.lower()
    if low.startswith(("http://", "https://", "file://", "ftp://")):
        return False
    if (":" in k) or ("\\" in k) or ("/" in k):
        return False
    return True


def public_config(cfg):
    llm = cfg.get("llm", {})
    return {
        "server": cfg.get("server", {}),
        "llm": {
            "enabled": bool(llm.get("enabled")),
            "base_url": llm.get("base_url", ""),
            "model": llm.get("model", ""),
            "temperature": llm.get("temperature", 0.6),
            "max_tokens": llm.get("max_tokens", 1200),
            "timeout": llm.get("timeout", 60),
            "api_key_set": key_looks_valid(llm.get("api_key")),
            "api_key_masked": mask_key(llm.get("api_key", "")) if key_looks_valid(llm.get("api_key")) else "",
        },
        # ★必须用 key_looks_valid：只判"非空"会把误填的 URL/路径也算成已配置，
        #   导致页面宣称"在线大模型"而实际静默跑本地知识库。
        "mode": "llm" if (llm.get("enabled") and key_looks_valid(llm.get("api_key"))) else "local",
    }


# ------------------------------------------------------------------ 大模型调用
def llm_endpoint(base_url):
    base = (base_url or "").strip().rstrip("/")
    if not base:
        return ""
    if base.endswith("/chat/completions"):
        return base
    if base.endswith("/v1"):
        return base + "/chat/completions"
    return base + "/v1/chat/completions"


def build_llm_messages(cfg, message, history):
    entry, score = KB.match(message)
    ref = ""
    if score > 0:
        ref = (
            "\n\n【内置知识库参考（可采信，也可结合你的判断修正）】\n"
            "故障类型：%s\n严重程度：%s\n可能原因：%s\n建议步骤：%s"
            % (
                entry["faultType"],
                KB.severity_of(entry)["text"],
                entry["possibleCauses"],
                "；".join(s["title"] for s in entry["steps"]),
            )
        )
    messages = [{"role": "system", "content": cfg.get("system_prompt", "") + ref}]
    for item in (history or [])[-10:]:
        role = item.get("role")
        content = (item.get("content") or "").strip()
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": message})
    return messages, entry, score


def llm_stream(cfg, message, history):
    """向 OpenAI 兼容接口发起流式请求，逐段 yield 文本。"""
    llm = cfg["llm"]
    url = llm_endpoint(llm.get("base_url"))
    if not url:
        raise RuntimeError("未配置 base_url")
    messages, _, _ = build_llm_messages(cfg, message, history)
    payload = {
        "model": llm.get("model"),
        "messages": messages,
        "temperature": float(llm.get("temperature", 0.6)),
        "max_tokens": int(llm.get("max_tokens", 1200)),
        "stream": True,
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer %s" % llm.get("api_key", ""),
            "Accept": "text/event-stream",
        },
    )
    timeout = float(llm.get("timeout", 60))
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        for raw in resp:
            line = raw.decode("utf-8", "ignore").strip()
            if not line or not line.startswith("data:"):
                continue
            chunk = line[5:].strip()
            if chunk == "[DONE]":
                break
            try:
                obj = json.loads(chunk)
            except Exception:
                continue
            choices = obj.get("choices") or []
            if not choices:
                continue
            delta = choices[0].get("delta") or {}
            text = delta.get("content")
            if text:
                yield text


def llm_complete(cfg, message, history):
    """非流式调用，返回完整文本。"""
    llm = cfg["llm"]
    url = llm_endpoint(llm.get("base_url"))
    messages, _, _ = build_llm_messages(cfg, message, history)
    payload = {
        "model": llm.get("model"),
        "messages": messages,
        "temperature": float(llm.get("temperature", 0.6)),
        "max_tokens": int(llm.get("max_tokens", 1200)),
        "stream": False,
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer %s" % llm.get("api_key", ""),
        },
    )
    with urllib.request.urlopen(req, timeout=float(llm.get("timeout", 60))) as resp:
        obj = json.loads(resp.read().decode("utf-8", "ignore"))
    return (obj.get("choices") or [{}])[0].get("message", {}).get("content", "")


# ------------------------------------------------------------------ 离线对话引擎
GREETINGS = ["你好", "您好", "hi", "hello", "在吗", "嗨", "早上好", "下午好", "晚上好"]
CAPABILITY = ["你能做什么", "你是谁", "介绍一下", "什么功能", "会什么", "帮助", "怎么用"]
THANKS = ["谢谢", "多谢", "感谢", "3q", "thanks"]


def local_reply(message):
    """离线知识库回答，返回 (文本, 命中的知识条目, 得分)。"""
    text = (message or "").strip()
    low = text.lower()

    if any(g in low for g in GREETINGS) and len(text) <= 12:
        return (
            "你好，我是车小智 🔧 新能源汽车智能诊断助手。\n\n"
            "你可以直接把故障现象说给我，例如：\n"
            "· 车辆无法启动，仪表盘电池灯亮\n"
            "· 充电充不进去，换了充电桩也不行\n"
            "· 最近续航掉得特别快\n"
            "· 车机黑屏重启\n\n"
            "我会给出故障判断、分步排查流程和维修建议。\n"
            "也可以点下面的快捷提问直接体验。",
            None, 0,
        )

    if any(c in low for c in CAPABILITY) and len(text) <= 20:
        names = "、".join(e["faultType"] for e in KB.KNOWLEDGE)
        return (
            "我是「车小智」，专注新能源智能网联车的故障诊断。\n\n"
            "目前内置 %d 类故障的完整诊断流程：\n%s\n\n"
            "直接把现象描述给我即可；如果描述里包含故障码（如 P0AFA、U0111），"
            "我会按故障码思路带你排查。\n"
            "另外我还能做 BD-CAN 总线参数判定（电阻 / CAN_H / CAN_L 电压）。"
            % (len(KB.KNOWLEDGE), names),
            None, 0,
        )

    if any(t in low for t in THANKS) and len(text) <= 10:
        return "不客气，路上注意安全 🚗 还有其他异常随时问我。", None, 0

    entry, score = KB.match(text)
    if score == 0:
        names = "、".join(e["faultType"] for e in KB.KNOWLEDGE[:8])
        body = KB.FALLBACK
        lines = [
            "我暂时没能从描述里锁定具体故障类型，建议按下面的通用流程排查：", "",
            "【故障判断】%s" % body["faultType"],
            "【可能原因】%s" % body["possibleCauses"], "",
            "【建议排查步骤】",
        ]
        for i, s in enumerate(body["steps"], 1):
            lines.append("%d. %s —— %s" % (i, s["title"], s["description"]))
            lines.append("   操作要点：%s" % s["keyPoints"])
        lines += ["", "【维修与使用建议】"]
        lines += ["- %s" % s for s in body["suggestions"]]
        lines += [
            "",
            "补充一句：把「什么时候出现、什么工况下出现、仪表盘亮什么灯」说清楚，"
            "我能给出更准的判断。",
            "目前覆盖的典型故障：%s。" % names,
        ]
        return "\n".join(lines), body, 0

    sev = KB.severity_of(entry)
    lines = [
        "【故障判断】%s" % entry["faultType"],
        "【严重程度】%s" % sev["text"],
        "【涉及系统】%s" % "、".join(entry.get("systems", [])),
        "【可能原因】%s" % entry["possibleCauses"],
        "",
        "【建议排查步骤】",
    ]
    for i, s in enumerate(entry["steps"], 1):
        lines.append("%d. %s —— %s" % (i, s["title"], s["description"]))
        lines.append("   操作要点：%s" % s["keyPoints"])
    lines += ["", "【维修与使用建议】"]
    lines += ["- %s" % s for s in entry["suggestions"]]
    if sev["level"] == "high":
        lines += ["", "⚠️ 该故障涉及安全，建议低速行驶并尽快进站，不要自行拆解高压部件。"]
    lines += ["", "（当前为离线知识库作答；在「设置」里填入大模型 API Key 可切换为在线 AI 深度分析。）"]
    return "\n".join(lines), entry, score


def chunk_text(text, size=14):
    for i in range(0, len(text), size):
        yield text[i:i + size]


# ------------------------------------------------------------------ BD-CAN 判定
def can_analyze(resistance, can_h, can_l):
    items = []

    def add(name, value, unit, low, high, note_bad):
        ok = low <= value <= high
        items.append({
            "name": name,
            "value": value,
            "unit": unit,
            "normal": "%s ~ %s%s" % (low, high, unit),
            "ok": ok,
            "note": ("在正常范围内" if ok else note_bad),
        })
        return ok

    ok1 = add("终端电阻", resistance, "Ω", 50, 70,
              "不在正常范围内（50-70Ω），可能存在线路短路、断路或终端电阻缺失")
    ok2 = add("CAN_H 电压", can_h, "V", 2.5, 4.5,
              "不在正常范围内（2.5-4.5V），可能存在信号异常或隐性/显性电平失配")
    ok3 = add("CAN_L 电压", can_l, "V", 0.5, 2.5,
              "不在正常范围内（0.5-2.5V），可能存在信号异常或总线对地短路")
    diff = abs(can_h - can_l)
    ok4 = add("CAN_H/CAN_L 压差", round(diff, 2), "V", 1.5, 3.5,
              "不在正常范围内（1.5-3.5V），可能存在通信故障或共模干扰")

    all_ok = all([ok1, ok2, ok3, ok4])
    if all_ok:
        conclusion = "BD-CAN 网络通信状态正常"
        advice = [
            "各项参数均在标准范围内，总线物理层无明显异常",
            "若仍存在偶发掉线，建议用示波器观察差分波形与终端匹配",
            "可继续排查节点软件层：网关、控制器休眠策略与故障码",
        ]
    else:
        conclusion = "BD-CAN 网络存在异常，建议按异常项逐条排查"
        advice = [
            "先测量终端电阻：标准约 60Ω（两个 120Ω 终端并联），偏离说明终端缺失或线束开路",
            "CAN_H / CAN_L 同时接近 0V 或 5V，多为总线对地/对电源短路",
            "压差异常但单线电压正常，常见于共模干扰或线束阻抗不匹配",
            "检查最近维修动过的线束与接插件，氧化与虚接是间歇性故障主因",
            "确认线束是否被随意破线取电或加装设备",
        ]

    return {
        "items": items,
        "allOk": all_ok,
        "conclusion": conclusion,
        "advice": advice,
    }


# ------------------------------------------------------------------ HTTP 处理
class Handler(BaseHTTPRequestHandler):
    server_version = "CheXiaoZhi/" + VERSION
    protocol_version = "HTTP/1.0"

    # ---------- 基础工具 ----------
    def log_message(self, fmt, *args):
        sys.stdout.write("  %s  %s\n" % (time.strftime("%H:%M:%S"), fmt % args))

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")

    def send_json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def read_json(self):
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        for enc in ("utf-8", "gbk"):
            try:
                return json.loads(raw.decode(enc))
            except Exception:
                continue
        return {}

    # ---------- SSE ----------
    def sse_start(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache, no-transform")
        self.send_header("Connection", "close")
        self.send_header("X-Accel-Buffering", "no")
        self._cors()
        self.end_headers()
        self.close_connection = True
        self.wfile.write(b": chexiaozhi stream open\n\n")
        self.wfile.flush()

    def sse_send(self, obj):
        payload = ("data: " + json.dumps(obj, ensure_ascii=False) + "\n\n").encode("utf-8")
        self.wfile.write(payload)
        self.wfile.flush()

    # ---------- 路由 ----------
    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0]
        if path.startswith("/api/"):
            return self.handle_api_get(path)
        return self.serve_static(path)

    def do_POST(self):
        path = self.path.split("?")[0]
        return self.handle_api_post(path)

    # ---------- 静态文件 ----------
    def serve_static(self, path):
        if path in ("/", "/index.html", "/" + PAGE_FILE):
            target = os.path.join(BASE_DIR, PAGE_FILE)
        elif path.startswith("/assets/"):
            rel = path[len("/assets/"):]
            target = os.path.normpath(os.path.join(ASSETS_DIR, rel))
            if not target.startswith(ASSETS_DIR):
                return self.send_json({"ok": False, "error": "非法路径"}, 403)
        elif path == "/favicon.ico":
            target = os.path.join(ASSETS_DIR, "cyber", "favicon.svg")
        elif path == "/favicon.svg":
            target = os.path.join(ASSETS_DIR, "cyber", "favicon.svg")
        else:
            return self.send_json({"ok": False, "error": "未找到：%s" % path}, 404)

        if not os.path.isfile(target):
            return self.send_json(
                {"ok": False,
                 "error": "文件不存在：%s" % target,
                 "hint": "确认 车小智.html 与本服务目录处于同一父目录"},
                404,
            )
        ext = os.path.splitext(target)[1].lower()
        ctype = MIME.get(ext, "application/octet-stream")
        with open(target, "rb") as f:
            body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    # ---------- GET API ----------
    def handle_api_get(self, path):
        cfg = load_config()
        if path == "/api/health":
            pub = public_config(cfg)
            return self.send_json({
                "ok": True,
                "service": SERVICE,
                "version": VERSION,
                "mode": pub["mode"],
                "modeText": "在线大模型" if pub["mode"] == "llm" else "离线知识库",
                "model": pub["llm"]["model"] if pub["mode"] == "llm" else None,
                "knowledgeCount": len(KB.KNOWLEDGE),
                "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            })
        if path == "/api/config":
            return self.send_json({"ok": True, "config": public_config(cfg)})
        if path == "/api/knowledge":
            return self.send_json({
                "ok": True,
                "count": len(KB.KNOWLEDGE),
                "items": KB.brief_list(),
            })
        return self.send_json({"ok": False, "error": "未知接口：%s" % path}, 404)

    # ---------- POST API ----------
    def handle_api_post(self, path):
        if path == "/api/config":
            return self.api_config()
        if path == "/api/diagnose":
            return self.api_diagnose()
        if path == "/api/can-analyze":
            return self.api_can_analyze()
        if path == "/api/chat":
            return self.api_chat()
        return self.send_json({"ok": False, "error": "未知接口：%s" % path}, 404)

    def api_config(self):
        body = self.read_json()
        cfg = load_config()
        llm = cfg.setdefault("llm", {})
        for key in ("base_url", "model"):
            if isinstance(body.get(key), str) and body[key].strip():
                llm[key] = body[key].strip()
        if isinstance(body.get("api_key"), str) and body["api_key"].strip():
            llm["api_key"] = body["api_key"].strip()
        if body.get("clear_key"):
            llm["api_key"] = ""
        if "enabled" in body:
            llm["enabled"] = bool(body["enabled"])
        for key in ("temperature", "max_tokens", "timeout"):
            if body.get(key) not in (None, ""):
                try:
                    llm[key] = float(body[key]) if key != "max_tokens" else int(body[key])
                except (TypeError, ValueError):
                    pass
        if isinstance(body.get("system_prompt"), str) and body["system_prompt"].strip():
            cfg["system_prompt"] = body["system_prompt"].strip()
        save_config(cfg)
        return self.send_json({"ok": True, "config": public_config(cfg)})

    def api_diagnose(self):
        body = self.read_json()
        desc = (body.get("description") or "").strip()
        if not desc:
            return self.send_json({"ok": False, "error": "请填写故障描述"}, 400)
        entry, score = KB.match(desc)
        result = KB.to_diagnosis(entry, score, matched=score > 0)
        result["ok"] = True
        result["source"] = "knowledge-base"
        result["input"] = desc
        vehicle = body.get("vehicle") or {}
        if any(vehicle.values()):
            result["vehicle"] = vehicle
        return self.send_json(result)

    def api_can_analyze(self):
        body = self.read_json()
        try:
            resistance = float(body.get("resistance"))
            can_h = float(body.get("can_h"))
            can_l = float(body.get("can_l"))
        except (TypeError, ValueError):
            return self.send_json({"ok": False, "error": "请填写有效的电阻与电压数值"}, 400)
        if not (0 <= resistance <= 1000) or not (0 <= can_h <= 20) or not (0 <= can_l <= 20):
            return self.send_json({"ok": False, "error": "数值超出合理量程，请检查输入"}, 400)
        out = can_analyze(resistance, can_h, can_l)
        out["ok"] = True
        out["source"] = "knowledge-base"
        return self.send_json(out)

    def api_chat(self):
        body = self.read_json()
        message = (body.get("message") or "").strip()
        history = body.get("history") or []
        stream = bool(body.get("stream"))
        if not message:
            return self.send_json({"ok": False, "error": "消息不能为空"}, 400)

        cfg = load_config()
        llm = cfg.get("llm", {})
        # 同样要用 key_looks_valid：只判非空的话，误填的 URL/路径也会让它去发一次
        # 注定 401 的请求，白等一个超时再退回本地知识库。
        use_llm = bool(llm.get("enabled") and key_looks_valid(llm.get("api_key")))

        if stream:
            return self.chat_stream(message, history, cfg, use_llm)

        # ---- 非流式 ----
        started = time.time()
        if use_llm:
            try:
                reply = llm_complete(cfg, message, history)
                return self.send_json({
                    "ok": True, "reply": reply, "mode": "llm",
                    "model": llm.get("model"), "elapsed": round(time.time() - started, 2),
                })
            except Exception as exc:
                reply, entry, score = local_reply(message)
                return self.send_json({
                    "ok": True, "reply": reply, "mode": "local",
                    "fallback": True,
                    "fallbackReason": "大模型调用失败：%s" % exc,
                    "matched": entry["faultType"] if entry else None,
                    "elapsed": round(time.time() - started, 2),
                })
        reply, entry, score = local_reply(message)
        return self.send_json({
            "ok": True, "reply": reply, "mode": "local",
            "matched": entry["faultType"] if entry else None,
            "score": score, "elapsed": round(time.time() - started, 2),
        })

    def chat_stream(self, message, history, cfg, use_llm):
        llm = cfg.get("llm", {})
        self.sse_start()
        started = time.time()
        try:
            if use_llm:
                self.sse_send({"type": "meta", "mode": "llm", "model": llm.get("model")})
                try:
                    got = False
                    for piece in llm_stream(cfg, message, history):
                        got = True
                        self.sse_send({"type": "delta", "text": piece})
                    if not got:
                        raise RuntimeError("大模型返回空内容")
                    self.sse_send({"type": "done", "mode": "llm",
                                   "elapsed": round(time.time() - started, 2)})
                    return
                except Exception as exc:
                    self.sse_send({"type": "notice",
                                   "message": "在线大模型调用失败，已切换到离线知识库：%s" % exc})
                    self.sse_send({"type": "meta", "mode": "local", "model": None})

            text, entry, score = local_reply(message)
            if not use_llm:
                self.sse_send({"type": "meta", "mode": "local", "model": None})
            for piece in chunk_text(text):
                self.sse_send({"type": "delta", "text": piece})
                time.sleep(0.02)                       # 打字机节奏
            self.sse_send({
                "type": "done",
                "mode": "local",
                "matched": entry["faultType"] if entry else None,
                "elapsed": round(time.time() - started, 2),
            })
        except (BrokenPipeError, ConnectionResetError):
            pass                                        # 用户关掉页面，正常结束
        except Exception as exc:
            try:
                self.sse_send({"type": "error", "message": str(exc)})
            except Exception:
                pass


# ------------------------------------------------------------------ 入口
def probe_existing(host, port):
    """探测该端口上是否已经跑着一个车小智服务；是则返回它的 /api/health。"""
    try:
        req = urllib.request.Request("http://%s:%d/api/health" % (host, port))
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            obj = json.loads(resp.read().decode("utf-8", "ignore"))
        return obj if obj.get("service") == SERVICE else None
    except Exception:
        return None


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    cfg = load_config()
    ap = argparse.ArgumentParser(description="车小智后端 API 服务")
    ap.add_argument("--host", default=cfg["server"].get("host", "127.0.0.1"))
    ap.add_argument("--port", type=int, default=int(cfg["server"].get("port", 8000)))
    ap.add_argument("--open", action="store_true", help="启动后自动打开浏览器")
    args = ap.parse_args()

    if not os.path.isfile(os.path.join(BASE_DIR, PAGE_FILE)):
        print("  [警告] 未找到页面文件：%s" % os.path.join(BASE_DIR, PAGE_FILE))

    probe_host = "127.0.0.1" if args.host in ("0.0.0.0", "") else args.host

    # 已经有一个车小智服务在跑？直接复用，避免同端口多实例（Windows 下 SO_REUSEADDR
    # 会允许重复绑定，导致请求被随机路由到旧实例，出现「代码改了却不生效」的怪现象）
    running = probe_existing(probe_host, args.port)
    if running:
        print("=" * 60)
        print("  车小智 · 后端 API 服务已经在运行")
        print("=" * 60)
        print("  页面地址 : http://%s:%d/" % (probe_host, args.port))
        print("  运行模式 : %s" % running.get("modeText", "-"))
        print("  如需另起一个实例，请指定其它端口：python server.py --port 8010")
        print("=" * 60)
        return

    # 端口被别的程序占用时自动顺延，避免用户看到一堆 traceback
    httpd = None
    actual_port = args.port
    for offset in range(0, 11):
        candidate = args.port + offset
        try:
            httpd = ThreadingHTTPServer((args.host, candidate), Handler)
            actual_port = candidate
            if offset:
                print("  [提示] 端口 %d 被占用，已自动改用 %d" % (args.port, candidate))
            break
        except OSError:
            continue
    if httpd is None:
        print("  [错误] 端口 %d-%d 均被占用，请用 --port 指定其它端口。" % (args.port, args.port + 10))
        sys.exit(1)

    httpd.daemon_threads = True
    pub = public_config(cfg)
    url = "http://%s:%d/" % (probe_host, actual_port)

    print("=" * 60)
    print("  车小智 · 后端 API 服务  v%s" % VERSION)
    print("=" * 60)
    print("  页面地址 : %s" % url)
    print("  健康检查 : %sapi/health" % url)
    print("  运行模式 : %s%s" % (
        "在线大模型（%s）" % pub["llm"]["model"] if pub["mode"] == "llm" else "离线诊断知识库",
        "" if pub["mode"] == "llm" else "  —— 在页面「设置」里填 API Key 可切换在线模式",
    ))
    print("  知识库   : 内置 %d 类故障诊断流程" % len(KB.KNOWLEDGE))
    print("  配置文件 : %s" % CONFIG_PATH)
    print("  按 Ctrl+C 停止服务")
    print("=" * 60)

    if args.open:
        threading.Timer(1.0, lambda: __import__("webbrowser").open(url)).start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n  服务已停止。")
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()
