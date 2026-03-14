import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
import requests
import urllib3
import time
import os
import glob
import json
from datetime import datetime

# LCU SSL 경고 무시 (자체 서명 인증서)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ──────────────────────────────────────────────
#  상수
# ──────────────────────────────────────────────
REGIONS = {
    "한국 (KR)":         ("kr",   "asia"),
    "북미 (NA1)":        ("na1",  "americas"),
    "유럽 서버 (EUW1)":  ("euw1", "europe"),
    "유럽 북동 (EUNE1)": ("eun1", "europe"),
    "오세아니아 (OC1)":  ("oc1",  "sea"),
    "일본 (JP1)":        ("jp1",  "asia"),
    "브라질 (BR1)":      ("br1",  "americas"),
    "라틴 북 (LA1)":     ("la1",  "americas"),
    "라틴 남 (LA2)":     ("la2",  "americas"),
}
TIERS = ["Challenger", "Grandmaster", "Master"]
QUEUE = "RANKED_SOLO_5x5"
MAP_SIZE = 14820
PENTA_WINDOW_MS = 10_000

# 펜타킬 점프 시 몇 초 앞에서 시작할지 (예고 구간)
REPLAY_PRE_ROLL_SEC = 10

GOLD   = "#C8AA6E"
GOLD_D = "#785A28"
BLUE   = "#0BC4E3"
DARK   = "#0A1428"
PANEL  = "#13243A"
PANEL2 = "#0E1F35"
TEXT   = "#A9B4C8"
WHITE  = "#E8E0D0"
RED    = "#C8393B"
GREEN  = "#00B48A"
ORANGE = "#E8A44A"
PURPLE = "#9B59B6"
CYAN   = "#00CED1"

# ──────────────────────────────────────────────
#  카메라 프리셋 정의
# ──────────────────────────────────────────────
# 각 프리셋은 펜타킬 타임스탬프(t=0) 기준 상대 시간(offset_s)에
# 적용할 render 파라미터 딕셔너리의 리스트
CAMERA_PRESETS = {
    "🎯 드라마틱 줌인": {
        "desc": "펜타킬 직전 챔피언에 포커스, 점점 줌인 후 확정 순간 슬로우",
        "keyframes": [
            {"offset_s": -10.0, "render": {"cameraMode": "top",    "fieldOfView": 80,  "interfaceAll": False, "interfaceScore": False}, "speed": 1.0},
            {"offset_s":  -5.0, "render": {"cameraMode": "focus",  "fieldOfView": 65}, "speed": 1.0},
            {"offset_s":  -2.0, "render": {"cameraMode": "focus",  "fieldOfView": 45}, "speed": 1.0},
            {"offset_s":   0.0, "render": {"cameraMode": "focus",  "fieldOfView": 35,  "depthOfField": True}, "speed": 0.5},
            {"offset_s":   3.0, "render": {"cameraMode": "focus",  "fieldOfView": 55,  "depthOfField": False}, "speed": 1.0},
            {"offset_s":   6.0, "render": {"cameraMode": "top",    "fieldOfView": 80}, "speed": 1.0},
        ]
    },
    "🎮 1인칭 추격": {
        "desc": "챔피언 시점으로 킬 5개를 따라감. 몰입감 극대화",
        "keyframes": [
            {"offset_s": -10.0, "render": {"cameraMode": "fps",    "fieldOfView": 90,  "interfaceAll": False, "interfaceScore": False}, "speed": 1.0},
            {"offset_s":   0.0, "render": {"cameraMode": "fps",    "fieldOfView": 90}, "speed": 0.5},
            {"offset_s":   4.0, "render": {"cameraMode": "fps",    "fieldOfView": 90}, "speed": 1.0},
        ]
    },
    "🌐 탑다운 전체": {
        "desc": "위에서 내려다보며 킬 동선을 모두 보여줌",
        "keyframes": [
            {"offset_s": -10.0, "render": {"cameraMode": "top",    "fieldOfView": 90,  "interfaceAll": False, "interfaceScore": False}, "speed": 1.0},
            {"offset_s":   0.0, "render": {"cameraMode": "top",    "fieldOfView": 90}, "speed": 0.75},
            {"offset_s":   5.0, "render": {"cameraMode": "top",    "fieldOfView": 90}, "speed": 1.0},
        ]
    },
    "🎬 시네마틱": {
        "desc": "UI 전부 숨기고 thirdPerson 뷰, 펜타킬 순간 극적인 슬로우",
        "keyframes": [
            {"offset_s": -10.0, "render": {"cameraMode": "thirdPerson", "fieldOfView": 75, "interfaceAll": False, "interfaceScore": False, "interfaceFrames": False, "depthOfField": True}, "speed": 1.0},
            {"offset_s":  -3.0, "render": {"cameraMode": "thirdPerson", "fieldOfView": 60}, "speed": 0.5},
            {"offset_s":   0.0, "render": {"cameraMode": "thirdPerson", "fieldOfView": 50}, "speed": 0.25},
            {"offset_s":   2.5, "render": {"cameraMode": "thirdPerson", "fieldOfView": 70}, "speed": 1.0},
            {"offset_s":   6.0, "render": {"cameraMode": "top",         "fieldOfView": 85, "depthOfField": False}, "speed": 1.0},
        ]
    },
    "⚡ 쾌속 하이라이트": {
        "desc": "1~4킬은 2배속으로 빠르게, 펜타킬 순간만 슬로우모션",
        "keyframes": [
            {"offset_s": -10.0, "render": {"cameraMode": "focus",  "fieldOfView": 70,  "interfaceAll": False, "interfaceScore": False}, "speed": 2.0},
            {"offset_s":  -1.0, "render": {"cameraMode": "focus",  "fieldOfView": 55}, "speed": 1.0},
            {"offset_s":   0.0, "render": {"cameraMode": "focus",  "fieldOfView": 40,  "depthOfField": True},  "speed": 0.25},
            {"offset_s":   3.0, "render": {"cameraMode": "focus",  "fieldOfView": 70,  "depthOfField": False}, "speed": 1.0},
        ]
    },
    # ── 쇼츠 전용 프리셋 ──────────────────────────────────────────
    "📱 쇼츠 — 클로즈업 포커스": {
        "desc": "[9:16 최적화] 좁은 FOV로 챔피언 중앙 고정. 크롭 후 인물이 꽉 찬 구도",
        "shorts": True,
        "keyframes": [
            {"offset_s": -12.0, "render": {"cameraMode": "focus",  "fieldOfView": 45, "interfaceAll": False, "interfaceScore": False, "interfaceFrames": False, "depthOfField": False}, "speed": 1.0},
            {"offset_s":  -5.0, "render": {"cameraMode": "focus",  "fieldOfView": 38}, "speed": 1.0},
            {"offset_s":  -1.0, "render": {"cameraMode": "focus",  "fieldOfView": 32, "depthOfField": True},  "speed": 0.5},
            {"offset_s":   0.0, "render": {"cameraMode": "focus",  "fieldOfView": 28, "depthOfField": True},  "speed": 0.25},
            {"offset_s":   2.0, "render": {"cameraMode": "focus",  "fieldOfView": 38, "depthOfField": False}, "speed": 1.0},
            {"offset_s":   5.0, "render": {"cameraMode": "focus",  "fieldOfView": 45}, "speed": 1.0},
        ]
    },
    "📱 쇼츠 — 탑뷰 세로 동선": {
        "desc": "[9:16 최적화] 탑다운으로 세로 크롭시 킬 동선이 위아래로 자연스럽게 배치",
        "shorts": True,
        "keyframes": [
            {"offset_s": -12.0, "render": {"cameraMode": "top", "fieldOfView": 55, "interfaceAll": False, "interfaceScore": False, "interfaceFrames": False}, "speed": 1.0},
            {"offset_s":   0.0, "render": {"cameraMode": "top", "fieldOfView": 45, "depthOfField": True},  "speed": 0.5},
            {"offset_s":   3.0, "render": {"cameraMode": "top", "fieldOfView": 55, "depthOfField": False}, "speed": 1.0},
        ]
    },
    "📱 쇼츠 — 시네마틱 세로": {
        "desc": "[9:16 최적화] UI 완전 숨김 + 좁은 FOV 3인칭. 크롭 후 영화 같은 세로 구도",
        "shorts": True,
        "keyframes": [
            {"offset_s": -12.0, "render": {"cameraMode": "thirdPerson", "fieldOfView": 50, "interfaceAll": False, "interfaceScore": False, "interfaceFrames": False, "depthOfField": True}, "speed": 1.0},
            {"offset_s":  -3.0, "render": {"cameraMode": "thirdPerson", "fieldOfView": 40}, "speed": 0.5},
            {"offset_s":   0.0, "render": {"cameraMode": "thirdPerson", "fieldOfView": 32}, "speed": 0.25},
            {"offset_s":   2.5, "render": {"cameraMode": "thirdPerson", "fieldOfView": 48, "depthOfField": False}, "speed": 1.0},
            {"offset_s":   6.0, "render": {"cameraMode": "focus",       "fieldOfView": 45}, "speed": 1.0},
        ]
    },
    "📱 쇼츠 — 쾌속 세로": {
        "desc": "[9:16 최적화] 빠른 전환 + 펜타킬 슬로우. 쇼츠 중 임팩트 최강",
        "shorts": True,
        "keyframes": [
            {"offset_s": -12.0, "render": {"cameraMode": "focus", "fieldOfView": 48, "interfaceAll": False, "interfaceScore": False, "interfaceFrames": False}, "speed": 2.0},
            {"offset_s":  -2.0, "render": {"cameraMode": "focus", "fieldOfView": 36}, "speed": 1.0},
            {"offset_s":   0.0, "render": {"cameraMode": "focus", "fieldOfView": 28, "depthOfField": True},  "speed": 0.25},
            {"offset_s":   2.5, "render": {"cameraMode": "focus", "fieldOfView": 48, "depthOfField": False}, "speed": 1.0},
        ]
    },
}

# ──────────────────────────────────────────────
#  LCU Client
# ──────────────────────────────────────────────
LOCKFILE_CANDIDATES = [
    r"C:\Riot Games\League of Legends\lockfile",
    r"C:\Program Files\Riot Games\League of Legends\lockfile",
    r"C:\Program Files (x86)\Riot Games\League of Legends\lockfile",
    r"D:\Riot Games\League of Legends\lockfile",
    r"D:\Games\League of Legends\lockfile",
    # macOS
    "/Applications/League of Legends.app/Contents/LoL/lockfile",
]

class LCUClient:
    """League Client Update API 클라이언트."""

    def __init__(self):
        self.port     = None
        self.password = None
        self.session  = requests.Session()
        self.session.verify = False   # 자체 서명 SSL
        self._connected = False

    # ── lockfile 탐색 & 연결 ──────────────────
    def find_lockfile(self) -> str | None:
        for path in LOCKFILE_CANDIDATES:
            if os.path.exists(path):
                return path
        return None

    def connect_from_lockfile(self, path: str) -> bool:
        """
        lockfile 파싱 후 연결.
        형식: LeagueClient:PID:PORT:PASSWORD:https
        """
        try:
            with open(path, "r") as f:
                parts = f.read().strip().split(":")
            # parts = [name, pid, port, password, protocol]
            self.port     = int(parts[2])
            self.password = parts[3]
            self.session.auth = ("riot", self.password)
            # 연결 확인
            self._get("/lol-summoner/v1/current-summoner")
            self._connected = True
            return True
        except Exception:
            self._connected = False
            return False

    @property
    def connected(self):
        return self._connected

    def _url(self, path: str) -> str:
        return f"https://127.0.0.1:{self.port}{path}"

    def _get(self, path: str) -> dict:
        r = self.session.get(self._url(path), timeout=5)
        r.raise_for_status()
        return r.json()

    def _post(self, path: str, data: dict = None) -> dict:
        r = self.session.post(self._url(path), json=data or {}, timeout=5)
        r.raise_for_status()
        try:    return r.json()
        except: return {}

    def _patch(self, path: str, data: dict) -> dict:
        r = self.session.patch(self._url(path), json=data, timeout=5)
        r.raise_for_status()
        try:    return r.json()
        except: return {}

    # ── 현재 소환사 ──────────────────────────
    def get_current_summoner(self) -> dict:
        return self._get("/lol-summoner/v1/current-summoner")

    # ── 저장된 리플레이 목록 ─────────────────
    def get_rofl_list(self) -> list:
        """저장된 .rofl 파일 게임 ID 목록 반환."""
        try:
            data = self._get("/lol-replays/v1/rofls")
            return data if isinstance(data, list) else []
        except Exception:
            return []

    def scan_replays(self) -> list:
        """리플레이 폴더 스캔 트리거."""
        try:
            self._post("/lol-replays/v1/rofls/scan")
            time.sleep(1.5)
            return self.get_rofl_list()
        except Exception:
            return []

    def get_replay_metadata(self, game_id: int) -> dict:
        try:
            return self._get(f"/lol-replays/v1/rofls/{game_id}/metadata")
        except Exception:
            return {}

    # ── 리플레이 재생 ────────────────────────
    def watch_replay(self, game_id: int) -> bool:
        """리플레이 실행. 이미 열려있으면 False 반환."""
        try:
            self._post(f"/lol-replays/v1/rofls/{game_id}/watch")
            return True
        except Exception:
            return False

    # ── 재생 제어 ────────────────────────────
    def get_playback(self) -> dict:
        """현재 재생 상태 반환. {currentTime, paused, speed, ...}"""
        try:
            return self._get("/lol-replays/v1/playback")
        except Exception:
            return {}

    def set_playback(self, current_time: float = None,
                     paused: bool = None, speed: float = None) -> dict:
        """재생 상태 변경."""
        data = {}
        if current_time is not None: data["currentTime"] = current_time
        if paused        is not None: data["paused"]       = paused
        if speed         is not None: data["speed"]        = speed
        try:
            return self._patch("/lol-replays/v1/playback", data)
        except Exception as e:
            raise RuntimeError(f"재생 제어 실패: {e}")

    def seek_to(self, seconds: float) -> dict:
        return self.set_playback(current_time=seconds, paused=False)

    def pause(self):
        self.set_playback(paused=True)

    def resume(self):
        self.set_playback(paused=False)

    def set_speed(self, speed: float):
        self.set_playback(speed=speed)

    # ── 카메라 ──────────────────────────────
    def get_render(self) -> dict:
        try:
            return self._get("/lol-replays/v1/render")
        except Exception:
            return {}

    def set_render(self, data: dict) -> dict:
        try:
            return self._patch("/lol-replays/v1/render", data)
        except Exception:
            return {}

    def wait_for_replay_ready(self, timeout: float = 30) -> bool:
        """리플레이가 재생 가능 상태가 될 때까지 대기."""
        start = time.time()
        while time.time() - start < timeout:
            pb = self.get_playback()
            if pb.get("length", 0) > 0:
                return True
            time.sleep(0.5)
        return False


# ──────────────────────────────────────────────
#  OBS WebSocket Client  (v5 프로토콜)
# ──────────────────────────────────────────────
class OBSClient:
    """
    OBS WebSocket v5 클라이언트.
    pip install websocket-client  필요.
    OBS → 도구 → WebSocket 서버 설정 → 활성화
    기본 포트: 4455
    """

    def __init__(self):
        self._ws        = None
        self._connected = False
        self._msg_id    = 0
        self._lock      = threading.Lock()

    # ── 연결 ──────────────────────────────────
    def connect(self, host: str = "localhost", port: int = 4455,
                password: str = "") -> bool:
        try:
            import websocket, hashlib, base64, json as _json
            ws = websocket.WebSocket()
            ws.connect(f"ws://{host}:{port}", timeout=5)

            # Hello 수신
            hello = _json.loads(ws.recv())
            rpc_ver = hello.get("d", {}).get("rpcVersion", 1)

            # Identify (비밀번호 있을 경우 인증)
            auth_data: dict = {"rpcVersion": rpc_ver}
            if password and hello.get("d", {}).get("authentication"):
                auth_info = hello["d"]["authentication"]
                secret    = base64.b64encode(
                    hashlib.sha256(
                        (password + auth_info["salt"]).encode()
                    ).digest()
                ).decode()
                auth_str  = base64.b64encode(
                    hashlib.sha256(
                        (secret + auth_info["challenge"]).encode()
                    ).digest()
                ).decode()
                auth_data["authentication"] = auth_str

            ws.send(_json.dumps({"op": 1, "d": auth_data}))
            identified = _json.loads(ws.recv())
            if identified.get("op") != 2:
                return False

            self._ws        = ws
            self._connected = True
            return True
        except Exception:
            self._connected = False
            return False

    def disconnect(self):
        if self._ws:
            try: self._ws.close()
            except: pass
        self._connected = False

    @property
    def connected(self): return self._connected

    # ── 요청 헬퍼 ─────────────────────────────
    def _request(self, request_type: str, data: dict = None) -> dict:
        import json as _json
        with self._lock:
            self._msg_id += 1
            mid = str(self._msg_id)
            payload = {
                "op": 6,
                "d": {
                    "requestType": request_type,
                    "requestId":   mid,
                    "requestData": data or {},
                }
            }
            self._ws.send(_json.dumps(payload))
            # 해당 requestId 응답 수신 (최대 3초 대기)
            import time as _time
            deadline = _time.time() + 3
            while _time.time() < deadline:
                raw = self._ws.recv()
                msg = _json.loads(raw)
                if msg.get("op") == 7 and msg["d"].get("requestId") == mid:
                    return msg["d"]
            raise TimeoutError(f"OBS 응답 타임아웃: {request_type}")

    # ── 녹화 제어 ─────────────────────────────
    def start_recording(self):
        return self._request("StartRecord")

    def stop_recording(self):
        return self._request("StopRecord")

    def get_record_status(self) -> dict:
        return self._request("GetRecordStatus")

    def toggle_recording(self):
        status = self.get_record_status()
        if status.get("responseData", {}).get("outputActive"):
            return self.stop_recording()
        return self.start_recording()

    # ── 씬 제어 ───────────────────────────────
    def get_scene_list(self) -> list:
        r = self._request("GetSceneList")
        return r.get("responseData", {}).get("scenes", [])

    def set_scene(self, scene_name: str):
        return self._request("SetCurrentProgramScene",
                             {"sceneName": scene_name})

    # ── 소스 필터 (크롭용) ────────────────────
    def set_source_filter_settings(self, source: str,
                                    filter_name: str, settings: dict):
        return self._request("SetSourceFilterSettings", {
            "sourceName":      source,
            "filterName":      filter_name,
            "filterSettings":  settings,
        })


# ──────────────────────────────────────────────
#  유틸
# ──────────────────────────────────────────────
def map_zone(x, y):
    nx, ny = x / MAP_SIZE, y / MAP_SIZE
    if nx < 0.12 and ny < 0.12: return "블루팀 기지"
    if nx > 0.88 and ny > 0.88: return "레드팀 기지"
    if ny > 0.72 and nx < 0.35: return "탑 라인"
    if ny < 0.28 and nx > 0.65: return "바텀 라인"
    if 0.38 < nx < 0.62 and 0.38 < ny < 0.62: return "미드 라인"
    if nx < 0.5 and ny > 0.5:   return "블루 정글 (탑)"
    if nx < 0.5 and ny < 0.5:   return "블루 정글 (봇)"
    if nx > 0.5 and ny > 0.5:   return "레드 정글 (탑)"
    return "레드 정글 (봇)"


def extract_pentakill_sequences(timeline, participant_id, pid_to_name,
                                pid_to_champion=None):
    if pid_to_champion is None:
        pid_to_champion = {}
    kill_events = []
    for frame in timeline.get("info", {}).get("frames", []):
        for ev in frame.get("events", []):
            if ev.get("type") == "CHAMPION_KILL" and ev.get("killerId") == participant_id:
                kill_events.append(ev)
    kill_events.sort(key=lambda e: e["timestamp"])

    sequences = []
    i = 0
    while i < len(kill_events):
        window = [kill_events[i]]
        j = i + 1
        while j < len(kill_events):
            if kill_events[j]["timestamp"] - kill_events[i]["timestamp"] <= PENTA_WINDOW_MS:
                window.append(kill_events[j])
                j += 1
            else:
                break
        if len(window) >= 5:
            seq = window[:5]
            detail = []
            for k_num, ev in enumerate(seq, 1):
                ts  = ev["timestamp"]
                pos = ev.get("position", {})
                x, y = pos.get("x", 0), pos.get("y", 0)
                gm   = ts // 1000
                interval = (ts - seq[k_num - 2]["timestamp"]) if k_num > 1 else 0
                vic_id = ev.get("victimId", 0)
                detail.append({
                    "kill_num":       k_num,
                    "timestamp_ms":   ts,
                    "timestamp_s":    ts / 1000,
                    "game_time":      f"{gm // 60:02d}:{gm % 60:02d}",
                    "interval_s":     f"+{interval / 1000:.2f}s" if k_num > 1 else "—",
                    "victim_name":    pid_to_name.get(vic_id, f"P{vic_id}"),
                    "victim_champion":pid_to_champion.get(vic_id, ""),
                    "pos_x": x, "pos_y": y,
                    "zone": map_zone(x, y),
                })
            sequences.append(detail)
            i = j
        else:
            i += 1
    return sequences


def match_id_to_game_id(match_id: str) -> int | None:
    """'KR_7234567890' → 7234567890"""
    try:
        return int(match_id.split("_")[-1])
    except Exception:
        return None


# ──────────────────────────────────────────────
#  Riot API
# ──────────────────────────────────────────────
class RiotAPI:
    def __init__(self, api_key, platform, region):
        self.platform = platform
        self.region   = region
        self.headers  = {"X-Riot-Token": api_key}

    def _get(self, url, params=None):
        r = requests.get(url, headers=self.headers, params=params, timeout=15)
        if r.status_code == 429:
            time.sleep(int(r.headers.get("Retry-After", 10)))
            return self._get(url, params)
        r.raise_for_status()
        return r.json()

    def get_league(self, tier):
        t = tier.lower()
        if t == "challenger":
            ep = f"https://{self.platform}.api.riotgames.com/lol/league/v4/challengerleagues/by-queue/{QUEUE}"
        elif t == "grandmaster":
            ep = f"https://{self.platform}.api.riotgames.com/lol/league/v4/grandmasterleagues/by-queue/{QUEUE}"
        else:
            ep = f"https://{self.platform}.api.riotgames.com/lol/league/v4/masterleagues/by-queue/{QUEUE}"
        return self._get(ep).get("entries", [])

    def get_summoner(self, sid):
        return self._get(f"https://{self.platform}.api.riotgames.com/lol/summoner/v4/summoners/{sid}")

    def get_match_ids(self, puuid, count=20):
        return self._get(
            f"https://{self.region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids",
            {"queue": 420, "count": count})

    def get_match(self, mid):
        return self._get(f"https://{self.region}.api.riotgames.com/lol/match/v5/matches/{mid}")

    def get_timeline(self, mid):
        return self._get(f"https://{self.region}.api.riotgames.com/lol/match/v5/matches/{mid}/timeline")


# ──────────────────────────────────────────────
#  메인 GUI
# ──────────────────────────────────────────────
class PentakillTracker(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("⚔  LOL  Pentakill Tracker  |  Master ~ Challenger")
        self.configure(bg=DARK)
        self.geometry("1340x900")
        self.minsize(1000, 700)

        self._stop_flag  = False
        self._sort_rev   = {}
        self._lcu        = LCUClient()
        self._obs        = OBSClient()
        self._lcu_poll   = None   # after() 핸들 (상태 폴링)
        self._session_data: dict = {}   # 저장/불러오기용 세션 데이터

        # 리플레이 점프용 데이터 저장소
        # (game_id, penta_ts_sec, summoner, champion) 리스트
        self._penta_replay_entries: list[dict] = []

        self._setup_styles()
        self._build_ui()

    # ── 스타일 ──────────────────────────────────
    def _setup_styles(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("TFrame",        background=DARK)
        s.configure("Panel.TFrame",  background=PANEL)
        s.configure("TLabel",        background=DARK,  foreground=TEXT,  font=("Malgun Gothic", 10))
        s.configure("Header.TLabel", background=DARK,  foreground=GOLD,  font=("Malgun Gothic", 22, "bold"))
        s.configure("Sub.TLabel",    background=DARK,  foreground=TEXT,  font=("Malgun Gothic", 10))
        s.configure("StatN.TLabel",  background=PANEL, foreground=GOLD,  font=("Malgun Gothic", 24, "bold"))
        s.configure("Gold.TButton",
                    background=GOLD_D, foreground=DARK,
                    font=("Malgun Gothic", 11, "bold"), padding=(16, 8), relief="flat")
        s.map("Gold.TButton",
              background=[("active", GOLD), ("disabled", "#3C3226")],
              foreground=[("disabled", "#6B5E45")])
        s.configure("Blue.TButton",
                    background="#0A2540", foreground=BLUE,
                    font=("Malgun Gothic", 11, "bold"), padding=(14, 7), relief="flat")
        s.map("Blue.TButton", background=[("active", "#0D3060"), ("disabled", "#081828")])
        s.configure("Stop.TButton",
                    background="#4A1010", foreground=RED,
                    font=("Malgun Gothic", 11, "bold"), padding=(16, 8), relief="flat")
        s.map("Stop.TButton", background=[("active", "#7A1818")])
        s.configure("Purple.TButton",
                    background="#2A1040", foreground="#C39BD3",
                    font=("Malgun Gothic", 11, "bold"), padding=(14, 7), relief="flat")
        s.map("Purple.TButton", background=[("active", "#3D1860"), ("disabled", "#1A0A28")])
        s.configure("TCombobox",
                    fieldbackground=PANEL2, background=PANEL,
                    foreground=WHITE, arrowcolor=GOLD,
                    selectbackground=PANEL2, selectforeground=WHITE,
                    font=("Malgun Gothic", 10))
        s.map("TCombobox", fieldbackground=[("readonly", PANEL2)])
        s.configure("Dark.TEntry", fieldbackground=PANEL2, foreground=WHITE,
                    insertcolor=GOLD, font=("Malgun Gothic", 10))
        s.configure("Treeview",
                    background=PANEL2, fieldbackground=PANEL2,
                    foreground=TEXT, rowheight=28, font=("Malgun Gothic", 10))
        s.configure("Treeview.Heading", background=PANEL, foreground=GOLD,
                    font=("Malgun Gothic", 10, "bold"), relief="flat")
        s.map("Treeview", background=[("selected", GOLD_D)], foreground=[("selected", WHITE)])
        s.configure("Gold.Horizontal.TProgressbar",
                    troughcolor=PANEL2, background=GOLD, thickness=6, relief="flat")
        s.configure("TNotebook", background=DARK, borderwidth=0)
        s.configure("TNotebook.Tab", background=PANEL2, foreground=TEXT,
                    font=("Malgun Gothic", 10), padding=(14, 6))
        s.map("TNotebook.Tab", background=[("selected", PANEL)], foreground=[("selected", GOLD)])
        s.configure("TScale", background=DARK, troughcolor=PANEL2)

    # ── UI 빌드 ─────────────────────────────────
    def _build_ui(self):
        # ─ 헤더 ─
        hdr = ttk.Frame(self)
        hdr.pack(fill="x")
        tk.Canvas(hdr, bg=GOLD_D, height=3, highlightthickness=0).pack(fill="x")
        ih = ttk.Frame(hdr)
        ih.pack(fill="x", padx=30, pady=(14, 10))
        ttk.Label(ih, text="⚔  PENTAKILL  TRACKER", style="Header.TLabel").pack(side="left")
        ttk.Label(ih, text="  Master · Grandmaster · Challenger  |  LCU 리플레이 컨트롤 포함",
                  style="Sub.TLabel").pack(side="left", padx=(10, 0))

        # 저장/불러오기 버튼 (헤더 우측)
        ttk.Button(ih, text="📂  불러오기", style="Blue.TButton",
                   command=self._load_session).pack(side="right", padx=(6, 0))
        ttk.Button(ih, text="💾  저장", style="Blue.TButton",
                   command=self._save_session).pack(side="right", padx=(0, 4))
        self.session_file_var = tk.StringVar(value="저장된 파일 없음")
        ttk.Label(ih, textvariable=self.session_file_var,
                  background=DARK, foreground=TEXT,
                  font=("Malgun Gothic", 8, "italic")).pack(side="right", padx=(0, 10))
        tk.Canvas(hdr, bg=GOLD_D, height=1, highlightthickness=0).pack(fill="x")

        # ─ 컨트롤 패널 ─
        ctrl = ttk.Frame(self, style="Panel.TFrame")
        ctrl.pack(fill="x")
        inn = ttk.Frame(ctrl, style="Panel.TFrame")
        inn.pack(fill="x", padx=30, pady=12)

        def lbl(text, col):
            ttk.Label(inn, text=text, background=PANEL, foreground=GOLD,
                      font=("Malgun Gothic", 9, "bold")).grid(row=0, column=col, sticky="w", padx=(0, 5))

        lbl("API Key", 0); lbl("지역", 1); lbl("티어", 2)
        lbl("최근 게임 수", 5); lbl("최대 소환사 수", 6)

        self.api_key_var = tk.StringVar()
        ttk.Entry(inn, textvariable=self.api_key_var, width=36,
                  style="Dark.TEntry", show="•").grid(row=1, column=0, sticky="w", padx=(0, 14))

        self.region_var = tk.StringVar(value="한국 (KR)")
        ttk.Combobox(inn, textvariable=self.region_var, values=list(REGIONS.keys()),
                     state="readonly", width=17).grid(row=1, column=1, sticky="w", padx=(0, 14))

        self.tier_var = tk.StringVar(value="Challenger")
        for i, t in enumerate(TIERS):
            tk.Radiobutton(inn, text=t, variable=self.tier_var, value=t,
                           bg=PANEL, fg=TEXT, selectcolor=PANEL2,
                           activebackground=PANEL, activeforeground=GOLD,
                           font=("Malgun Gothic", 10)).grid(row=1, column=2 + i, sticky="w", padx=(0, 8))

        self.match_count_var = tk.IntVar(value=20)
        tk.Spinbox(inn, from_=5, to=100, increment=5, textvariable=self.match_count_var,
                   width=5, bg=PANEL2, fg=WHITE, buttonbackground=PANEL,
                   highlightthickness=0, relief="flat",
                   font=("Malgun Gothic", 10)).grid(row=1, column=5, sticky="w", padx=(6, 14))

        self.sum_limit_var = tk.IntVar(value=30)
        tk.Spinbox(inn, from_=5, to=300, increment=5, textvariable=self.sum_limit_var,
                   width=5, bg=PANEL2, fg=WHITE, buttonbackground=PANEL,
                   highlightthickness=0, relief="flat",
                   font=("Malgun Gothic", 10)).grid(row=1, column=6, sticky="w", padx=(0, 14))

        self.search_btn = ttk.Button(inn, text="🔍  검색 시작", style="Gold.TButton",
                                     command=self._start_search)
        self.search_btn.grid(row=1, column=7, padx=(6, 5))
        self.stop_btn = ttk.Button(inn, text="⏹  중지", style="Stop.TButton",
                                   command=self._stop_search, state="disabled")
        self.stop_btn.grid(row=1, column=8)
        tk.Canvas(ctrl, bg=GOLD_D, height=1, highlightthickness=0).pack(fill="x")

        # ─ 진행 바 ─
        pf = ttk.Frame(self)
        pf.pack(fill="x", padx=30, pady=(7, 3))
        self.status_var = tk.StringVar(value="API 키를 입력하고 검색을 시작하세요.")
        ttk.Label(pf, textvariable=self.status_var, style="Sub.TLabel").pack(side="left")
        self.prog_label = ttk.Label(pf, text="", style="Sub.TLabel")
        self.prog_label.pack(side="right", padx=(0, 8))
        self.progress_var = tk.DoubleVar()
        ttk.Progressbar(pf, variable=self.progress_var,
                        style="Gold.Horizontal.TProgressbar",
                        mode="determinate", length=340).pack(side="right")

        # ─ 통계 카드 ─
        sr = ttk.Frame(self)
        sr.pack(fill="x", padx=30, pady=(0, 7))
        self.stat_cards = {}
        for key, label, default in [
            ("total_summoners", "조회한 소환사",   "0"),
            ("penta_summoners", "펜타킬 달성자",   "0"),
            ("total_pentas",    "총 펜타킬 수",    "0"),
            ("timeline_fetched","타임라인 수집",   "0"),
            ("kill_events",     "킬 이벤트",       "0"),
            ("best_champion",   "최다 펜타 챔피언","–"),
        ]:
            card = ttk.Frame(sr, style="Panel.TFrame", padding=9)
            card.pack(side="left", padx=(0, 6), ipadx=5, ipady=2)
            ttk.Label(card, text=label, background=PANEL,
                      foreground=TEXT, font=("Malgun Gothic", 9)).pack(anchor="w")
            v = ttk.Label(card, text=default, style="StatN.TLabel")
            v.pack(anchor="w")
            self.stat_cards[key] = v

        # ─ 탭 ─
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=30, pady=(0, 12))

        # 탭1 소환사 요약
        t1 = ttk.Frame(nb)
        nb.add(t1, text="  소환사별 요약  ")
        cols1 = ("rank", "summoner", "tier", "lp", "pentas", "matches")
        self.tree_summary = self._make_tree(t1, cols1,
            [("#", 40), ("소환사명", 200), ("티어", 100), ("LP", 80), ("펜타킬", 80), ("조회 게임", 90)])
        self.tree_summary.tag_configure("penta",   foreground=GOLD)
        self.tree_summary.tag_configure("nopenta", foreground=TEXT)

        # 탭2 게임별 상세
        t2 = ttk.Frame(nb)
        nb.add(t2, text="  게임별 펜타킬  ")
        cols2 = ("summoner", "champion", "kda", "pentas", "result", "duration", "date", "tl")
        self.tree_detail = self._make_tree(t2, cols2,
            [("소환사명", 165), ("챔피언", 120), ("KDA", 100), ("펜타킬", 65),
             ("결과", 65), ("게임 시간", 85), ("날짜", 95), ("타임라인", 75)])
        self.tree_detail.tag_configure("win",  foreground=GREEN)
        self.tree_detail.tag_configure("loss", foreground=RED)

        # 탭3 킬 타임라인
        t3 = ttk.Frame(nb)
        nb.add(t3, text="  ⚡ 킬 타임라인  ")
        info_f = ttk.Frame(t3, style="Panel.TFrame")
        info_f.pack(fill="x")
        ttk.Label(info_f,
                  text="  각 킬의 게임 시간·간격·피해자·맵 구역  |  5번째 킬 = 빨간색",
                  background=PANEL, foreground=TEXT,
                  font=("Malgun Gothic", 9)).pack(side="left", pady=5)
        cols3 = ("summoner", "champion", "date", "penta_num",
                 "kill_num", "game_time", "interval", "victim", "zone", "coords")
        self.tree_timeline = self._make_tree(t3, cols3,
            [("소환사명", 150), ("챔피언", 108), ("날짜", 88), ("펜타킬 #", 62),
             ("킬 순서", 80), ("게임 시간", 80), ("킬 간격", 78),
             ("피해자", 140), ("맵 구역", 135), ("좌표(x,y)", 112)],
            hscroll=True)
        for k, c in [("kill1", TEXT), ("kill2", TEXT), ("kill3", ORANGE),
                     ("kill4", GOLD), ("kill5", RED)]:
            self.tree_timeline.tag_configure(k, foreground=c)

        # ★ 탭4 LCU 리플레이 컨트롤러 ★
        t4 = ttk.Frame(nb)
        nb.add(t4, text="  🎬 리플레이 컨트롤  ")
        self._build_replay_tab(t4)

        # ★ 탭5 카메라 편집기 ★
        t5 = ttk.Frame(nb)
        nb.add(t5, text="  🎥 카메라 편집기  ")
        self._build_camera_tab(t5)

        # ★ 탭6 쇼츠 내보내기 (FFmpeg + OBS) ★
        t6 = ttk.Frame(nb)
        nb.add(t6, text="  📱 쇼츠 내보내기  ")
        self._build_export_tab(t6)

        # ★ 탭7 비트 싱크 편집기 ★
        t7 = ttk.Frame(nb)
        nb.add(t7, text="  🎵 비트 싱크  ")
        self._build_beatsync_tab(t7)

        # ★ 탭8 썸네일 생성기 ★
        t8 = ttk.Frame(nb)
        nb.add(t8, text="  🖼 썸네일  ")
        self._build_thumbnail_tab(t8)

        # 탭9 로그
        t5 = ttk.Frame(nb)
        nb.add(t5, text="  로그  ")
        self.log_text = scrolledtext.ScrolledText(
            t5, bg=PANEL2, fg=TEXT, insertbackground=GOLD,
            font=("Consolas", 9), state="disabled", relief="flat", wrap="word")
        self.log_text.pack(fill="both", expand=True)
        for tag, col in [("info", BLUE), ("ok", GREEN), ("warn", ORANGE), ("error", RED), ("lcu", PURPLE)]:
            self.log_text.tag_configure(tag, foreground=col)

    # ── LCU 탭 UI ────────────────────────────────
    def _build_replay_tab(self, parent):
        # ─ 상단: 연결 패널 ─
        conn_frame = ttk.Frame(parent, style="Panel.TFrame")
        conn_frame.pack(fill="x", pady=(0, 1))
        inner_conn = ttk.Frame(conn_frame, style="Panel.TFrame")
        inner_conn.pack(fill="x", padx=16, pady=10)

        # 상태 표시
        self.lcu_status_dot = tk.Label(inner_conn, text="●", fg=RED,
                                        bg=PANEL, font=("Malgun Gothic", 14))
        self.lcu_status_dot.pack(side="left", padx=(0, 6))
        self.lcu_status_var = tk.StringVar(value="LCU 연결 안됨 — 롤 클라이언트가 실행 중이어야 합니다")
        ttk.Label(inner_conn, textvariable=self.lcu_status_var,
                  background=PANEL, foreground=TEXT,
                  font=("Malgun Gothic", 10)).pack(side="left", padx=(0, 20))

        # 연결 버튼
        ttk.Button(inner_conn, text="🔌  자동 연결", style="Blue.TButton",
                   command=self._lcu_auto_connect).pack(side="left", padx=(0, 8))

        # 수동 lockfile 선택
        ttk.Button(inner_conn, text="📂  lockfile 직접 선택", style="Gold.TButton",
                   command=self._lcu_manual_connect).pack(side="left", padx=(0, 16))

        # Pre-roll 설정
        ttk.Label(inner_conn, text="펜타킬 앞  ", background=PANEL,
                  foreground=TEXT, font=("Malgun Gothic", 9)).pack(side="left")
        self.pre_roll_var = tk.IntVar(value=REPLAY_PRE_ROLL_SEC)
        tk.Spinbox(inner_conn, from_=0, to=60, increment=5,
                   textvariable=self.pre_roll_var, width=4,
                   bg=PANEL2, fg=WHITE, buttonbackground=PANEL,
                   highlightthickness=0, relief="flat",
                   font=("Malgun Gothic", 10)).pack(side="left")
        ttk.Label(inner_conn, text=" 초 앞에서 시작", background=PANEL,
                  foreground=TEXT, font=("Malgun Gothic", 9)).pack(side="left", padx=(0, 20))

        # ── 오프셋 보정 ──────────────────────────────────────────
        ttk.Label(inner_conn, text="│", background=PANEL,
                  foreground=GOLD_D, font=("Malgun Gothic", 12)).pack(side="left", padx=(0, 20))

        ttk.Label(inner_conn, text="⏱ 오프셋 보정", background=PANEL,
                  foreground=GOLD, font=("Malgun Gothic", 9, "bold")).pack(side="left", padx=(0, 6))
        self.seek_offset_var = tk.DoubleVar(value=0.0)
        tk.Spinbox(inner_conn, from_=-60, to=60, increment=0.5,
                   textvariable=self.seek_offset_var, width=5,
                   bg=PANEL2, fg=WHITE, buttonbackground=PANEL,
                   highlightthickness=0, relief="flat",
                   font=("Malgun Gothic", 10), format="%.1f").pack(side="left")
        ttk.Label(inner_conn, text=" 초  ", background=PANEL,
                  foreground=TEXT, font=("Malgun Gothic", 9)).pack(side="left")
        ttk.Button(inner_conn, text="↺ 초기화", style="Blue.TButton",
                   command=lambda: self.seek_offset_var.set(0.0)).pack(side="left", padx=(0, 8))
        ttk.Label(inner_conn,
                  text="(0 = 기존 방식  |  + = 더 뒤  |  - = 더 앞)",
                  background=PANEL, foreground=TEXT,
                  font=("Malgun Gothic", 8, "italic")).pack(side="left")

        # ─ 가운데: 좌우 분할 ─
        mid = ttk.Frame(parent)
        mid.pack(fill="both", expand=True)
        mid.columnconfigure(0, weight=1)
        mid.columnconfigure(1, weight=2)

        # ── 왼쪽: 펜타킬 목록 ──
        left = ttk.Frame(mid, style="Panel.TFrame")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 1))

        ttk.Label(left, text="  펜타킬 목록  (더블클릭 → 리플레이 자동 점프)",
                  background=PANEL, foreground=GOLD,
                  font=("Malgun Gothic", 10, "bold")).pack(anchor="w", pady=(8, 4), padx=10)

        cols_p = ("summoner", "champion", "game_time", "date", "game_id", "ts_sec")
        self.tree_penta_list = ttk.Treeview(left, columns=cols_p, show="headings", height=18)
        for cid, hd, w in zip(cols_p,
            ["소환사명", "챔피언", "펜타킬 시간", "날짜", "게임 ID", "타임스탬프(초)"],
            [140, 110, 90, 90, 110, 100]):
            self.tree_penta_list.heading(cid, text=hd)
            self.tree_penta_list.column(cid, width=w, anchor="center")
        self.tree_penta_list.tag_configure("has_replay", foreground=GREEN)
        self.tree_penta_list.tag_configure("no_replay",  foreground=TEXT)

        vsb_p = ttk.Scrollbar(left, orient="vertical", command=self.tree_penta_list.yview)
        self.tree_penta_list.configure(yscrollcommand=vsb_p.set)
        vsb_p.pack(side="right", fill="y", pady=(0, 4))
        self.tree_penta_list.pack(fill="both", expand=True, padx=(8, 0), pady=(0, 4))
        self.tree_penta_list.bind("<Double-1>", self._on_penta_double_click)

        # ── 오른쪽: 재생 컨트롤 ──
        right = ttk.Frame(mid)
        right.grid(row=0, column=1, sticky="nsew", padx=(1, 0))

        # 현재 재생 정보
        info_card = ttk.Frame(right, style="Panel.TFrame", padding=12)
        info_card.pack(fill="x", pady=(0, 1))

        ttk.Label(info_card, text="현재 리플레이 상태",
                  background=PANEL, foreground=GOLD,
                  font=("Malgun Gothic", 11, "bold")).pack(anchor="w")

        row_info = ttk.Frame(info_card, style="Panel.TFrame")
        row_info.pack(fill="x", pady=(6, 0))

        self.replay_time_var  = tk.StringVar(value="–:––")
        self.replay_speed_var = tk.StringVar(value="× 1.0")
        self.replay_state_var = tk.StringVar(value="대기 중")

        for label, var, color in [
            ("현재 시간", self.replay_time_var,  WHITE),
            ("배속",      self.replay_speed_var, GOLD),
            ("상태",      self.replay_state_var, BLUE),
        ]:
            col_f = ttk.Frame(row_info, style="Panel.TFrame")
            col_f.pack(side="left", padx=(0, 24))
            ttk.Label(col_f, text=label, background=PANEL,
                      foreground=TEXT, font=("Malgun Gothic", 9)).pack(anchor="w")
            ttk.Label(col_f, textvariable=var, background=PANEL,
                      foreground=color, font=("Malgun Gothic", 16, "bold")).pack(anchor="w")

        # 재생 버튼 행
        btn_row = ttk.Frame(right, style="Panel.TFrame")
        btn_row.pack(fill="x", pady=(1, 1))
        inner_btn = ttk.Frame(btn_row, style="Panel.TFrame")
        inner_btn.pack(padx=12, pady=10)

        ttk.Button(inner_btn, text="▶  재생", style="Gold.TButton",
                   command=lambda: self._lcu_cmd(lambda: self._lcu.resume())).pack(side="left", padx=(0, 6))
        ttk.Button(inner_btn, text="⏸  일시정지", style="Blue.TButton",
                   command=lambda: self._lcu_cmd(lambda: self._lcu.pause())).pack(side="left", padx=(0, 6))

        # 배속 버튼
        ttk.Label(inner_btn, text="  배속:", background=PANEL,
                  foreground=TEXT, font=("Malgun Gothic", 10)).pack(side="left", padx=(8, 4))
        for spd in [0.25, 0.5, 1.0, 2.0, 4.0, 8.0]:
            ttk.Button(inner_btn, text=f"×{spd}",
                       style="Purple.TButton" if spd in (0.25, 0.5) else "Blue.TButton",
                       command=lambda s=spd: self._lcu_cmd(lambda s=s: self._lcu.set_speed(s))
                       ).pack(side="left", padx=(0, 3))

        # 수동 Seek
        seek_frame = ttk.Frame(right, style="Panel.TFrame")
        seek_frame.pack(fill="x", pady=(0, 1))
        inner_seek = ttk.Frame(seek_frame, style="Panel.TFrame")
        inner_seek.pack(padx=12, pady=8)
        ttk.Label(inner_seek, text="시간 직접 이동 (초):", background=PANEL,
                  foreground=TEXT, font=("Malgun Gothic", 10)).pack(side="left", padx=(0, 8))
        self.seek_var = tk.StringVar(value="0")
        tk.Entry(inner_seek, textvariable=self.seek_var, width=8,
                 bg=PANEL2, fg=WHITE, insertbackground=GOLD,
                 highlightthickness=0, relief="flat",
                 font=("Malgun Gothic", 11)).pack(side="left", padx=(0, 6))
        ttk.Button(inner_seek, text="⏩  이동", style="Gold.TButton",
                   command=self._lcu_seek_manual).pack(side="left")

        # 저장된 리플레이 목록
        rep_frame = ttk.Frame(right)
        rep_frame.pack(fill="both", expand=True)

        hdr_rep = ttk.Frame(rep_frame, style="Panel.TFrame")
        hdr_rep.pack(fill="x")
        ttk.Label(hdr_rep, text="  저장된 리플레이",
                  background=PANEL, foreground=GOLD,
                  font=("Malgun Gothic", 10, "bold")).pack(side="left", pady=(7, 5), padx=8)
        ttk.Button(hdr_rep, text="🔄  새로고침", style="Blue.TButton",
                   command=self._lcu_refresh_replays).pack(side="right", padx=8, pady=4)

        cols_r = ("game_id", "date", "status")
        self.tree_replays = ttk.Treeview(rep_frame, columns=cols_r, show="headings", height=6)
        for cid, hd, w in zip(cols_r, ["게임 ID", "날짜", "상태"], [160, 120, 120]):
            self.tree_replays.heading(cid, text=hd)
            self.tree_replays.column(cid, width=w, anchor="center")
        self.tree_replays.tag_configure("available", foreground=GREEN)
        self.tree_replays.tag_configure("watching",  foreground=GOLD)

        vsb_r = ttk.Scrollbar(rep_frame, orient="vertical", command=self.tree_replays.yview)
        self.tree_replays.configure(yscrollcommand=vsb_r.set)
        vsb_r.pack(side="right", fill="y")
        self.tree_replays.pack(fill="both", expand=True)

        # 폴링 시작
        self._lcu_poll_status()

    # ── LCU 연결 ────────────────────────────────
    def _lcu_auto_connect(self):
        path = self._lcu.find_lockfile()
        if not path:
            self._lcu_set_status(False, "lockfile을 찾을 수 없습니다. 롤 클라이언트가 실행 중인지 확인하세요.")
            messagebox.showwarning("연결 실패",
                "lockfile을 자동으로 찾지 못했습니다.\n"
                "'lockfile 직접 선택' 버튼으로 수동 지정해 주세요.\n\n"
                "일반적인 경로:\n"
                "C:\\Riot Games\\League of Legends\\lockfile")
            return
        self._lcu_connect(path)

    def _lcu_manual_connect(self):
        path = filedialog.askopenfilename(
            title="lockfile 선택",
            filetypes=[("lockfile", "lockfile"), ("모든 파일", "*.*")])
        if path:
            self._lcu_connect(path)

    def _lcu_connect(self, path: str):
        self._lcu_set_status(None, "연결 중…")
        def _do():
            ok = self._lcu.connect_from_lockfile(path)
            if ok:
                try:
                    me = self._lcu.get_current_summoner()
                    name = me.get("displayName", me.get("gameName", "Unknown"))
                    self.after(0, lambda n=name: self._lcu_set_status(True, f"연결됨  |  {n}"))
                    self._log(f"LCU 연결 성공: {name}", "lcu")
                    self.after(0, self._lcu_refresh_replays)
                    self.after(0, self._update_replay_list_tags)
                except Exception as e:
                    self.after(0, lambda: self._lcu_set_status(True, "연결됨 (소환사 정보 오류)"))
            else:
                self.after(0, lambda: self._lcu_set_status(False, "연결 실패 — lockfile 확인 필요"))
                self._log("LCU 연결 실패", "error")
        threading.Thread(target=_do, daemon=True).start()

    def _lcu_set_status(self, connected: bool | None, msg: str):
        def _do():
            self.lcu_status_var.set(msg)
            if connected is True:
                self.lcu_status_dot.config(fg=GREEN)
            elif connected is False:
                self.lcu_status_dot.config(fg=RED)
            else:
                self.lcu_status_dot.config(fg=ORANGE)
        self.after(0, _do)

    # ── LCU 상태 폴링 (1초마다) ─────────────────
    def _lcu_poll_status(self):
        if self._lcu.connected:
            try:
                pb = self._lcu.get_playback()
                if pb:
                    ct  = pb.get("currentTime", 0)
                    m, s = int(ct) // 60, int(ct) % 60
                    spd = pb.get("speed", 1.0)
                    paused = pb.get("paused", False)
                    self.replay_time_var.set(f"{m}:{s:02d}")
                    self.replay_speed_var.set(f"× {spd:.2f}")
                    self.replay_state_var.set("일시정지" if paused else "재생 중")
            except Exception:
                pass
        self._lcu_poll = self.after(1000, self._lcu_poll_status)

    # ── LCU 명령 래퍼 ───────────────────────────
    def _lcu_cmd(self, fn):
        if not self._lcu.connected:
            messagebox.showwarning("연결 필요", "먼저 LCU에 연결해 주세요.")
            return
        try:
            fn()
        except Exception as e:
            messagebox.showerror("LCU 오류", str(e))

    def _lcu_seek_manual(self):
        try:
            sec = float(self.seek_var.get())
            self._lcu_cmd(lambda: self._lcu.seek_to(sec))
        except ValueError:
            messagebox.showwarning("입력 오류", "올바른 숫자(초)를 입력하세요.")

    # ── 저장된 리플레이 목록 새로고침 ──────────
    def _lcu_refresh_replays(self):
        if not self._lcu.connected:
            return
        def _do():
            replays = self._lcu.scan_replays()
            self.after(0, lambda r=replays: self._fill_replay_tree(r))
            self.after(0, self._update_replay_list_tags)
        threading.Thread(target=_do, daemon=True).start()

    def _fill_replay_tree(self, replays: list):
        self.tree_replays.delete(*self.tree_replays.get_children())
        for r in replays:
            gid = r.get("gameId", "")
            self.tree_replays.insert("", "end",
                values=(gid, "–", "저장됨"), tags=("available",))

    # ── 펜타킬 목록 태그 갱신 (리플레이 있는지 표시) ─
    def _update_replay_list_tags(self):
        if not self._lcu.connected:
            return
        available_ids = set()
        for row in self.tree_replays.get_children():
            try:
                available_ids.add(int(self.tree_replays.set(row, "game_id")))
            except Exception:
                pass

        for row in self.tree_penta_list.get_children():
            try:
                gid = int(self.tree_penta_list.set(row, "game_id"))
                tag = "has_replay" if gid in available_ids else "no_replay"
                self.tree_penta_list.item(row, tags=(tag,))
            except Exception:
                pass

    # ── 펜타킬 더블클릭 → 리플레이 자동 점프 ──
    def _on_penta_double_click(self, event):
        sel = self.tree_penta_list.selection()
        if not sel:
            return
        item = sel[0]
        try:
            game_id = int(self.tree_penta_list.set(item, "game_id"))
            ts_sec  = float(self.tree_penta_list.set(item, "ts_sec"))
            sname   = self.tree_penta_list.set(item, "summoner")
            champ   = self.tree_penta_list.set(item, "champion")
            gt      = self.tree_penta_list.set(item, "game_time")
        except Exception as e:
            messagebox.showerror("오류", f"데이터 파싱 실패: {e}")
            return

        if not self._lcu.connected:
            messagebox.showwarning("연결 필요", "LCU에 연결되어 있지 않습니다.\n'자동 연결' 버튼을 눌러주세요.")
            return

        pre_roll = self.pre_roll_var.get()
        offset   = self.seek_offset_var.get()
        jump_sec = max(0.0, ts_sec - pre_roll + offset)

        self._log(
            f"[LCU] 리플레이 점프: {sname} | {champ} | 게임시간 {gt} | "
            f"pre_roll={pre_roll}s  offset={offset:+.1f}s  → seek {jump_sec:.1f}s", "lcu")
        threading.Thread(
            target=self._do_replay_jump,
            args=(game_id, jump_sec, sname, champ, gt),
            daemon=True).start()

    def _do_replay_jump(self, game_id: int, jump_sec: float,
                        sname: str, champ: str, gt: str):
        """리플레이 실행 → 대기 → seek → 속도 1.0"""
        def update_state(msg):
            self.after(0, lambda m=msg: self.replay_state_var.set(m))

        try:
            # 1) 리플레이 실행
            update_state("리플레이 실행 중…")
            self._lcu.watch_replay(game_id)
            self._log(f"[LCU] 게임 {game_id} 리플레이 실행", "lcu")

            # 2) 로딩 대기 (최대 45초)
            update_state("로딩 대기…")
            ready = self._lcu.wait_for_replay_ready(timeout=45)
            if not ready:
                self._log(f"[LCU] 리플레이 로딩 타임아웃", "error")
                update_state("로딩 실패")
                return

            # 3) 추가 대기 (안정화)
            time.sleep(1.5)

            # 4) seek
            update_state(f"→ {int(jump_sec) // 60}:{int(jump_sec) % 60:02d} 로 이동 중…")
            self._lcu.seek_to(jump_sec)
            self._lcu.set_speed(1.0)
            self._log(f"[LCU] seek 완료: {sname} {champ} 펜타킬 @ {gt} (seek={jump_sec:.1f}s)", "lcu")
            update_state("재생 중")

        except Exception as e:
            self._log(f"[LCU] 리플레이 점프 오류: {e}", "error")
            update_state(f"오류: {e}")
            self.after(0, lambda: messagebox.showerror("LCU 오류", str(e)))

    # ── 카메라 편집기 탭 ─────────────────────────
    def _build_camera_tab(self, parent):
        # 시퀀스 실행 상태
        self._cam_running   = False
        self._cam_stop_flag = False
        # 커스텀 키프레임 리스트 (각 항목: dict)
        self._keyframes: list[dict] = []

        # ─ 상단: 프리셋 선택 ─
        preset_frame = ttk.Frame(parent, style="Panel.TFrame")
        preset_frame.pack(fill="x", pady=(0, 1))
        pf_inner = ttk.Frame(preset_frame, style="Panel.TFrame")
        pf_inner.pack(fill="x", padx=14, pady=10)

        ttk.Label(pf_inner, text="카메라 프리셋", background=PANEL,
                  foreground=GOLD, font=("Malgun Gothic", 11, "bold")).pack(side="left", padx=(0, 16))

        self.preset_var = tk.StringVar(value=list(CAMERA_PRESETS.keys())[0])
        preset_cb = ttk.Combobox(pf_inner, textvariable=self.preset_var,
                                  values=list(CAMERA_PRESETS.keys()),
                                  state="readonly", width=24)
        preset_cb.pack(side="left", padx=(0, 10))
        preset_cb.bind("<<ComboboxSelected>>", self._on_preset_select)

        self.preset_desc_var = tk.StringVar(value=list(CAMERA_PRESETS.values())[0]["desc"])
        ttk.Label(pf_inner, textvariable=self.preset_desc_var,
                  background=PANEL, foreground=TEXT,
                  font=("Malgun Gothic", 9, "italic")).pack(side="left", padx=(0, 20))

        ttk.Button(pf_inner, text="📋  편집기에 불러오기", style="Blue.TButton",
                   command=self._load_preset_to_editor).pack(side="left", padx=(0, 8))

        # ─ 가운데: 좌우 분할 ─
        mid = ttk.Frame(parent)
        mid.pack(fill="both", expand=True)
        mid.columnconfigure(0, weight=3)
        mid.columnconfigure(1, weight=2)

        # ══ 왼쪽: 키프레임 편집기 ══
        left = ttk.Frame(mid)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 1))

        # 편집기 헤더
        kf_hdr = ttk.Frame(left, style="Panel.TFrame")
        kf_hdr.pack(fill="x")
        ttk.Label(kf_hdr, text="  키프레임 편집기",
                  background=PANEL, foreground=GOLD,
                  font=("Malgun Gothic", 10, "bold")).pack(side="left", pady=(7, 5), padx=6)
        ttk.Label(kf_hdr,
                  text="  offset_s = 펜타킬 확정 순간(t=0) 기준 상대 시간 (음수 = 이전)",
                  background=PANEL, foreground=TEXT,
                  font=("Malgun Gothic", 8, "italic")).pack(side="left")

        # 키프레임 트리
        kf_cols = ("offset_s", "cam_mode", "fov", "speed",
                   "depth", "ui_hide", "extra")
        self.tree_kf = ttk.Treeview(left, columns=kf_cols, show="headings", height=10)
        for cid, hd, w in zip(kf_cols,
            ["시간(s)", "카메라 모드", "FOV", "배속",
             "아웃포커스", "UI숨김", "추가 설정"],
            [75, 120, 55, 60, 80, 65, 240]):
            self.tree_kf.heading(cid, text=hd)
            self.tree_kf.column(cid, width=w, anchor="center")
        self.tree_kf.tag_configure("selected_kf", background=GOLD_D)

        kf_vsb = ttk.Scrollbar(left, orient="vertical", command=self.tree_kf.yview)
        self.tree_kf.configure(yscrollcommand=kf_vsb.set)
        kf_vsb.pack(side="right", fill="y")
        self.tree_kf.pack(fill="both", expand=True)
        self.tree_kf.bind("<<TreeviewSelect>>", self._on_kf_select)

        # 키프레임 조작 버튼 행
        kf_btns = ttk.Frame(left, style="Panel.TFrame")
        kf_btns.pack(fill="x")
        ib = ttk.Frame(kf_btns, style="Panel.TFrame")
        ib.pack(padx=8, pady=8)
        ttk.Button(ib, text="➕  추가", style="Gold.TButton",
                   command=self._kf_add).pack(side="left", padx=(0, 5))
        ttk.Button(ib, text="✏️  수정", style="Blue.TButton",
                   command=self._kf_edit).pack(side="left", padx=(0, 5))
        ttk.Button(ib, text="🗑  삭제", style="Stop.TButton",
                   command=self._kf_delete).pack(side="left", padx=(0, 5))
        ttk.Button(ib, text="⬆", style="Blue.TButton",
                   command=lambda: self._kf_move(-1)).pack(side="left", padx=(0, 3))
        ttk.Button(ib, text="⬇", style="Blue.TButton",
                   command=lambda: self._kf_move(1)).pack(side="left", padx=(0, 12))
        ttk.Button(ib, text="🗑  전체 초기화", style="Stop.TButton",
                   command=self._kf_clear).pack(side="left")

        # ══ 오른쪽: 실행 패널 ══
        right = ttk.Frame(mid)
        right.grid(row=0, column=1, sticky="nsew", padx=(1, 0))

        # ─ 실행 설정 ─
        run_card = ttk.Frame(right, style="Panel.TFrame", padding=12)
        run_card.pack(fill="x", pady=(0, 1))
        ttk.Label(run_card, text="시퀀스 실행",
                  background=PANEL, foreground=GOLD,
                  font=("Malgun Gothic", 11, "bold")).pack(anchor="w")

        # 펜타킬 기준 시간
        row_ts = ttk.Frame(run_card, style="Panel.TFrame")
        row_ts.pack(fill="x", pady=(8, 4))
        ttk.Label(row_ts, text="펜타킬 절대 시간(초):",
                  background=PANEL, foreground=TEXT,
                  font=("Malgun Gothic", 10)).pack(side="left", padx=(0, 8))
        self.cam_ts_var = tk.StringVar(value="0.0")
        tk.Entry(row_ts, textvariable=self.cam_ts_var, width=8,
                 bg=PANEL2, fg=WHITE, insertbackground=GOLD,
                 highlightthickness=0, relief="flat",
                 font=("Malgun Gothic", 11)).pack(side="left", padx=(0, 8))
        ttk.Label(row_ts, text="← 펜타킬 목록에서 선택하면 자동 입력",
                  background=PANEL, foreground=TEXT,
                  font=("Malgun Gothic", 8, "italic")).pack(side="left")

        # 실행/중지 버튼
        run_btns = ttk.Frame(run_card, style="Panel.TFrame")
        run_btns.pack(fill="x", pady=(4, 0))
        self.run_seq_btn = ttk.Button(run_btns, text="▶  시퀀스 실행", style="Gold.TButton",
                                       command=self._run_camera_sequence)
        self.run_seq_btn.pack(side="left", padx=(0, 8))
        self.stop_seq_btn = ttk.Button(run_btns, text="⏹  중지", style="Stop.TButton",
                                        command=self._stop_camera_sequence, state="disabled")
        self.stop_seq_btn.pack(side="left", padx=(0, 12))
        ttk.Button(run_btns, text="📸  현재 카메라 상태 읽기", style="Blue.TButton",
                   command=self._read_current_camera).pack(side="left")

        # 시퀀스 진행 상태
        self.cam_status_var = tk.StringVar(value="대기 중")
        self.cam_prog_var   = tk.DoubleVar(value=0)
        ttk.Label(run_card, textvariable=self.cam_status_var,
                  background=PANEL, foreground=BLUE,
                  font=("Malgun Gothic", 10)).pack(anchor="w", pady=(6, 2))
        ttk.Progressbar(run_card, variable=self.cam_prog_var,
                        style="Gold.Horizontal.TProgressbar",
                        mode="determinate", length=300).pack(anchor="w")

        # ─ 현재 카메라 상태 표시 ─
        cam_info = ttk.Frame(right, style="Panel.TFrame", padding=10)
        cam_info.pack(fill="x", pady=(1, 1))
        ttk.Label(cam_info, text="현재 렌더 설정",
                  background=PANEL, foreground=GOLD,
                  font=("Malgun Gothic", 10, "bold")).pack(anchor="w", pady=(0, 4))

        self.cam_info_text = scrolledtext.ScrolledText(
            cam_info, bg=PANEL2, fg=TEXT, insertbackground=GOLD,
            font=("Consolas", 8), height=8, state="disabled",
            relief="flat", wrap="word")
        self.cam_info_text.pack(fill="both")

        # ─ 펜타킬 목록 (카메라 탭용 — 클릭하면 cam_ts_var 자동 입력) ─
        plist_frame = ttk.Frame(right)
        plist_frame.pack(fill="both", expand=True)

        ttk.Label(plist_frame,
                  text="  펜타킬 목록  (클릭 → 시간 자동 입력)",
                  background=PANEL, foreground=GOLD,
                  font=("Malgun Gothic", 9, "bold")).pack(anchor="w",
                  pady=(6, 2), padx=6)

        cols_cp = ("summoner", "champion", "game_time", "ts_sec")
        self.tree_cam_penta = ttk.Treeview(plist_frame, columns=cols_cp,
                                            show="headings", height=6)
        for cid, hd, w in zip(cols_cp,
            ["소환사명", "챔피언", "펜타킬 시간", "타임스탬프(초)"],
            [140, 110, 90, 100]):
            self.tree_cam_penta.heading(cid, text=hd)
            self.tree_cam_penta.column(cid, width=w, anchor="center")
        self.tree_cam_penta.bind("<<TreeviewSelect>>", self._on_cam_penta_select)

        cam_vsb = ttk.Scrollbar(plist_frame, orient="vertical",
                                 command=self.tree_cam_penta.yview)
        self.tree_cam_penta.configure(yscrollcommand=cam_vsb.set)
        cam_vsb.pack(side="right", fill="y")
        self.tree_cam_penta.pack(fill="both", expand=True, padx=(6, 0))

    # ── 카메라 탭 이벤트 ────────────────────────
    def _on_preset_select(self, _=None):
        name = self.preset_var.get()
        if name in CAMERA_PRESETS:
            self.preset_desc_var.set(CAMERA_PRESETS[name]["desc"])

    def _load_preset_to_editor(self):
        name = self.preset_var.get()
        if name not in CAMERA_PRESETS:
            return
        self._keyframes = [dict(kf) for kf in CAMERA_PRESETS[name]["keyframes"]]
        self._refresh_kf_tree()
        self._log(f"[카메라] 프리셋 '{name}' 불러옴 ({len(self._keyframes)}개 키프레임)", "lcu")

    def _refresh_kf_tree(self):
        self.tree_kf.delete(*self.tree_kf.get_children())
        for kf in self._keyframes:
            r  = kf.get("render", {})
            ex = {k: v for k, v in r.items()
                  if k not in ("cameraMode", "fieldOfView", "depthOfField",
                               "interfaceAll", "interfaceScore", "interfaceFrames")}
            self.tree_kf.insert("", "end", values=(
                f"{kf.get('offset_s', 0):+.1f}",
                r.get("cameraMode", "–"),
                r.get("fieldOfView", "–"),
                f"× {kf.get('speed', 1.0)}",
                "ON" if r.get("depthOfField") else "OFF",
                "ON" if r.get("interfaceAll") == False else "–",
                ", ".join(f"{k}={v}" for k, v in ex.items()) or "–",
            ))

    def _on_kf_select(self, _=None):
        pass

    def _kf_add(self):
        self._open_kf_dialog(mode="add")

    def _kf_edit(self):
        sel = self.tree_kf.selection()
        if not sel:
            messagebox.showinfo("선택 필요", "수정할 키프레임을 선택하세요.")
            return
        idx = self.tree_kf.index(sel[0])
        self._open_kf_dialog(mode="edit", idx=idx)

    def _kf_delete(self):
        sel = self.tree_kf.selection()
        if not sel:
            return
        idx = self.tree_kf.index(sel[0])
        self._keyframes.pop(idx)
        self._refresh_kf_tree()

    def _kf_move(self, direction: int):
        sel = self.tree_kf.selection()
        if not sel:
            return
        idx = self.tree_kf.index(sel[0])
        new_idx = idx + direction
        if 0 <= new_idx < len(self._keyframes):
            self._keyframes.insert(new_idx, self._keyframes.pop(idx))
            self._refresh_kf_tree()
            children = self.tree_kf.get_children()
            if 0 <= new_idx < len(children):
                self.tree_kf.selection_set(children[new_idx])

    def _kf_clear(self):
        if messagebox.askyesno("확인", "모든 키프레임을 삭제할까요?"):
            self._keyframes.clear()
            self._refresh_kf_tree()

    def _open_kf_dialog(self, mode="add", idx=None):
        """키프레임 추가/수정 다이얼로그."""
        dlg = tk.Toplevel(self)
        dlg.title("키프레임 편집" if mode == "edit" else "키프레임 추가")
        dlg.configure(bg=DARK)
        dlg.resizable(False, False)
        dlg.grab_set()

        existing = self._keyframes[idx] if mode == "edit" and idx is not None else {}
        ex_r = existing.get("render", {})

        fields = {}

        def row(label, default, row_n, width=12):
            ttk.Label(dlg, text=label, background=DARK, foreground=TEXT,
                      font=("Malgun Gothic", 10)).grid(row=row_n, column=0,
                      sticky="w", padx=(16, 8), pady=4)
            var = tk.StringVar(value=str(default))
            tk.Entry(dlg, textvariable=var, width=width,
                     bg=PANEL2, fg=WHITE, insertbackground=GOLD,
                     highlightthickness=0, relief="flat",
                     font=("Malgun Gothic", 10)).grid(row=row_n, column=1,
                     sticky="w", padx=(0, 16), pady=4)
            fields[label] = var

        def boolrow(label, default, row_n):
            ttk.Label(dlg, text=label, background=DARK, foreground=TEXT,
                      font=("Malgun Gothic", 10)).grid(row=row_n, column=0,
                      sticky="w", padx=(16, 8), pady=4)
            var = tk.BooleanVar(value=default)
            tk.Checkbutton(dlg, variable=var, bg=DARK,
                           activebackground=DARK,
                           selectcolor=PANEL2).grid(row=row_n, column=1, sticky="w",
                           padx=(0, 16), pady=4)
            fields[label] = var

        def moderow(row_n):
            ttk.Label(dlg, text="카메라 모드", background=DARK, foreground=TEXT,
                      font=("Malgun Gothic", 10)).grid(row=row_n, column=0,
                      sticky="w", padx=(16, 8), pady=4)
            var = tk.StringVar(value=ex_r.get("cameraMode", "focus"))
            cb = ttk.Combobox(dlg, textvariable=var,
                              values=["focus", "fps", "thirdPerson", "top", "path"],
                              state="readonly", width=14)
            cb.grid(row=row_n, column=1, sticky="w", padx=(0, 16), pady=4)
            fields["카메라 모드"] = var

        ttk.Label(dlg, text="  키프레임 설정",
                  background=DARK, foreground=GOLD,
                  font=("Malgun Gothic", 12, "bold")).grid(row=0, column=0,
                  columnspan=2, sticky="w", padx=16, pady=(14, 6))

        row("시간 오프셋(초)", existing.get("offset_s", 0.0), 1)
        moderow(2)
        row("FOV", ex_r.get("fieldOfView", 70), 3, 8)
        row("배속", existing.get("speed", 1.0), 4, 8)
        boolrow("아웃포커스(DOF)", ex_r.get("depthOfField", False), 5)
        boolrow("UI 전체 숨기기", ex_r.get("interfaceAll") == False, 6)
        boolrow("점수판 숨기기",  ex_r.get("interfaceScore") == False, 7)

        def save():
            try:
                kf = {
                    "offset_s": float(fields["시간 오프셋(초)"].get()),
                    "speed":    float(fields["배속"].get()),
                    "render": {
                        "cameraMode":      fields["카메라 모드"].get(),
                        "fieldOfView":     int(fields["FOV"].get()),
                        "depthOfField":    fields["아웃포커스(DOF)"].get(),
                        "interfaceAll":    not fields["UI 전체 숨기기"].get(),
                        "interfaceScore":  not fields["점수판 숨기기"].get(),
                    }
                }
                if mode == "add":
                    self._keyframes.append(kf)
                else:
                    self._keyframes[idx] = kf
                self._refresh_kf_tree()
                dlg.destroy()
            except ValueError as e:
                messagebox.showerror("입력 오류", f"숫자 형식을 확인하세요: {e}", parent=dlg)

        btn_row = ttk.Frame(dlg)
        btn_row.grid(row=8, column=0, columnspan=2, pady=(8, 14))
        ttk.Button(btn_row, text="✅  저장", style="Gold.TButton",
                   command=save).pack(side="left", padx=(0, 8))
        ttk.Button(btn_row, text="취소", style="Stop.TButton",
                   command=dlg.destroy).pack(side="left")

    # ── 현재 카메라 상태 읽기 ───────────────────
    def _read_current_camera(self):
        if not self._lcu.connected:
            messagebox.showwarning("연결 필요", "LCU에 먼저 연결하세요.")
            return
        def _do():
            rd = self._lcu.get_render()
            pretty = json.dumps(rd, indent=2, ensure_ascii=False)
            def _ui():
                self.cam_info_text.config(state="normal")
                self.cam_info_text.delete("1.0", "end")
                self.cam_info_text.insert("end", pretty)
                self.cam_info_text.config(state="disabled")
            self.after(0, _ui)
            self._log(f"[카메라] 현재 렌더 상태 읽기 완료", "lcu")
        threading.Thread(target=_do, daemon=True).start()

    # ── 카메라 탭 펜타킬 선택 ───────────────────
    def _on_cam_penta_select(self, _=None):
        sel = self.tree_cam_penta.selection()
        if not sel:
            return
        try:
            ts = self.tree_cam_penta.set(sel[0], "ts_sec")
            self.cam_ts_var.set(ts)
        except Exception:
            pass

    # ── 시퀀스 실행 ─────────────────────────────
    def _run_camera_sequence(self):
        if not self._lcu.connected:
            messagebox.showwarning("연결 필요", "LCU에 먼저 연결하세요.")
            return
        if not self._keyframes:
            messagebox.showwarning("키프레임 없음", "키프레임을 먼저 추가하세요.")
            return
        try:
            penta_ts = float(self.cam_ts_var.get())
        except ValueError:
            messagebox.showerror("오류", "펜타킬 시간(초)을 올바르게 입력하세요.")
            return

        self._cam_stop_flag = False
        self._cam_running   = True
        self.run_seq_btn.config(state="disabled")
        self.stop_seq_btn.config(state="normal")

        threading.Thread(
            target=self._camera_sequence_worker,
            args=(list(self._keyframes), penta_ts),
            daemon=True).start()

    def _stop_camera_sequence(self):
        self._cam_stop_flag = True
        self._log("[카메라] 시퀀스 중지 요청", "warn")

    def _camera_sequence_worker(self, keyframes: list, penta_ts: float):
        """
        키프레임 리스트를 순서대로 실행.
        각 키프레임의 offset_s는 penta_ts 기준 상대 시간.
        실제 적용 시각 = penta_ts + offset_s
        """
        total = len(keyframes)

        def set_status(msg, prog=None):
            self.after(0, lambda m=msg, p=prog: (
                self.cam_status_var.set(m),
                self.cam_prog_var.set(p) if p is not None else None,
            ))

        self._log(f"[카메라] 시퀀스 시작 — {total}개 키프레임 | 펜타킬 기준 {penta_ts:.1f}s", "lcu")

        # OBS 자동 녹화 시작
        if (hasattr(self, 'obs_auto_rec_var') and self.obs_auto_rec_var.get()
                and self._obs.connected):
            try:
                # 씬 전환
                if hasattr(self, 'obs_auto_scene_var') and self.obs_auto_scene_var.get():
                    scene = self.obs_scene_var.get()
                    if scene and scene != "–":
                        self._obs.set_scene(scene)
                        self._log(f"[OBS] 씬 전환: {scene}", "lcu")
                # 딜레이 대기
                delay = self.obs_delay_var.get() if hasattr(self, 'obs_delay_var') else 2
                if delay > 0:
                    set_status(f"녹화 시작 전 {delay}초 대기…")
                    time.sleep(delay)
                self._obs.start_recording()
                self._log("[OBS] 녹화 자동 시작", "ok")
            except Exception as e:
                self._log(f"[OBS] 자동 녹화 시작 오류: {e}", "error")

        # 키프레임을 절대 시간 기준으로 정렬
        kfs = sorted(keyframes, key=lambda k: k.get("offset_s", 0))

        for i, kf in enumerate(kfs):
            if self._cam_stop_flag:
                break

            target_abs = penta_ts + kf.get("offset_s", 0)
            render     = kf.get("render", {})
            speed      = kf.get("speed", 1.0)
            offset_s   = kf.get("offset_s", 0)

            set_status(
                f"키프레임 {i+1}/{total}  |  t={offset_s:+.1f}s  |  "
                f"{render.get('cameraMode','?')} FOV={render.get('fieldOfView','?')} ×{speed}",
                (i / total) * 100
            )

            # 1) 리플레이를 해당 시점으로 seek (첫 키프레임 전에만)
            if i == 0:
                try:
                    self._lcu.seek_to(max(0, target_abs))
                    time.sleep(0.8)  # seek 안정화 대기
                except Exception as e:
                    self._log(f"[카메라] seek 오류: {e}", "error")

            # 2) 렌더 설정 적용
            try:
                self._lcu.set_render(render)
                self._log(
                    f"[카메라] KF{i+1} 적용: mode={render.get('cameraMode')} "
                    f"FOV={render.get('fieldOfView')} speed={speed} "
                    f"@ t={offset_s:+.1f}s", "lcu")
            except Exception as e:
                self._log(f"[카메라] 렌더 설정 오류: {e}", "error")

            # 3) 배속 설정
            try:
                self._lcu.set_speed(speed)
            except Exception as e:
                self._log(f"[카메라] 배속 오류: {e}", "error")

            # 4) 다음 키프레임까지 대기
            if i < len(kfs) - 1:
                next_abs = penta_ts + kfs[i + 1].get("offset_s", 0)
                wait_sec = next_abs - target_abs

                if wait_sec > 0:
                    # 배속이 적용된 실제 경과 시간 = 게임 시간 / 배속
                    real_wait = wait_sec / speed if speed > 0 else wait_sec
                    # 0.1초 단위로 쪼개서 중지 플래그 체크
                    elapsed = 0.0
                    chunk   = 0.1
                    while elapsed < real_wait and not self._cam_stop_flag:
                        time.sleep(chunk)
                        elapsed += chunk

        if self._cam_stop_flag:
            set_status("⏹ 중지됨", 0)
            self._log("[카메라] 시퀀스 중지됨", "warn")
        else:
            set_status("✅ 시퀀스 완료!", 100)
            self._log("[카메라] 시퀀스 완료", "ok")

        # OBS 자동 녹화 중지
        if (hasattr(self, 'obs_auto_rec_var') and self.obs_auto_rec_var.get()
                and self._obs.connected):
            try:
                self._obs.stop_recording()
                self._log("[OBS] 녹화 자동 중지", "warn")
            except Exception as e:
                self._log(f"[OBS] 자동 녹화 중지 오류: {e}", "error")

        self._cam_running = False
        self.after(0, lambda: (
            self.run_seq_btn.config(state="normal"),
            self.stop_seq_btn.config(state="disabled"),
        ))

    # ── 쇼츠 내보내기 탭 ────────────────────────
    def _build_export_tab(self, parent):

        # ════════════════════════════════════════
        #  상단: OBS 연결 패널
        # ════════════════════════════════════════
        obs_frame = ttk.Frame(parent, style="Panel.TFrame")
        obs_frame.pack(fill="x", pady=(0, 1))
        obs_inner = ttk.Frame(obs_frame, style="Panel.TFrame")
        obs_inner.pack(fill="x", padx=14, pady=10)

        # OBS 상태 표시
        self.obs_dot = tk.Label(obs_inner, text="●", fg=RED,
                                bg=PANEL, font=("Malgun Gothic", 14))
        self.obs_dot.pack(side="left", padx=(0, 5))
        self.obs_status_var = tk.StringVar(value="OBS 연결 안됨")
        ttk.Label(obs_inner, textvariable=self.obs_status_var,
                  background=PANEL, foreground=TEXT,
                  font=("Malgun Gothic", 10)).pack(side="left", padx=(0, 16))

        # 연결 설정
        ttk.Label(obs_inner, text="Host:", background=PANEL,
                  foreground=TEXT, font=("Malgun Gothic", 9)).pack(side="left")
        self.obs_host_var = tk.StringVar(value="localhost")
        tk.Entry(obs_inner, textvariable=self.obs_host_var, width=12,
                 bg=PANEL2, fg=WHITE, insertbackground=GOLD,
                 highlightthickness=0, relief="flat",
                 font=("Malgun Gothic", 9)).pack(side="left", padx=(4, 8))

        ttk.Label(obs_inner, text="Port:", background=PANEL,
                  foreground=TEXT, font=("Malgun Gothic", 9)).pack(side="left")
        self.obs_port_var = tk.StringVar(value="4455")
        tk.Entry(obs_inner, textvariable=self.obs_port_var, width=6,
                 bg=PANEL2, fg=WHITE, insertbackground=GOLD,
                 highlightthickness=0, relief="flat",
                 font=("Malgun Gothic", 9)).pack(side="left", padx=(4, 8))

        ttk.Label(obs_inner, text="PW:", background=PANEL,
                  foreground=TEXT, font=("Malgun Gothic", 9)).pack(side="left")
        self.obs_pw_var = tk.StringVar()
        tk.Entry(obs_inner, textvariable=self.obs_pw_var, width=10,
                 bg=PANEL2, fg=WHITE, insertbackground=GOLD,
                 highlightthickness=0, relief="flat", show="•",
                 font=("Malgun Gothic", 9)).pack(side="left", padx=(4, 10))

        ttk.Button(obs_inner, text="🔌  OBS 연결", style="Blue.TButton",
                   command=self._obs_connect).pack(side="left", padx=(0, 8))
        ttk.Label(obs_inner,
                  text="OBS → 도구 → WebSocket 서버 설정 → 활성화 필요",
                  background=PANEL, foreground=TEXT,
                  font=("Malgun Gothic", 8, "italic")).pack(side="left")

        # ════════════════════════════════════════
        #  중단: 좌우 분할
        # ════════════════════════════════════════
        mid = ttk.Frame(parent)
        mid.pack(fill="both", expand=True)
        mid.columnconfigure(0, weight=1)
        mid.columnconfigure(1, weight=1)

        # ══ 왼쪽: OBS 녹화 컨트롤 ══
        left = ttk.Frame(mid, style="Panel.TFrame")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 1))

        ttk.Label(left, text="  🎙 OBS 녹화 컨트롤",
                  background=PANEL, foreground=GOLD,
                  font=("Malgun Gothic", 11, "bold")).pack(anchor="w",
                  padx=12, pady=(10, 6))

        # 씬 선택
        scene_row = ttk.Frame(left, style="Panel.TFrame")
        scene_row.pack(fill="x", padx=12, pady=(0, 6))
        ttk.Label(scene_row, text="씬:", background=PANEL,
                  foreground=TEXT, font=("Malgun Gothic", 10)).pack(side="left", padx=(0, 8))
        self.obs_scene_var = tk.StringVar(value="–")
        self.obs_scene_cb  = ttk.Combobox(scene_row, textvariable=self.obs_scene_var,
                                           state="readonly", width=22)
        self.obs_scene_cb.pack(side="left", padx=(0, 8))
        ttk.Button(scene_row, text="🔄", style="Blue.TButton",
                   command=self._obs_refresh_scenes).pack(side="left")

        # 녹화 상태
        rec_status_row = ttk.Frame(left, style="Panel.TFrame")
        rec_status_row.pack(fill="x", padx=12, pady=(0, 10))
        self.obs_rec_dot = tk.Label(rec_status_row, text="●", fg=TEXT,
                                     bg=PANEL, font=("Malgun Gothic", 12))
        self.obs_rec_dot.pack(side="left", padx=(0, 5))
        self.obs_rec_var = tk.StringVar(value="녹화 중지 상태")
        ttk.Label(rec_status_row, textvariable=self.obs_rec_var,
                  background=PANEL, foreground=TEXT,
                  font=("Malgun Gothic", 10)).pack(side="left")

        # 녹화 버튼
        rec_btns = ttk.Frame(left, style="Panel.TFrame")
        rec_btns.pack(fill="x", padx=12, pady=(0, 10))
        self.obs_rec_btn = ttk.Button(rec_btns, text="⏺  녹화 시작",
                                       style="Gold.TButton",
                                       command=self._obs_start_rec)
        self.obs_rec_btn.pack(side="left", padx=(0, 8))
        self.obs_stop_btn = ttk.Button(rec_btns, text="⏹  녹화 중지",
                                        style="Stop.TButton",
                                        command=self._obs_stop_rec,
                                        state="disabled")
        self.obs_stop_btn.pack(side="left")

        # 자동 녹화 (시퀀스 실행에 연동)
        ttk.Label(left, text="  ─── 자동화 옵션 ───",
                  background=PANEL, foreground=GOLD,
                  font=("Malgun Gothic", 9, "bold")).pack(anchor="w", padx=12, pady=(4, 4))

        self.obs_auto_rec_var = tk.BooleanVar(value=True)
        tk.Checkbutton(left,
                       text="카메라 시퀀스 실행 시 녹화 자동 시작/종료",
                       variable=self.obs_auto_rec_var,
                       bg=PANEL, fg=TEXT, selectcolor=PANEL2,
                       activebackground=PANEL, activeforeground=GOLD,
                       font=("Malgun Gothic", 10)).pack(anchor="w", padx=12)

        self.obs_auto_scene_var = tk.BooleanVar(value=False)
        tk.Checkbutton(left,
                       text="녹화 전 씬 자동 전환",
                       variable=self.obs_auto_scene_var,
                       bg=PANEL, fg=TEXT, selectcolor=PANEL2,
                       activebackground=PANEL, activeforeground=GOLD,
                       font=("Malgun Gothic", 10)).pack(anchor="w", padx=12)

        # 딜레이
        delay_row = ttk.Frame(left, style="Panel.TFrame")
        delay_row.pack(fill="x", padx=12, pady=(6, 0))
        ttk.Label(delay_row, text="녹화 시작 전 대기:", background=PANEL,
                  foreground=TEXT, font=("Malgun Gothic", 10)).pack(side="left", padx=(0, 8))
        self.obs_delay_var = tk.IntVar(value=2)
        tk.Spinbox(delay_row, from_=0, to=10, increment=1,
                   textvariable=self.obs_delay_var, width=4,
                   bg=PANEL2, fg=WHITE, buttonbackground=PANEL,
                   highlightthickness=0, relief="flat",
                   font=("Malgun Gothic", 10)).pack(side="left")
        ttk.Label(delay_row, text="초", background=PANEL,
                  foreground=TEXT, font=("Malgun Gothic", 10)).pack(side="left", padx=(4, 0))

        # ══ 오른쪽: FFmpeg 크롭 설정 ══
        right = ttk.Frame(mid)
        right.grid(row=0, column=1, sticky="nsew", padx=(1, 0))

        ttk.Label(right, text="  ✂ FFmpeg 9:16 크롭 & 내보내기",
                  background=PANEL, foreground=GOLD,
                  font=("Malgun Gothic", 11, "bold")).pack(anchor="w",
                  padx=12, pady=(10, 6))

        # FFmpeg 경로
        ffmpeg_row = ttk.Frame(right, style="Panel.TFrame")
        ffmpeg_row.pack(fill="x", padx=12, pady=(0, 6))
        ttk.Label(ffmpeg_row, text="FFmpeg 경로:", background=PANEL,
                  foreground=TEXT, font=("Malgun Gothic", 9)).pack(side="left", padx=(0, 8))
        self.ffmpeg_path_var = tk.StringVar(value="ffmpeg")
        tk.Entry(ffmpeg_row, textvariable=self.ffmpeg_path_var, width=22,
                 bg=PANEL2, fg=WHITE, insertbackground=GOLD,
                 highlightthickness=0, relief="flat",
                 font=("Malgun Gothic", 9)).pack(side="left", padx=(0, 6))
        ttk.Button(ffmpeg_row, text="📂", style="Blue.TButton",
                   command=self._pick_ffmpeg).pack(side="left")

        # 입력/출력 파일
        for label, attr, btn_text in [
            ("입력 영상:", "ffmpeg_input_var",  "📂 선택"),
            ("출력 경로:", "ffmpeg_output_var", "📂 선택"),
        ]:
            row = ttk.Frame(right, style="Panel.TFrame")
            row.pack(fill="x", padx=12, pady=(0, 5))
            ttk.Label(row, text=label, background=PANEL,
                      foreground=TEXT, font=("Malgun Gothic", 9),
                      width=9).pack(side="left", padx=(0, 6))
            var = tk.StringVar()
            setattr(self, attr, var)
            tk.Entry(row, textvariable=var, width=26,
                     bg=PANEL2, fg=WHITE, insertbackground=GOLD,
                     highlightthickness=0, relief="flat",
                     font=("Malgun Gothic", 9)).pack(side="left", padx=(0, 5))
            is_output = (attr == "ffmpeg_output_var")
            ttk.Button(row, text=btn_text, style="Blue.TButton",
                       command=(self._pick_output if is_output else self._pick_input)
                       ).pack(side="left")

        # 크롭 설정
        crop_card = ttk.Frame(right, style="Panel.TFrame", padding=8)
        crop_card.pack(fill="x", padx=12, pady=(4, 4))
        ttk.Label(crop_card, text="크롭 설정",
                  background=PANEL, foreground=GOLD,
                  font=("Malgun Gothic", 10, "bold")).pack(anchor="w", pady=(0, 6))

        # 프리셋 버튼
        crop_presets_row = ttk.Frame(crop_card, style="Panel.TFrame")
        crop_presets_row.pack(fill="x", pady=(0, 6))
        ttk.Label(crop_presets_row, text="빠른 설정:",
                  background=PANEL, foreground=TEXT,
                  font=("Malgun Gothic", 9)).pack(side="left", padx=(0, 8))
        for label, vals in [
            ("1080×1920", (1080, 1920, "center")),
            ("720×1280",  (720,  1280, "center")),
            ("608×1080",  (608,  1080, "center")),
        ]:
            ttk.Button(crop_presets_row, text=label, style="Purple.TButton",
                       command=lambda v=vals: self._apply_crop_preset(*v)
                       ).pack(side="left", padx=(0, 4))

        # 수동 크롭 값
        crop_vals_row = ttk.Frame(crop_card, style="Panel.TFrame")
        crop_vals_row.pack(fill="x")
        self.crop_w_var   = tk.StringVar(value="1080")
        self.crop_h_var   = tk.StringVar(value="1920")
        self.crop_x_var   = tk.StringVar(value="420")   # (1920-1080)/2
        self.crop_y_var   = tk.StringVar(value="0")
        self.scale_w_var  = tk.StringVar(value="1080")
        self.scale_h_var  = tk.StringVar(value="1920")

        for label, var in [
            ("크롭 W", self.crop_w_var), ("H", self.crop_h_var),
            ("X", self.crop_x_var),     ("Y", self.crop_y_var),
        ]:
            ttk.Label(crop_vals_row, text=f"  {label}:", background=PANEL,
                      foreground=TEXT, font=("Malgun Gothic", 9)).pack(side="left")
            tk.Entry(crop_vals_row, textvariable=var, width=5,
                     bg=PANEL2, fg=WHITE, insertbackground=GOLD,
                     highlightthickness=0, relief="flat",
                     font=("Malgun Gothic", 9)).pack(side="left", padx=(2, 0))

        scale_row = ttk.Frame(crop_card, style="Panel.TFrame")
        scale_row.pack(fill="x", pady=(4, 0))
        ttk.Label(scale_row, text="출력 스케일:", background=PANEL,
                  foreground=TEXT, font=("Malgun Gothic", 9)).pack(side="left")
        for label, var in [("W", self.scale_w_var), ("H", self.scale_h_var)]:
            ttk.Label(scale_row, text=f"  {label}:", background=PANEL,
                      foreground=TEXT, font=("Malgun Gothic", 9)).pack(side="left")
            tk.Entry(scale_row, textvariable=var, width=5,
                     bg=PANEL2, fg=WHITE, insertbackground=GOLD,
                     highlightthickness=0, relief="flat",
                     font=("Malgun Gothic", 9)).pack(side="left", padx=(2, 0))

        # 추가 옵션
        opts_row = ttk.Frame(right, style="Panel.TFrame")
        opts_row.pack(fill="x", padx=12, pady=(0, 4))
        self.ffmpeg_crf_var   = tk.StringVar(value="18")
        self.ffmpeg_codec_var = tk.StringVar(value="libx264")
        for label, var, opts, w in [
            ("코덱",  self.ffmpeg_codec_var,
             ["libx264", "libx265", "h264_nvenc", "hevc_nvenc"], 14),
            ("CRF",   self.ffmpeg_crf_var, None, 5),
        ]:
            ttk.Label(opts_row, text=f"  {label}:", background=PANEL,
                      foreground=TEXT, font=("Malgun Gothic", 9)).pack(side="left")
            if opts:
                ttk.Combobox(opts_row, textvariable=var, values=opts,
                             state="readonly", width=w).pack(side="left", padx=(4, 0))
            else:
                tk.Entry(opts_row, textvariable=var, width=w,
                         bg=PANEL2, fg=WHITE, insertbackground=GOLD,
                         highlightthickness=0, relief="flat",
                         font=("Malgun Gothic", 9)).pack(side="left", padx=(4, 0))

        # ── 워터마크 설정 ──────────────────────────────────
        wm_card = ttk.Frame(right, style="Panel.TFrame", padding=8)
        wm_card.pack(fill="x", padx=12, pady=(0, 4))

        wm_hdr = ttk.Frame(wm_card, style="Panel.TFrame")
        wm_hdr.pack(fill="x", pady=(0, 6))
        ttk.Label(wm_hdr, text="💧 워터마크",
                  background=PANEL, foreground=GOLD,
                  font=("Malgun Gothic", 10, "bold")).pack(side="left")
        self.wm_enabled_var = tk.BooleanVar(value=True)
        tk.Checkbutton(wm_hdr, text="사용",
                       variable=self.wm_enabled_var,
                       bg=PANEL, fg=TEXT, selectcolor=PANEL2,
                       activebackground=PANEL, activeforeground=GOLD,
                       font=("Malgun Gothic", 9),
                       command=self._toggle_wm_ui).pack(side="left", padx=(10, 0))

        # 워터마크 타입 선택
        wm_type_row = ttk.Frame(wm_card, style="Panel.TFrame")
        wm_type_row.pack(fill="x", pady=(0, 5))
        ttk.Label(wm_type_row, text="타입:", background=PANEL,
                  foreground=TEXT, font=("Malgun Gothic", 9)).pack(side="left", padx=(0, 8))
        self.wm_type_var = tk.StringVar(value="텍스트")
        for t in ["텍스트", "이미지"]:
            tk.Radiobutton(wm_type_row, text=t, variable=self.wm_type_var,
                           value=t, bg=PANEL, fg=TEXT, selectcolor=PANEL2,
                           activebackground=PANEL, activeforeground=GOLD,
                           font=("Malgun Gothic", 9),
                           command=self._toggle_wm_type).pack(side="left", padx=(0, 10))

        # 텍스트 워터마크 설정
        self.wm_text_frame = ttk.Frame(wm_card, style="Panel.TFrame")
        self.wm_text_frame.pack(fill="x", pady=(0, 4))

        wm_text_row = ttk.Frame(self.wm_text_frame, style="Panel.TFrame")
        wm_text_row.pack(fill="x", pady=(0, 3))
        ttk.Label(wm_text_row, text="텍스트:", background=PANEL,
                  foreground=TEXT, font=("Malgun Gothic", 9)).pack(side="left", padx=(0, 6))
        self.wm_text_var = tk.StringVar(value="@채널명")
        tk.Entry(wm_text_row, textvariable=self.wm_text_var, width=18,
                 bg=PANEL2, fg=WHITE, insertbackground=GOLD,
                 highlightthickness=0, relief="flat",
                 font=("Malgun Gothic", 10)).pack(side="left", padx=(0, 10))
        ttk.Label(wm_text_row, text="크기:", background=PANEL,
                  foreground=TEXT, font=("Malgun Gothic", 9)).pack(side="left", padx=(0, 4))
        self.wm_fontsize_var = tk.IntVar(value=42)
        tk.Spinbox(wm_text_row, from_=16, to=120, increment=2,
                   textvariable=self.wm_fontsize_var, width=5,
                   bg=PANEL2, fg=WHITE, buttonbackground=PANEL,
                   highlightthickness=0, relief="flat",
                   font=("Malgun Gothic", 9)).pack(side="left")

        wm_style_row = ttk.Frame(self.wm_text_frame, style="Panel.TFrame")
        wm_style_row.pack(fill="x", pady=(0, 3))
        ttk.Label(wm_style_row, text="색상:", background=PANEL,
                  foreground=TEXT, font=("Malgun Gothic", 9)).pack(side="left", padx=(0, 6))
        self.wm_color_var = tk.StringVar(value="white")
        ttk.Combobox(wm_style_row, textvariable=self.wm_color_var,
                     values=["white", "yellow", "gold", "cyan",
                             "red", "black", "0xC8AA6E"],
                     width=10, state="readonly").pack(side="left", padx=(0, 10))
        ttk.Label(wm_style_row, text="투명도(0~1):", background=PANEL,
                  foreground=TEXT, font=("Malgun Gothic", 9)).pack(side="left", padx=(0, 4))
        self.wm_alpha_var = tk.StringVar(value="0.7")
        tk.Entry(wm_style_row, textvariable=self.wm_alpha_var, width=5,
                 bg=PANEL2, fg=WHITE, insertbackground=GOLD,
                 highlightthickness=0, relief="flat",
                 font=("Malgun Gothic", 9)).pack(side="left")

        # 이미지 워터마크 설정
        self.wm_img_frame = ttk.Frame(wm_card, style="Panel.TFrame")
        # 기본은 숨김 (텍스트 타입이 기본)

        wm_img_row = ttk.Frame(self.wm_img_frame, style="Panel.TFrame")
        wm_img_row.pack(fill="x", pady=(0, 3))
        ttk.Label(wm_img_row, text="이미지:", background=PANEL,
                  foreground=TEXT, font=("Malgun Gothic", 9)).pack(side="left", padx=(0, 6))
        self.wm_img_var = tk.StringVar()
        tk.Entry(wm_img_row, textvariable=self.wm_img_var, width=22,
                 bg=PANEL2, fg=WHITE, insertbackground=GOLD,
                 highlightthickness=0, relief="flat",
                 font=("Malgun Gothic", 9)).pack(side="left", padx=(0, 4))
        ttk.Button(wm_img_row, text="📂", style="Blue.TButton",
                   command=self._pick_wm_image).pack(side="left", padx=(0, 8))
        ttk.Label(wm_img_row, text="스케일:", background=PANEL,
                  foreground=TEXT, font=("Malgun Gothic", 9)).pack(side="left", padx=(0, 4))
        self.wm_img_scale_var = tk.StringVar(value="0.15")
        tk.Entry(wm_img_row, textvariable=self.wm_img_scale_var, width=5,
                 bg=PANEL2, fg=WHITE, insertbackground=GOLD,
                 highlightthickness=0, relief="flat",
                 font=("Malgun Gothic", 9)).pack(side="left")
        ttk.Label(wm_img_row, text=" (0.1=10%)", background=PANEL,
                  foreground=TEXT, font=("Malgun Gothic", 8, "italic")).pack(side="left")

        # 공통 위치 설정
        wm_pos_row = ttk.Frame(wm_card, style="Panel.TFrame")
        wm_pos_row.pack(fill="x", pady=(4, 0))
        ttk.Label(wm_pos_row, text="위치:", background=PANEL,
                  foreground=TEXT, font=("Malgun Gothic", 9)).pack(side="left", padx=(0, 8))
        self.wm_pos_var = tk.StringVar(value="우하단")
        for pos in ["좌상단", "우상단", "좌하단", "우하단", "중앙하단"]:
            ttk.Button(wm_pos_row, text=pos,
                       style="Purple.TButton",
                       command=lambda p=pos: self.wm_pos_var.set(p)
                       ).pack(side="left", padx=(0, 3))

        # 현재 선택 위치 표시
        wm_pos_cur = ttk.Frame(wm_card, style="Panel.TFrame")
        wm_pos_cur.pack(fill="x", pady=(3, 0))
        ttk.Label(wm_pos_cur, text="선택:", background=PANEL,
                  foreground=TEXT, font=("Malgun Gothic", 9)).pack(side="left", padx=(0, 6))
        ttk.Label(wm_pos_cur, textvariable=self.wm_pos_var,
                  background=PANEL, foreground=GOLD,
                  font=("Malgun Gothic", 10, "bold")).pack(side="left", padx=(0, 14))

        # 여백 설정
        ttk.Label(wm_pos_cur, text="여백(px):", background=PANEL,
                  foreground=TEXT, font=("Malgun Gothic", 9)).pack(side="left", padx=(0, 4))
        self.wm_margin_var = tk.IntVar(value=30)
        tk.Spinbox(wm_pos_cur, from_=0, to=200, increment=5,
                   textvariable=self.wm_margin_var, width=5,
                   bg=PANEL2, fg=WHITE, buttonbackground=PANEL,
                   highlightthickness=0, relief="flat",
                   font=("Malgun Gothic", 9)).pack(side="left")

        # 내보내기 버튼 + 진행
        export_btn_row = ttk.Frame(right, style="Panel.TFrame")
        export_btn_row.pack(fill="x", padx=12, pady=(6, 4))
        self.export_btn = ttk.Button(export_btn_row, text="🎬  9:16 크롭 & 내보내기",
                                      style="Gold.TButton",
                                      command=self._run_ffmpeg_export)
        self.export_btn.pack(side="left", padx=(0, 10))
        ttk.Button(export_btn_row, text="📋  FFmpeg 명령 복사",
                   style="Blue.TButton",
                   command=self._copy_ffmpeg_cmd).pack(side="left")

        self.export_status_var = tk.StringVar(value="대기 중")
        self.export_prog_var   = tk.DoubleVar(value=0)
        ttk.Label(right, textvariable=self.export_status_var,
                  background=DARK, foreground=BLUE,
                  font=("Malgun Gothic", 9)).pack(anchor="w", padx=12, pady=(2, 2))
        ttk.Progressbar(right, variable=self.export_prog_var,
                        style="Gold.Horizontal.TProgressbar",
                        mode="determinate", length=320).pack(anchor="w", padx=12)

    # ── OBS 메서드 ──────────────────────────────
    def _obs_connect(self):
        def _do():
            self.after(0, lambda: (
                self.obs_dot.config(fg=ORANGE),
                self.obs_status_var.set("연결 중…")
            ))
            ok = self._obs.connect(
                host=self.obs_host_var.get(),
                port=int(self.obs_port_var.get()),
                password=self.obs_pw_var.get())
            if ok:
                self.after(0, lambda: (
                    self.obs_dot.config(fg=GREEN),
                    self.obs_status_var.set("OBS 연결됨 ✅")
                ))
                self._log("[OBS] 연결 성공", "ok")
                self.after(0, self._obs_refresh_scenes)
                self.after(0, self._obs_poll_rec)
            else:
                self.after(0, lambda: (
                    self.obs_dot.config(fg=RED),
                    self.obs_status_var.set("연결 실패 — OBS WebSocket 활성화 확인")
                ))
                self._log("[OBS] 연결 실패", "error")
        threading.Thread(target=_do, daemon=True).start()

    def _obs_refresh_scenes(self):
        if not self._obs.connected: return
        def _do():
            try:
                scenes = self._obs.get_scene_list()
                names  = [s.get("sceneName", "") for s in scenes]
                self.after(0, lambda n=names: (
                    self.obs_scene_cb.config(values=n),
                    self.obs_scene_var.set(n[0] if n else "–")
                ))
            except Exception as e:
                self._log(f"[OBS] 씬 목록 오류: {e}", "error")
        threading.Thread(target=_do, daemon=True).start()

    def _obs_poll_rec(self):
        """녹화 상태 1초마다 폴링."""
        if not self._obs.connected: return
        try:
            st = self._obs.get_record_status()
            active = st.get("responseData", {}).get("outputActive", False)
            if active:
                self.obs_rec_dot.config(fg=RED)
                self.obs_rec_var.set("🔴  녹화 중")
                self.obs_rec_btn.config(state="disabled")
                self.obs_stop_btn.config(state="normal")
            else:
                self.obs_rec_dot.config(fg=TEXT)
                self.obs_rec_var.set("녹화 중지 상태")
                self.obs_rec_btn.config(state="normal")
                self.obs_stop_btn.config(state="disabled")
        except Exception:
            pass
        self.after(1000, self._obs_poll_rec)

    def _obs_start_rec(self):
        if not self._obs.connected:
            messagebox.showwarning("연결 필요", "OBS에 먼저 연결하세요.")
            return
        def _do():
            try:
                self._obs.start_recording()
                self._log("[OBS] 녹화 시작", "ok")
            except Exception as e:
                self._log(f"[OBS] 녹화 시작 오류: {e}", "error")
        threading.Thread(target=_do, daemon=True).start()

    def _obs_stop_rec(self):
        if not self._obs.connected: return
        def _do():
            try:
                self._obs.stop_recording()
                self._log("[OBS] 녹화 중지", "warn")
            except Exception as e:
                self._log(f"[OBS] 녹화 중지 오류: {e}", "error")
        threading.Thread(target=_do, daemon=True).start()

    # ── FFmpeg 크롭 메서드 ──────────────────────
    def _apply_crop_preset(self, w: int, h: int, align: str):
        """크롭 프리셋 적용. 입력 해상도 1920×1080 기준."""
        src_w, src_h = 1920, 1080
        x = (src_w - w) // 2 if align == "center" else 0
        y = (src_h - h) // 2 if align == "center" else 0
        self.crop_w_var.set(str(w))
        self.crop_h_var.set(str(h))
        self.crop_x_var.set(str(x))
        self.crop_y_var.set(str(y))
        self.scale_w_var.set(str(w))
        self.scale_h_var.set(str(h))

    def _pick_ffmpeg(self):
        p = filedialog.askopenfilename(
            title="ffmpeg 실행 파일 선택",
            filetypes=[("실행 파일", "*.exe ffmpeg"), ("모든 파일", "*.*")])
        if p: self.ffmpeg_path_var.set(p)

    def _pick_input(self):
        p = filedialog.askopenfilename(
            title="입력 영상 선택",
            filetypes=[("영상 파일", "*.mp4 *.mkv *.avi *.mov"), ("모든 파일", "*.*")])
        if p: self.ffmpeg_input_var.set(p)

    def _pick_output(self):
        p = filedialog.asksaveasfilename(
            title="출력 파일 저장",
            defaultextension=".mp4",
            filetypes=[("MP4", "*.mp4"), ("MKV", "*.mkv")])
        if p: self.ffmpeg_output_var.set(p)

    # ── 워터마크 UI 토글 ────────────────────────
    def _toggle_wm_ui(self):
        """워터마크 활성/비활성 시 관련 위젯 상태 토글."""
        state = "normal" if self.wm_enabled_var.get() else "disabled"
        for child in self.wm_text_frame.winfo_children():
            for w in child.winfo_children():
                try: w.config(state=state)
                except: pass

    def _toggle_wm_type(self):
        """텍스트 ↔ 이미지 타입 전환."""
        if self.wm_type_var.get() == "텍스트":
            self.wm_img_frame.pack_forget()
            self.wm_text_frame.pack(fill="x", pady=(0, 4),
                                     before=self.wm_img_frame)
        else:
            self.wm_text_frame.pack_forget()
            self.wm_img_frame.pack(fill="x", pady=(0, 4))

    def _pick_wm_image(self):
        p = filedialog.askopenfilename(
            title="워터마크 이미지 선택",
            filetypes=[("이미지", "*.png *.jpg *.jpeg *.gif"),
                       ("PNG (투명 지원)", "*.png"),
                       ("모든 파일", "*.*")])
        if p: self.wm_img_var.set(p)

    def _wm_position_expr(self, w_expr: str, h_expr: str) -> tuple[str, str]:
        """
        위치 이름 → FFmpeg x, y 표현식 반환.
        w_expr, h_expr: 워터마크 너비/높이 표현식
        """
        margin = self.wm_margin_var.get()
        pos    = self.wm_pos_var.get()
        positions = {
            "좌상단":   (f"{margin}",
                         f"{margin}"),
            "우상단":   (f"W-{w_expr}-{margin}",
                         f"{margin}"),
            "좌하단":   (f"{margin}",
                         f"H-{h_expr}-{margin}"),
            "우하단":   (f"W-{w_expr}-{margin}",
                         f"H-{h_expr}-{margin}"),
            "중앙하단": (f"(W-{w_expr})/2",
                         f"H-{h_expr}-{margin}"),
        }
        return positions.get(pos, positions["우하단"])

    def _build_ffmpeg_cmd(self) -> list:
        """FFmpeg 크롭 + 스케일 + 워터마크 명령 생성."""
        ffmpeg  = self.ffmpeg_path_var.get() or "ffmpeg"
        inp     = self.ffmpeg_input_var.get()
        out     = self.ffmpeg_output_var.get()
        cw, ch  = self.crop_w_var.get(),  self.crop_h_var.get()
        cx, cy  = self.crop_x_var.get(),  self.crop_y_var.get()
        sw, sh  = self.scale_w_var.get(), self.scale_h_var.get()
        codec   = self.ffmpeg_codec_var.get()
        crf     = self.ffmpeg_crf_var.get()

        # ── 기본 비디오 필터: 크롭 + 스케일 ──
        vf_parts = [f"crop={cw}:{ch}:{cx}:{cy}", f"scale={sw}:{sh}"]

        # ── 워터마크 필터 추가 ──
        use_wm    = hasattr(self, 'wm_enabled_var') and self.wm_enabled_var.get()
        wm_type   = self.wm_type_var.get() if hasattr(self, 'wm_type_var') else "텍스트"
        extra_inputs = []

        if use_wm:
            if wm_type == "텍스트":
                # drawtext 필터
                text   = self.wm_text_var.get().replace("'", "\\'").replace(":", "\\:")
                size   = self.wm_fontsize_var.get()
                color  = self.wm_color_var.get()
                alpha  = self.wm_alpha_var.get()
                margin = self.wm_margin_var.get()

                # 색상에 알파 적용 (FFmpeg drawtext 형식)
                # color@alpha 형식
                color_expr = f"{color}@{alpha}"

                # 위치 계산 (텍스트는 tw/th 사용)
                x_expr, y_expr = self._wm_position_expr("tw", "th")

                wm_filter = (
                    f"drawtext="
                    f"text='{text}':"
                    f"fontsize={size}:"
                    f"fontcolor={color_expr}:"
                    f"x={x_expr}:"
                    f"y={y_expr}:"
                    f"shadowcolor=black@0.5:"
                    f"shadowx=2:"
                    f"shadowy=2"
                )
                vf_parts.append(wm_filter)

            else:
                # 이미지 오버레이 (overlay 필터, 별도 -i 입력)
                img_path = self.wm_img_var.get()
                if not img_path or not os.path.exists(img_path):
                    messagebox.showwarning("이미지 없음",
                        "워터마크 이미지 파일을 선택해 주세요.")
                    raise ValueError("워터마크 이미지 없음")

                scale_ratio = self.wm_img_scale_var.get()
                extra_inputs = ["-i", img_path]

                # 이미지 스케일 → overlay 위치
                # scale2ref로 영상 크기 기준 비율 계산
                x_expr, y_expr = self._wm_position_expr("overlay_w", "overlay_h")
                vf_parts.append(
                    f"[0:v]scale={sw}:{sh}[base];"
                    f"[1:v]scale=iw*{scale_ratio}:-1[wm];"
                    f"[base][wm]overlay={x_expr}:{y_expr}"
                )
                # overlay는 복합 필터이므로 -vf 대신 -filter_complex 사용
                vf_str = ",".join(vf_parts[:-1])  # crop+scale
                overlay_filter = vf_parts[-1]      # overlay
                complex_filter = (
                    f"[0:v]crop={cw}:{ch}:{cx}:{cy},scale={sw}:{sh}[base];"
                    f"[1:v]scale=iw*{scale_ratio}:-1[wm];"
                    f"[base][wm]overlay={x_expr}:{y_expr}[out]"
                )
                return [
                    ffmpeg, "-y",
                    "-i", inp,
                    *extra_inputs,
                    "-filter_complex", complex_filter,
                    "-map", "[out]",
                    "-map", "0:a?",
                    "-c:v", codec,
                    "-crf", crf,
                    "-preset", "fast",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    "-movflags", "+faststart",
                    out
                ]

        vf = ",".join(vf_parts)
        return [
            ffmpeg, "-y", "-i", inp,
            "-vf", vf,
            "-c:v", codec,
            "-crf", crf,
            "-preset", "fast",
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
            out
        ]

    def _copy_ffmpeg_cmd(self):
        try:
            cmd = self._build_ffmpeg_cmd()
            self.clipboard_clear()
            self.clipboard_append(" ".join(
                f'"{c}"' if " " in c else c for c in cmd))
            messagebox.showinfo("복사 완료", "FFmpeg 명령이 클립보드에 복사됐어요!")
        except Exception as e:
            messagebox.showerror("오류", str(e))

    def _run_ffmpeg_export(self):
        inp = self.ffmpeg_input_var.get()
        out = self.ffmpeg_output_var.get()
        if not inp or not out:
            messagebox.showwarning("파일 필요", "입력/출력 경로를 모두 지정하세요.")
            return
        cmd = self._build_ffmpeg_cmd()
        self._log(f"[FFmpeg] 실행: {' '.join(cmd[:6])} …", "info")
        self.export_btn.config(state="disabled")
        self.export_status_var.set("FFmpeg 실행 중…")
        self.export_prog_var.set(0)
        threading.Thread(target=self._ffmpeg_worker, args=(cmd,), daemon=True).start()

    def _ffmpeg_worker(self, cmd: list):
        import subprocess, re
        try:
            proc = subprocess.Popen(
                cmd,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                encoding="utf-8", errors="replace"
            )
            duration_s = None
            for line in proc.stderr:
                # 총 재생 시간 파악
                m = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", line)
                if m and duration_s is None:
                    h, mi, s = int(m.group(1)), int(m.group(2)), float(m.group(3))
                    duration_s = h * 3600 + mi * 60 + s

                # 진행 시간
                m2 = re.search(r"time=(\d+):(\d+):([\d.]+)", line)
                if m2 and duration_s:
                    h, mi, s = int(m2.group(1)), int(m2.group(2)), float(m2.group(3))
                    elapsed = h * 3600 + mi * 60 + s
                    pct = min(elapsed / duration_s * 100, 99)
                    self.after(0, lambda p=pct, e=elapsed, d=duration_s: (
                        self.export_prog_var.set(p),
                        self.export_status_var.set(
                            f"처리 중… {e:.0f}s / {d:.0f}s  ({p:.0f}%)")
                    ))

            proc.wait()
            if proc.returncode == 0:
                self.after(0, lambda: (
                    self.export_prog_var.set(100),
                    self.export_status_var.set("✅ 내보내기 완료!")
                ))
                self._log(f"[FFmpeg] 내보내기 완료 → {cmd[-1]}", "ok")
            else:
                self.after(0, lambda: self.export_status_var.set("❌ FFmpeg 오류"))
                self._log(f"[FFmpeg] 오류 (코드 {proc.returncode})", "error")
        except FileNotFoundError:
            self.after(0, lambda: self.export_status_var.set("❌ ffmpeg 없음 — 경로 확인"))
            self._log("[FFmpeg] 실행 파일을 찾을 수 없습니다", "error")
        except Exception as e:
            self._log(f"[FFmpeg] 예외: {e}", "error")
        finally:
            self.after(0, lambda: self.export_btn.config(state="normal"))

    # ══════════════════════════════════════════════
    #  비트 싱크 편집기 탭
    # ══════════════════════════════════════════════
    def _build_beatsync_tab(self, parent):
        """
        librosa 로 음악 BPM & 비트 타임스탬프 분석 →
        킬 5개를 비트 5개에 1:1 매핑 →
        FFmpeg setpts 로 구간별 time-stretch →
        완성된 영상은 킬 순간이 비트에 정확히 일치
        """
        self._beats: list[float]   = []   # 분석된 비트 타임스탬프 (초)
        self._kill_ts: list[float] = []   # 킬 타임스탬프 (초, API에서 추출)
        self._beat_map: list[tuple] = []  # [(kill_ts, beat_ts), ...]

        # ── 상단 안내 ──
        info = ttk.Frame(parent, style="Panel.TFrame")
        info.pack(fill="x", pady=(0, 1))
        ttk.Label(info,
                  text="  음악의 비트 타임스탬프와 킬 타임스탬프를 1:1 매핑 → FFmpeg time-stretch로 프레임 단위 완벽 싱크",
                  background=PANEL, foreground=TEXT,
                  font=("Malgun Gothic", 9, "italic")).pack(side="left", pady=6, padx=4)

        # ── 3단 레이아웃 ──
        body = ttk.Frame(parent)
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)
        body.columnconfigure(2, weight=1)

        # ══ 1열: 음악 분석 ══
        col1 = ttk.Frame(body, style="Panel.TFrame")
        col1.grid(row=0, column=0, sticky="nsew", padx=(0, 1))

        ttk.Label(col1, text="  🎵 음악 분석",
                  background=PANEL, foreground=GOLD,
                  font=("Malgun Gothic", 11, "bold")).pack(anchor="w", padx=10, pady=(10, 6))

        # 음악 파일 선택
        mf_row = ttk.Frame(col1, style="Panel.TFrame")
        mf_row.pack(fill="x", padx=10, pady=(0, 6))
        self.music_path_var = tk.StringVar()
        tk.Entry(mf_row, textvariable=self.music_path_var, width=24,
                 bg=PANEL2, fg=WHITE, insertbackground=GOLD,
                 highlightthickness=0, relief="flat",
                 font=("Malgun Gothic", 9)).pack(side="left", padx=(0, 6))
        ttk.Button(mf_row, text="📂", style="Blue.TButton",
                   command=self._pick_music).pack(side="left")

        # BPM / 시작 비트 오프셋
        bpm_row = ttk.Frame(col1, style="Panel.TFrame")
        bpm_row.pack(fill="x", padx=10, pady=(0, 6))
        ttk.Label(bpm_row, text="BPM(자동):", background=PANEL,
                  foreground=TEXT, font=("Malgun Gothic", 9)).pack(side="left")
        self.bpm_var = tk.StringVar(value="–")
        ttk.Label(bpm_row, textvariable=self.bpm_var, background=PANEL,
                  foreground=GOLD, font=("Malgun Gothic", 10, "bold")).pack(side="left", padx=(4, 14))
        ttk.Label(bpm_row, text="시작 오프셋(초):", background=PANEL,
                  foreground=TEXT, font=("Malgun Gothic", 9)).pack(side="left")
        self.beat_offset_var = tk.StringVar(value="0.0")
        tk.Entry(bpm_row, textvariable=self.beat_offset_var, width=5,
                 bg=PANEL2, fg=WHITE, insertbackground=GOLD,
                 highlightthickness=0, relief="flat",
                 font=("Malgun Gothic", 9)).pack(side="left", padx=(4, 0))

        ttk.Button(col1, text="🔍  BPM & 비트 분석", style="Gold.TButton",
                   command=self._analyze_beats).pack(anchor="w", padx=10, pady=(0, 8))

        # 비트 목록
        ttk.Label(col1, text="감지된 비트 타임스탬프 (초)",
                  background=PANEL, foreground=TEXT,
                  font=("Malgun Gothic", 9)).pack(anchor="w", padx=10)

        self.beat_listbox = tk.Listbox(col1,
            bg=PANEL2, fg=TEXT, selectbackground=GOLD_D,
            font=("Consolas", 9), height=12,
            highlightthickness=0, relief="flat")
        beat_vsb = ttk.Scrollbar(col1, orient="vertical",
                                  command=self.beat_listbox.yview)
        self.beat_listbox.configure(yscrollcommand=beat_vsb.set)
        beat_vsb.pack(side="right", fill="y", padx=(0, 4))
        self.beat_listbox.pack(fill="both", expand=True, padx=(10, 0), pady=(2, 8))

        self.beat_status_var = tk.StringVar(value="음악 파일을 선택하세요")
        ttk.Label(col1, textvariable=self.beat_status_var,
                  background=PANEL, foreground=BLUE,
                  font=("Malgun Gothic", 9)).pack(anchor="w", padx=10, pady=(0, 6))

        # ══ 2열: 킬 타임스탬프 & 매핑 ══
        col2 = ttk.Frame(body, style="Panel.TFrame")
        col2.grid(row=0, column=1, sticky="nsew", padx=(1, 1))

        ttk.Label(col2, text="  ⚔ 킬 → 비트 매핑",
                  background=PANEL, foreground=GOLD,
                  font=("Malgun Gothic", 11, "bold")).pack(anchor="w", padx=10, pady=(10, 6))

        # 펜타킬 선택
        ttk.Label(col2, text="펜타킬 선택 (킬 타임스탬프 자동 입력):",
                  background=PANEL, foreground=TEXT,
                  font=("Malgun Gothic", 9)).pack(anchor="w", padx=10, pady=(0, 3))

        cols_bs = ("summoner", "champion", "game_time", "ts_sec")
        self.tree_bs_penta = ttk.Treeview(col2, columns=cols_bs,
                                           show="headings", height=5)
        for cid, hd, w in zip(cols_bs,
            ["소환사명", "챔피언", "시간", "타임스탬프(초)"],
            [120, 100, 70, 100]):
            self.tree_bs_penta.heading(cid, text=hd)
            self.tree_bs_penta.column(cid, width=w, anchor="center")
        self.tree_bs_penta.bind("<<TreeviewSelect>>", self._on_bs_penta_select)
        bs_vsb = ttk.Scrollbar(col2, orient="vertical",
                                command=self.tree_bs_penta.yview)
        self.tree_bs_penta.configure(yscrollcommand=bs_vsb.set)
        bs_vsb.pack(side="right", fill="y")
        self.tree_bs_penta.pack(fill="x", padx=(10, 0), pady=(0, 8))

        # 킬 타임스탬프 5개 편집
        ttk.Label(col2, text="킬 타임스탬프 (초, 자동 입력 or 수동 수정):",
                  background=PANEL, foreground=TEXT,
                  font=("Malgun Gothic", 9)).pack(anchor="w", padx=10, pady=(0, 3))

        self.kill_ts_vars = []
        for i in range(5):
            row = ttk.Frame(col2, style="Panel.TFrame")
            row.pack(fill="x", padx=10, pady=1)
            color = [TEXT, TEXT, ORANGE, GOLD, RED][i]
            ttk.Label(row, text=f"{'⚔'*(i+1)} {i+1}킬:",
                      background=PANEL, foreground=color,
                      font=("Malgun Gothic", 10, "bold"), width=8).pack(side="left")
            var = tk.StringVar(value="0.0")
            tk.Entry(row, textvariable=var, width=9,
                     bg=PANEL2, fg=color, insertbackground=GOLD,
                     highlightthickness=0, relief="flat",
                     font=("Malgun Gothic", 10)).pack(side="left", padx=(4, 0))
            self.kill_ts_vars.append(var)

        ttk.Label(col2, text="\n비트 타임스탬프 (목록에서 클릭하거나 수동 입력):",
                  background=PANEL, foreground=TEXT,
                  font=("Malgun Gothic", 9)).pack(anchor="w", padx=10, pady=(6, 3))

        self.beat_ts_vars = []
        for i in range(5):
            row = ttk.Frame(col2, style="Panel.TFrame")
            row.pack(fill="x", padx=10, pady=1)
            color = [TEXT, TEXT, ORANGE, GOLD, RED][i]
            ttk.Label(row, text=f"비트 {i+1}:",
                      background=PANEL, foreground=color,
                      font=("Malgun Gothic", 10), width=8).pack(side="left")
            var = tk.StringVar(value="0.0")
            tk.Entry(row, textvariable=var, width=9,
                     bg=PANEL2, fg=color, insertbackground=GOLD,
                     highlightthickness=0, relief="flat",
                     font=("Malgun Gothic", 10)).pack(side="left", padx=(4, 8))
            self.beat_ts_vars.append(var)

        # 자동 매핑 버튼
        ttk.Button(col2, text="🎯  비트 자동 배치 (간격 최적화)",
                   style="Blue.TButton",
                   command=self._auto_assign_beats).pack(anchor="w", padx=10, pady=(8, 4))

        # ── 목표 길이 자동 설정 ──────────────────────────────────
        tk.Canvas(col2, bg=GOLD_D, height=1,
                  highlightthickness=0).pack(fill="x", padx=10, pady=(8, 6))

        ttk.Label(col2, text="🎯 목표 영상 길이 자동 설정",
                  background=PANEL, foreground=GOLD,
                  font=("Malgun Gothic", 10, "bold")).pack(anchor="w", padx=10, pady=(0, 6))

        # 목표 길이 입력
        tl_row1 = ttk.Frame(col2, style="Panel.TFrame")
        tl_row1.pack(fill="x", padx=10, pady=(0, 4))
        ttk.Label(tl_row1, text="목표 길이:", background=PANEL,
                  foreground=TEXT, font=("Malgun Gothic", 9)).pack(side="left", padx=(0, 6))
        self.target_len_var = tk.IntVar(value=45)
        tk.Spinbox(tl_row1, from_=15, to=180, increment=5,
                   textvariable=self.target_len_var, width=5,
                   bg=PANEL2, fg=WHITE, buttonbackground=PANEL,
                   highlightthickness=0, relief="flat",
                   font=("Malgun Gothic", 10)).pack(side="left", padx=(0, 4))
        ttk.Label(tl_row1, text="초", background=PANEL,
                  foreground=TEXT, font=("Malgun Gothic", 9)).pack(side="left", padx=(0, 16))

        # 빠른 선택 버튼
        for sec in [30, 45, 60]:
            ttk.Button(tl_row1, text=f"{sec}초",
                       style="Purple.TButton",
                       command=lambda s=sec: self.target_len_var.set(s)
                       ).pack(side="left", padx=(0, 3))

        # 인트로/아웃트로 설정
        tl_row2 = ttk.Frame(col2, style="Panel.TFrame")
        tl_row2.pack(fill="x", padx=10, pady=(0, 4))
        ttk.Label(tl_row2, text="인트로:", background=PANEL,
                  foreground=TEXT, font=("Malgun Gothic", 9)).pack(side="left", padx=(0, 4))
        self.tl_intro_var = tk.IntVar(value=8)
        tk.Spinbox(tl_row2, from_=0, to=30, increment=1,
                   textvariable=self.tl_intro_var, width=4,
                   bg=PANEL2, fg=WHITE, buttonbackground=PANEL,
                   highlightthickness=0, relief="flat",
                   font=("Malgun Gothic", 9)).pack(side="left", padx=(0, 10))
        ttk.Label(tl_row2, text="아웃트로:", background=PANEL,
                  foreground=TEXT, font=("Malgun Gothic", 9)).pack(side="left", padx=(0, 4))
        self.tl_outro_var = tk.IntVar(value=5)
        tk.Spinbox(tl_row2, from_=0, to=30, increment=1,
                   textvariable=self.tl_outro_var, width=4,
                   bg=PANEL2, fg=WHITE, buttonbackground=PANEL,
                   highlightthickness=0, relief="flat",
                   font=("Malgun Gothic", 9)).pack(side="left", padx=(0, 10))
        ttk.Label(tl_row2, text="초", background=PANEL,
                  foreground=TEXT, font=("Malgun Gothic", 9)).pack(side="left")

        # 펜타킬 비트 배수
        tl_row3 = ttk.Frame(col2, style="Panel.TFrame")
        tl_row3.pack(fill="x", padx=10, pady=(0, 6))
        ttk.Label(tl_row3, text="펜타킬 비트 배수:", background=PANEL,
                  foreground=TEXT, font=("Malgun Gothic", 9)).pack(side="left", padx=(0, 6))
        self.penta_beat_mult_var = tk.IntVar(value=2)
        ttk.Combobox(tl_row3, textvariable=self.penta_beat_mult_var,
                     values=[1, 2, 3, 4], state="readonly",
                     width=4).pack(side="left", padx=(0, 8))
        ttk.Label(tl_row3,
                  text="배  (펜타킬 확정 순간을 다른 킬보다 길게)",
                  background=PANEL, foreground=TEXT,
                  font=("Malgun Gothic", 8, "italic")).pack(side="left")

        # 자동 계산 버튼
        ttk.Button(col2, text="⚡  목표 길이로 비트 자동 계산 & 배치",
                   style="Gold.TButton",
                   command=self._auto_assign_beats_by_length
                   ).pack(anchor="w", padx=10, pady=(0, 6))

        # 계산 결과 요약
        self.tl_result_var = tk.StringVar(value="")
        ttk.Label(col2, textvariable=self.tl_result_var,
                  background=PANEL, foreground=CYAN,
                  font=("Consolas", 8), wraplength=260,
                  justify="left").pack(anchor="w", padx=10, pady=(0, 4))

        # 매핑 미리보기
        self.mapping_preview_var = tk.StringVar(value="매핑 결과가 여기 표시됩니다")
        ttk.Label(col2, textvariable=self.mapping_preview_var,
                  background=PANEL, foreground=CYAN,
                  font=("Consolas", 8), wraplength=260,
                  justify="left").pack(anchor="w", padx=10, pady=(4, 0))

        # ══ 3열: FFmpeg 렌더링 ══
        col3 = ttk.Frame(body)
        col3.grid(row=0, column=2, sticky="nsew", padx=(1, 0))

        ttk.Label(col3, text="  🎬 time-stretch 렌더링",
                  background=PANEL, foreground=GOLD,
                  font=("Malgun Gothic", 11, "bold")).pack(anchor="w", padx=10, pady=(10, 6))

        # 입출력
        for label, attr, cmd in [
            ("원본 영상:", "bs_input_var",  self._bs_pick_input),
            ("음악 파일:", "bs_music_var",  self._bs_pick_music),
            ("출력 파일:", "bs_output_var", self._bs_pick_output),
        ]:
            fr = ttk.Frame(col3, style="Panel.TFrame")
            fr.pack(fill="x", padx=10, pady=(0, 4))
            ttk.Label(fr, text=label, background=PANEL,
                      foreground=TEXT, font=("Malgun Gothic", 9),
                      width=9).pack(side="left")
            var = tk.StringVar()
            setattr(self, attr, var)
            tk.Entry(fr, textvariable=var, width=22,
                     bg=PANEL2, fg=WHITE, insertbackground=GOLD,
                     highlightthickness=0, relief="flat",
                     font=("Malgun Gothic", 9)).pack(side="left", padx=(4, 4))
            ttk.Button(fr, text="📂", style="Blue.TButton",
                       command=cmd).pack(side="left")

        # 옵션
        opt_card = ttk.Frame(col3, style="Panel.TFrame", padding=8)
        opt_card.pack(fill="x", padx=10, pady=(4, 4))
        ttk.Label(opt_card, text="렌더 옵션",
                  background=PANEL, foreground=GOLD,
                  font=("Malgun Gothic", 10, "bold")).pack(anchor="w", pady=(0, 4))

        self.bs_interp_var = tk.BooleanVar(value=True)
        tk.Checkbutton(opt_card,
                       text="minterpolate 프레임 보간 (슬로우모션 부드럽게)",
                       variable=self.bs_interp_var,
                       bg=PANEL, fg=TEXT, selectcolor=PANEL2,
                       activebackground=PANEL, activeforeground=GOLD,
                       font=("Malgun Gothic", 9)).pack(anchor="w")

        self.bs_crop916_var = tk.BooleanVar(value=True)
        tk.Checkbutton(opt_card,
                       text="9:16 크롭 동시 적용 (쇼츠 즉시 출력)",
                       variable=self.bs_crop916_var,
                       bg=PANEL, fg=TEXT, selectcolor=PANEL2,
                       activebackground=PANEL, activeforeground=GOLD,
                       font=("Malgun Gothic", 9)).pack(anchor="w")

        self.bs_fade_var = tk.BooleanVar(value=True)
        tk.Checkbutton(opt_card,
                       text="페이드인/아웃 (0.3초)",
                       variable=self.bs_fade_var,
                       bg=PANEL, fg=TEXT, selectcolor=PANEL2,
                       activebackground=PANEL, activeforeground=GOLD,
                       font=("Malgun Gothic", 9)).pack(anchor="w")

        # ── 타격감 효과 ───────────────────────────────────
        tk.Canvas(opt_card, bg=GOLD_D, height=1,
                  highlightthickness=0).pack(fill="x", pady=(8, 6))
        ttk.Label(opt_card, text="⚡ 타격감 효과",
                  background=PANEL, foreground=GOLD,
                  font=("Malgun Gothic", 10, "bold")).pack(anchor="w", pady=(0, 5))

        # 슬로우 예비 동작
        self.bs_preslow_var = tk.BooleanVar(value=True)
        tk.Checkbutton(opt_card,
                       text="킬 직전 슬로우 예비동작 (비트 임팩트 극대화)",
                       variable=self.bs_preslow_var,
                       bg=PANEL, fg=TEXT, selectcolor=PANEL2,
                       activebackground=PANEL, activeforeground=GOLD,
                       font=("Malgun Gothic", 9)).pack(anchor="w")

        # 슬로우 세부 설정
        preslow_detail = ttk.Frame(opt_card, style="Panel.TFrame")
        preslow_detail.pack(fill="x", padx=16, pady=(2, 6))

        ttk.Label(preslow_detail, text="슬로우 구간:",
                  background=PANEL, foreground=TEXT,
                  font=("Malgun Gothic", 8)).pack(side="left", padx=(0, 4))
        self.bs_preslow_dur_var = tk.DoubleVar(value=0.5)
        tk.Spinbox(preslow_detail, from_=0.1, to=1.5, increment=0.1,
                   textvariable=self.bs_preslow_dur_var, width=4,
                   bg=PANEL2, fg=WHITE, buttonbackground=PANEL,
                   highlightthickness=0, relief="flat",
                   font=("Malgun Gothic", 8), format="%.1f").pack(side="left", padx=(0, 8))
        ttk.Label(preslow_detail, text="초  |  슬로우 배속:",
                  background=PANEL, foreground=TEXT,
                  font=("Malgun Gothic", 8)).pack(side="left", padx=(0, 4))
        self.bs_preslow_speed_var = tk.DoubleVar(value=0.5)
        tk.Spinbox(preslow_detail, from_=0.1, to=0.9, increment=0.1,
                   textvariable=self.bs_preslow_speed_var, width=4,
                   bg=PANEL2, fg=WHITE, buttonbackground=PANEL,
                   highlightthickness=0, relief="flat",
                   font=("Malgun Gothic", 8), format="%.1f").pack(side="left", padx=(0, 6))
        ttk.Label(preslow_detail,
                  text="× (0.5 추천)",
                  background=PANEL, foreground=TEXT,
                  font=("Malgun Gothic", 8, "italic")).pack(side="left")

        # 화면 흔들림
        self.bs_shake_var = tk.BooleanVar(value=True)
        tk.Checkbutton(opt_card,
                       text="화면 흔들림 Screen Shake (킬 순간 타격감)",
                       variable=self.bs_shake_var,
                       bg=PANEL, fg=TEXT, selectcolor=PANEL2,
                       activebackground=PANEL, activeforeground=GOLD,
                       font=("Malgun Gothic", 9)).pack(anchor="w")

        # 흔들림 세부 설정
        shake_detail = ttk.Frame(opt_card, style="Panel.TFrame")
        shake_detail.pack(fill="x", padx=16, pady=(2, 4))

        ttk.Label(shake_detail, text="흔들림 강도(px):",
                  background=PANEL, foreground=TEXT,
                  font=("Malgun Gothic", 8)).pack(side="left", padx=(0, 4))
        self.bs_shake_px_var = tk.IntVar(value=5)
        tk.Spinbox(shake_detail, from_=1, to=20, increment=1,
                   textvariable=self.bs_shake_px_var, width=4,
                   bg=PANEL2, fg=WHITE, buttonbackground=PANEL,
                   highlightthickness=0, relief="flat",
                   font=("Malgun Gothic", 8)).pack(side="left", padx=(0, 8))
        ttk.Label(shake_detail, text="지속 시간:",
                  background=PANEL, foreground=TEXT,
                  font=("Malgun Gothic", 8)).pack(side="left", padx=(0, 4))
        self.bs_shake_dur_var = tk.DoubleVar(value=0.3)
        tk.Spinbox(shake_detail, from_=0.1, to=1.0, increment=0.1,
                   textvariable=self.bs_shake_dur_var, width=4,
                   bg=PANEL2, fg=WHITE, buttonbackground=PANEL,
                   highlightthickness=0, relief="flat",
                   font=("Malgun Gothic", 8), format="%.1f").pack(side="left", padx=(0, 6))
        ttk.Label(shake_detail, text="초  (MoviePy 필요)",
                  background=PANEL, foreground=ORANGE,
                  font=("Malgun Gothic", 8, "italic")).pack(side="left")

        # ── 줌인 펀치 ──
        self.bs_zoom_var = tk.BooleanVar(value=True)
        tk.Checkbutton(opt_card,
                       text="줌인 펀치 Zoom Punch (킬 순간 화면 순간 확대)",
                       variable=self.bs_zoom_var,
                       bg=PANEL, fg=TEXT, selectcolor=PANEL2,
                       activebackground=PANEL, activeforeground=GOLD,
                       font=("Malgun Gothic", 9)).pack(anchor="w")

        zoom_detail = ttk.Frame(opt_card, style="Panel.TFrame")
        zoom_detail.pack(fill="x", padx=16, pady=(2, 6))
        ttk.Label(zoom_detail, text="최대 줌:",
                  background=PANEL, foreground=TEXT,
                  font=("Malgun Gothic", 8)).pack(side="left", padx=(0, 4))
        self.bs_zoom_scale_var = tk.DoubleVar(value=1.06)
        tk.Spinbox(zoom_detail, from_=1.01, to=1.2, increment=0.01,
                   textvariable=self.bs_zoom_scale_var, width=5,
                   bg=PANEL2, fg=WHITE, buttonbackground=PANEL,
                   highlightthickness=0, relief="flat",
                   font=("Malgun Gothic", 8), format="%.2f").pack(side="left", padx=(0, 8))
        ttk.Label(zoom_detail, text="지속:",
                  background=PANEL, foreground=TEXT,
                  font=("Malgun Gothic", 8)).pack(side="left", padx=(0, 4))
        self.bs_zoom_dur_var = tk.DoubleVar(value=0.15)
        tk.Spinbox(zoom_detail, from_=0.05, to=0.5, increment=0.05,
                   textvariable=self.bs_zoom_dur_var, width=5,
                   bg=PANEL2, fg=WHITE, buttonbackground=PANEL,
                   highlightthickness=0, relief="flat",
                   font=("Malgun Gothic", 8), format="%.2f").pack(side="left", padx=(0, 6))
        ttk.Label(zoom_detail, text="초  (1.06 × 0.15s 추천)",
                  background=PANEL, foreground=TEXT,
                  font=("Malgun Gothic", 8, "italic")).pack(side="left")

        # ── 킬 카운터 오버레이 ──
        self.bs_killcounter_var = tk.BooleanVar(value=True)
        tk.Checkbutton(opt_card,
                       text="킬 카운터 오버레이 ⚔ (챔피언 얼굴 + X 표시 + PENTAKILL)",
                       variable=self.bs_killcounter_var,
                       bg=PANEL, fg=TEXT, selectcolor=PANEL2,
                       activebackground=PANEL, activeforeground=GOLD,
                       font=("Malgun Gothic", 9)).pack(anchor="w")

        kc_detail = ttk.Frame(opt_card, style="Panel.TFrame")
        kc_detail.pack(fill="x", padx=16, pady=(2, 4))

        ttk.Label(kc_detail, text="위치:",
                  background=PANEL, foreground=TEXT,
                  font=("Malgun Gothic", 8)).pack(side="left", padx=(0, 4))
        self.bs_kc_pos_var = tk.StringVar(value="하단 중앙")
        ttk.Combobox(kc_detail, textvariable=self.bs_kc_pos_var,
                     values=["하단 중앙", "하단 좌측", "하단 우측", "상단 중앙"],
                     state="readonly", width=10).pack(side="left", padx=(0, 10))

        ttk.Label(kc_detail, text="아이콘 크기(px):",
                  background=PANEL, foreground=TEXT,
                  font=("Malgun Gothic", 8)).pack(side="left", padx=(0, 4))
        self.bs_kc_size_var = tk.IntVar(value=80)
        tk.Spinbox(kc_detail, from_=40, to=160, increment=10,
                   textvariable=self.bs_kc_size_var, width=5,
                   bg=PANEL2, fg=WHITE, buttonbackground=PANEL,
                   highlightthickness=0, relief="flat",
                   font=("Malgun Gothic", 8)).pack(side="left", padx=(0, 10))

        # 챔피언 아이콘 소스 설정
        icon_src_row = ttk.Frame(opt_card, style="Panel.TFrame")
        icon_src_row.pack(fill="x", padx=16, pady=(4, 3))
        ttk.Label(icon_src_row, text="아이콘 소스:",
                  background=PANEL, foreground=TEXT,
                  font=("Malgun Gothic", 8)).pack(side="left", padx=(0, 8))
        self.icon_src_var = tk.StringVar(value="로컬 폴더")
        for src in ["로컬 폴더", "Data Dragon (자동 다운로드)"]:
            tk.Radiobutton(icon_src_row, text=src,
                           variable=self.icon_src_var, value=src,
                           bg=PANEL, fg=TEXT, selectcolor=PANEL2,
                           activebackground=PANEL, activeforeground=GOLD,
                           font=("Malgun Gothic", 8),
                           command=self._toggle_icon_src).pack(side="left", padx=(0, 10))

        # 로컬 폴더 경로
        self.icon_local_frame = ttk.Frame(opt_card, style="Panel.TFrame")
        self.icon_local_frame.pack(fill="x", padx=16, pady=(0, 3))
        ttk.Label(self.icon_local_frame, text="폴더 경로:",
                  background=PANEL, foreground=TEXT,
                  font=("Malgun Gothic", 8)).pack(side="left", padx=(0, 6))
        self.icon_folder_var = tk.StringVar()
        tk.Entry(self.icon_local_frame, textvariable=self.icon_folder_var,
                 width=28, bg=PANEL2, fg=WHITE, insertbackground=GOLD,
                 highlightthickness=0, relief="flat",
                 font=("Malgun Gothic", 8)).pack(side="left", padx=(0, 4))
        ttk.Button(self.icon_local_frame, text="📂", style="Blue.TButton",
                   command=self._pick_icon_folder).pack(side="left", padx=(0, 8))
        ttk.Label(self.icon_local_frame,
                  text="← Yasuo.png 형식",
                  background=PANEL, foreground=TEXT,
                  font=("Malgun Gothic", 7, "italic")).pack(side="left")

        # Data Dragon 설정 (숨김 상태로 시작)
        self.icon_ddragon_frame = ttk.Frame(opt_card, style="Panel.TFrame")
        ver_row = self.icon_ddragon_frame
        ttk.Label(ver_row, text="패치 버전:",
                  background=PANEL, foreground=TEXT,
                  font=("Malgun Gothic", 8)).pack(side="left", padx=(0, 6))
        self.ddragon_ver_var = tk.StringVar(value="14.6.1")
        tk.Entry(ver_row, textvariable=self.ddragon_ver_var, width=9,
                 bg=PANEL2, fg=WHITE, insertbackground=GOLD,
                 highlightthickness=0, relief="flat",
                 font=("Malgun Gothic", 8)).pack(side="left", padx=(0, 6))
        ttk.Button(ver_row, text="🔄 최신 버전 확인",
                   style="Blue.TButton",
                   command=self._fetch_ddragon_version).pack(side="left")

        # FFmpeg 명령 미리보기
        ttk.Label(col3, text="생성될 FFmpeg 필터 (미리보기):",
                  background=DARK, foreground=TEXT,
                  font=("Malgun Gothic", 9)).pack(anchor="w", padx=10, pady=(6, 2))
        self.bs_cmd_text = scrolledtext.ScrolledText(
            col3, bg=PANEL2, fg=CYAN,
            font=("Consolas", 7), height=7, state="disabled",
            relief="flat", wrap="word")
        self.bs_cmd_text.pack(fill="x", padx=10, pady=(0, 6))

        ttk.Button(col3, text="🔄  명령 미리보기 생성",
                   style="Blue.TButton",
                   command=self._bs_preview_cmd).pack(anchor="w", padx=10, pady=(0, 6))

        # 렌더 버튼
        self.bs_render_btn = ttk.Button(col3, text="▶  비트 싱크 렌더링",
                                         style="Gold.TButton",
                                         command=self._bs_render)
        self.bs_render_btn.pack(anchor="w", padx=10, pady=(0, 6))

        self.bs_status_var = tk.StringVar(value="대기 중")
        self.bs_prog_var   = tk.DoubleVar(value=0)
        ttk.Label(col3, textvariable=self.bs_status_var,
                  background=DARK, foreground=BLUE,
                  font=("Malgun Gothic", 9)).pack(anchor="w", padx=10, pady=(2, 2))
        ttk.Progressbar(col3, variable=self.bs_prog_var,
                        style="Gold.Horizontal.TProgressbar",
                        mode="determinate", length=280).pack(anchor="w", padx=10)

    # ── 비트 싱크 메서드 ─────────────────────────
    def _pick_music(self):
        p = filedialog.askopenfilename(
            title="음악 파일 선택",
            filetypes=[("오디오", "*.mp3 *.wav *.flac *.ogg *.m4a"), ("모든", "*.*")])
        if p:
            self.music_path_var.set(p)
            self.bs_music_var.set(p)

    def _bs_pick_input(self):
        p = filedialog.askopenfilename(
            title="원본 영상 선택",
            filetypes=[("영상", "*.mp4 *.mkv *.avi *.mov"), ("모든", "*.*")])
        if p: self.bs_input_var.set(p)

    def _bs_pick_music(self):
        p = filedialog.askopenfilename(
            title="음악 파일 선택",
            filetypes=[("오디오", "*.mp3 *.wav *.flac *.ogg *.m4a"), ("모든", "*.*")])
        if p:
            self.bs_music_var.set(p)
            self.music_path_var.set(p)

    def _bs_pick_output(self):
        p = filedialog.asksaveasfilename(
            title="출력 저장",
            defaultextension=".mp4",
            filetypes=[("MP4", "*.mp4"), ("MKV", "*.mkv")])
        if p: self.bs_output_var.set(p)

    def _analyze_beats(self):
        path = self.music_path_var.get()
        if not path:
            messagebox.showwarning("파일 필요", "음악 파일을 먼저 선택하세요.")
            return
        self.beat_status_var.set("librosa 분석 중…")
        threading.Thread(target=self._analyze_beats_worker,
                         args=(path,), daemon=True).start()

    def _analyze_beats_worker(self, path: str):
        try:
            import librosa  # type: ignore[import]
            self._log(f"[비트 싱크] librosa 분석 시작: {path}", "info")

            y, sr = librosa.load(path, sr=None, mono=True)
            tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
            beat_times = librosa.frames_to_time(beat_frames, sr=sr)

            # 오프셋 적용
            try:
                offset = float(self.beat_offset_var.get())
            except ValueError:
                offset = 0.0

            self._beats = [float(t) + offset for t in beat_times]
            bpm = float(tempo) if hasattr(tempo, '__float__') else float(tempo[0])

            def _ui():
                self.bpm_var.set(f"{bpm:.1f}")
                self.beat_listbox.delete(0, "end")
                for i, t in enumerate(self._beats):
                    self.beat_listbox.insert("end", f"  비트 {i+1:3d}  {t:.3f}s")
                self.beat_status_var.set(
                    f"✅ {len(self._beats)}개 비트 감지  |  BPM {bpm:.1f}")
                self._log(
                    f"[비트 싱크] BPM={bpm:.1f}, 비트 {len(self._beats)}개", "ok")

            self.after(0, _ui)
        except ImportError:
            self.after(0, lambda: self.beat_status_var.set(
                "❌ librosa 없음 — pip install librosa soundfile"))
            self._log("[비트 싱크] librosa 미설치. pip install librosa soundfile", "error")
        except Exception as e:
            self.after(0, lambda: self.beat_status_var.set(f"오류: {e}"))
            self._log(f"[비트 싱크] 분석 오류: {e}", "error")

    def _on_bs_penta_select(self, _=None):
        sel = self.tree_bs_penta.selection()
        if not sel: return
        try:
            ts = float(self.tree_bs_penta.set(sel[0], "ts_sec"))
            # kill_ts_vars에 펜타킬 타임라인 데이터 자동 주입
            # tree_cam_penta에서 같은 소환사 찾아 킬 타임스탬프 5개 채우기
            sname = self.tree_bs_penta.set(sel[0], "summoner")
            champ = self.tree_bs_penta.set(sel[0], "champion")
            # 타임라인 탭에서 해당 소환사 킬 시퀀스 검색
            kills = self._get_kill_sequence(sname, champ)
            if kills:
                for i, k_ts in enumerate(kills[:5]):
                    self.kill_ts_vars[i].set(f"{k_ts:.3f}")
            else:
                # 타임라인 없을 경우 펜타킬 확정 시간만
                self.kill_ts_vars[4].set(f"{ts:.3f}")
            self._bs_update_mapping_preview()
        except Exception:
            pass

    def _get_kill_sequence(self, sname: str, champ: str) -> list[float]:
        """타임라인 탭에서 해당 소환사+챔피언의 킬 타임스탬프 5개 반환."""
        result = []
        for row in self.tree_timeline.get_children():
            vals = self.tree_timeline.item(row, "values")
            if vals[0] == sname and vals[1] == champ and "5킬" not in vals[4]:
                pass
        # tree_timeline 컬럼: summoner, champion, date, penta_num, kill_num, game_time, ...
        # game_time을 초로 변환
        for row in self.tree_timeline.get_children():
            vals = self.tree_timeline.item(row, "values")
            if vals[0] == sname and vals[1] == champ:
                try:
                    m, s = vals[5].split(":")
                    result.append(int(m) * 60 + float(s))
                except Exception:
                    pass
        return sorted(result)[:5]

    def _auto_assign_beats(self):
        """킬 간격에 맞는 비트를 자동으로 찾아 매핑."""
        if not self._beats:
            messagebox.showwarning("비트 없음", "먼저 음악 파일을 분석하세요.")
            return
        try:
            kill_ts = [float(v.get()) for v in self.kill_ts_vars]
        except ValueError:
            messagebox.showerror("오류", "킬 타임스탬프를 올바르게 입력하세요.")
            return

        # 킬 간 상대 간격
        intervals = [kill_ts[i+1] - kill_ts[i] for i in range(4)]
        total_kill_dur = kill_ts[4] - kill_ts[0]

        # 비트 목록에서 5개짜리 윈도우를 슬라이딩하며
        # 킬 간격 비율과 비트 간격 비율이 가장 유사한 구간 탐색
        best_score = float("inf")
        best_start = 0

        for start in range(len(self._beats) - 4):
            b_window = self._beats[start:start+5]
            b_dur    = b_window[4] - b_window[0]
            if b_dur == 0: continue
            # 각 간격의 비율 차이 합산
            score = 0
            for i in range(4):
                b_ratio = (b_window[i+1] - b_window[i]) / b_dur
                k_ratio = intervals[i] / total_kill_dur if total_kill_dur > 0 else 0.2
                score += abs(b_ratio - k_ratio)
            if score < best_score:
                best_score = score
                best_start = start

        # 최적 비트 할당
        for i, var in enumerate(self.beat_ts_vars):
            var.set(f"{self._beats[best_start + i]:.3f}")

        self._bs_update_mapping_preview()
        self._log(
            f"[비트 싱크] 자동 매핑 완료 — 비트 {best_start+1}~{best_start+5} "
            f"(유사도 점수: {best_score:.4f})", "ok")

    def _auto_assign_beats_by_length(self):
        """
        목표 영상 길이 → 킬당 비트 수 자동 계산 → 비트 배치
        """
        if not self._beats:
            messagebox.showwarning("비트 없음", "먼저 음악 파일을 분석하세요.")
            return
        try:
            kill_ts = [float(v.get()) for v in self.kill_ts_vars]
        except ValueError:
            messagebox.showerror("오류", "킬 타임스탬프를 먼저 입력하세요.")
            return

        target  = self.target_len_var.get()
        intro   = self.tl_intro_var.get()
        outro   = self.tl_outro_var.get()
        mult    = self.penta_beat_mult_var.get()

        # BPM에서 비트 간격 계산
        if len(self._beats) < 2:
            messagebox.showerror("오류", "비트가 2개 이상 필요합니다.")
            return
        beat_gaps = [self._beats[i+1] - self._beats[i]
                     for i in range(min(8, len(self._beats)-1))]
        beat_interval = sum(beat_gaps) / len(beat_gaps)
        bpm = 60 / beat_interval

        # 킬 구간 목표 시간
        # 1~4킬: 각 N비트, 5킬(펜타): N × mult 비트
        # total_kill_beats = 4 * N + N * mult = N * (4 + mult)
        kill_time_budget = target - intro - outro
        if kill_time_budget <= 0:
            messagebox.showerror("오류", "인트로+아웃트로가 목표 길이보다 깁니다.")
            return

        # 킬당 비트 수 계산
        # kill_time_budget = beats_per_kill * (4 + mult) * beat_interval
        beats_per_kill = kill_time_budget / ((4 + mult) * beat_interval)
        beats_per_kill = max(1, round(beats_per_kill))
        penta_beats    = beats_per_kill * mult

        # 실제 킬 구간 길이
        actual_kill_dur = beats_per_kill * 4 * beat_interval + penta_beats * beat_interval
        actual_total    = intro + actual_kill_dur + outro

        # 비트 시작점 탐색 (인트로 이후 비트부터 시작)
        # intro 이후에 오는 첫 비트 인덱스
        start_idx = 0
        for i, bt in enumerate(self._beats):
            if bt >= intro:
                start_idx = i
                break

        # 킬 1~4는 beats_per_kill 간격, 5킬은 penta_beats 간격
        needed = beats_per_kill * 4 + penta_beats
        if start_idx + needed >= len(self._beats):
            # 비트가 부족하면 start_idx를 앞으로 당김
            start_idx = max(0, len(self._beats) - int(needed) - 1)

        assigned = []
        cur = start_idx
        for i in range(5):
            if cur >= len(self._beats):
                break
            assigned.append(self._beats[cur])
            step = penta_beats if i == 4 else beats_per_kill
            cur += int(step)

        # beat_ts_vars에 적용
        for i, var in enumerate(self.beat_ts_vars):
            var.set(f"{assigned[i]:.3f}" if i < len(assigned) else "0.0")

        # 결과 요약
        summary = (
            f"목표: {target}초  →  실제: {actual_total:.1f}초\n"
            f"BPM: {bpm:.1f}  비트간격: {beat_interval:.3f}s\n"
            f"킬당 비트: {beats_per_kill}  ({beats_per_kill*beat_interval:.2f}초/킬)\n"
            f"펜타킬 비트: {penta_beats}  ({penta_beats*beat_interval:.2f}초)\n"
            f"킬 구간: {actual_kill_dur:.1f}초  |  "
            f"인트로: {intro}s  아웃트로: {outro}s"
        )
        self.tl_result_var.set(summary)
        self._bs_update_mapping_preview()
        self._log(
            f"[비트 싱크] 목표 {target}초 → 킬당 {beats_per_kill}비트 / "
            f"펜타킬 {penta_beats}비트 / 실제 {actual_total:.1f}초", "ok")

    def _bs_update_mapping_preview(self):
        try:
            kill_ts  = [float(v.get()) for v in self.kill_ts_vars]
            beat_ts  = [float(v.get()) for v in self.beat_ts_vars]
            lines = ["킬 → 비트 매핑 및 구간별 배속:"]
            for i in range(5):
                lines.append(f"  {i+1}킬  {kill_ts[i]:.2f}s → 비트 {beat_ts[i]:.2f}s")
            lines.append("")
            lines.append("구간별 time-stretch 비율:")
            for i in range(4):
                game_dur = kill_ts[i+1] - kill_ts[i]
                beat_dur = beat_ts[i+1] - beat_ts[i]
                ratio    = game_dur / beat_dur if beat_dur > 0 else 1.0
                lines.append(
                    f"  구간 {i+1}→{i+2}: {game_dur:.2f}s → {beat_dur:.2f}s  "
                    f"(×{1/ratio:.2f} 배속)")
            self.mapping_preview_var.set("\n".join(lines))
        except Exception:
            pass

    def _bs_preview_cmd(self):
        """FFmpeg 필터 명령 미리보기 생성."""
        try:
            cmd = self._build_beatsync_ffmpeg_cmd()
            txt = "\n".join(cmd)
            self.bs_cmd_text.config(state="normal")
            self.bs_cmd_text.delete("1.0", "end")
            self.bs_cmd_text.insert("end", txt)
            self.bs_cmd_text.config(state="disabled")
        except Exception as e:
            messagebox.showerror("오류", str(e))

    def _build_beatsync_ffmpeg_cmd(self) -> list[str]:
        """
        킬 타임스탬프와 비트 타임스탬프를 이용해
        setpts 기반 구간별 time-stretch FFmpeg 명령을 생성.
        """
        import shlex
        ffmpeg = self.ffmpeg_path_var.get() or "ffmpeg"
        inp    = self.bs_input_var.get()
        music  = self.bs_music_var.get()
        out    = self.bs_output_var.get()

        kill_ts = [float(v.get()) for v in self.kill_ts_vars]
        beat_ts = [float(v.get()) for v in self.beat_ts_vars]

        use_preslow   = hasattr(self, 'bs_preslow_var') and self.bs_preslow_var.get()
        preslow_dur   = self.bs_preslow_dur_var.get()  if hasattr(self, 'bs_preslow_dur_var')   else 0.5
        preslow_speed = self.bs_preslow_speed_var.get() if hasattr(self, 'bs_preslow_speed_var') else 0.5

        # ══════════════════════════════════════════
        #  세그먼트 설계
        #
        #  슬로우 예비동작이 있는 경우 각 킬마다:
        #  [이동 구간 (빠르게)] → [킬 직전 N초 슬로우] → [킬 순간~다음이동]
        #
        #  비트 타이밍:
        #    beat[i] = 킬[i] 순간에 대응
        #    beat[i] - preslow_dur_in_beat 직전부터 슬로우
        # ══════════════════════════════════════════
        segments = []

        def add_seg(start, end, ratio, label=""):
            if end > start:
                segments.append({"start": start, "end": end,
                                  "ratio": ratio, "label": label})

        # 구간 0: 영상 시작 ~ 첫 킬 직전(슬로우 포함)
        if use_preslow and kill_ts[0] > preslow_dur:
            # 0 ~ (kill0 - preslow_dur): 그대로
            add_seg(0, kill_ts[0] - preslow_dur, 1.0, "인트로")
            # (kill0 - preslow_dur) ~ kill0: 슬로우 예비동작
            # 실제 게임 시간 preslow_dur → 음악에서 preslow_dur * preslow_speed 차지
            add_seg(kill_ts[0] - preslow_dur, kill_ts[0],
                    preslow_speed, f"슬로우(킬0)")
        else:
            add_seg(0, kill_ts[0], 1.0, "인트로")

        # 구간 1~4: 킬 사이 이동 + 다음 킬 직전 슬로우
        for i in range(4):
            seg_start = kill_ts[i]
            seg_end   = kill_ts[i + 1]
            game_dur  = seg_end - seg_start

            if use_preslow and game_dur > preslow_dur:
                # 이동 구간: kill[i] ~ kill[i+1] - preslow_dur  (비트 싱크 배속)
                move_end   = seg_end - preslow_dur
                move_dur   = move_end - seg_start
                # 비트 싱크 구간에서 슬로우가 차지하는 비트 시간
                beat_dur_total = beat_ts[i + 1] - beat_ts[i]
                # 슬로우가 차지하는 비트 시간 = preslow_dur * preslow_speed
                preslow_beat_dur = preslow_dur * preslow_speed
                move_beat_dur    = beat_dur_total - preslow_beat_dur
                move_ratio = move_beat_dur / move_dur if move_dur > 0 else 1.0

                add_seg(seg_start, move_end, move_ratio, f"이동{i+1}")
                add_seg(move_end,  seg_end,  preslow_speed, f"슬로우(킬{i+1})")
            else:
                # 슬로우 없이 그냥 비트 싱크 배속
                beat_dur = beat_ts[i + 1] - beat_ts[i]
                ratio    = beat_dur / game_dur if game_dur > 0 else 1.0
                add_seg(seg_start, seg_end, ratio, f"이동{i+1}")

        # 구간 5: 마지막 킬 이후 3초
        add_seg(kill_ts[4], kill_ts[4] + 3.0, 1.0, "아웃트로")

        # 각 구간 trim + setpts + concat 필터 생성
        filter_parts = []
        concat_inputs = []
        for i, seg in enumerate(segments):
            s, e, r = seg["start"], seg["end"], seg["ratio"]
            pts = f"PTS*{1/r:.6f}" if r != 1.0 else "PTS"
            part = (
                f"[0:v]trim=start={s:.3f}:end={e:.3f},"
                f"setpts={pts}[v{i}];"
                f"[0:a]atrim=start={s:.3f}:end={e:.3f},"
                f"asetpts=PTS-STARTPTS[a{i}]"
            )
            filter_parts.append(part)
            concat_inputs.append(f"[v{i}][a{i}]")

        n_segs = len(segments)
        concat_str = "".join(concat_inputs) + f"concat=n={n_segs}:v=1:a=1[vout][aout]"

        # 보간 필터
        vout_filter = "[vout]"
        extra_filters = []
        if self.bs_interp_var.get():
            extra_filters.append("minterpolate=fps=60:mi_mode=mci[vinterp]")
            vout_filter = "[vinterp]"

        # 9:16 크롭
        if self.bs_crop916_var.get():
            extra_filters.append(f"{vout_filter}crop=608:1080:656:0,scale=1080:1920[vfinal]")
            vout_filter = "[vfinal]"
        else:
            if extra_filters:
                extra_filters[-1] = extra_filters[-1].rsplit("[", 1)[0] + "[vfinal]"
                vout_filter = "[vfinal]"

        # 페이드
        if self.bs_fade_var.get():
            extra_filters.append(
                f"{vout_filter}fade=t=in:st=0:d=0.3,fade=t=out:st={beat_ts[4]:.2f}:d=0.3[vfade]")
            vout_filter = "[vfade]"

        full_filter = ";".join(filter_parts) + ";" + concat_str
        if extra_filters:
            full_filter += ";" + ";".join(extra_filters)

        cmd = [
            ffmpeg, "-y",
            "-i", inp,
            "-i", music,
            "-filter_complex", full_filter,
            "-map", vout_filter,
            "-map", "[aout]",    # 게임 사운드 (원하면 음악으로 교체)
            "-map", "1:a:0",     # 음악 트랙
            "-c:v", "libx264", "-crf", "18", "-preset", "fast",
            "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart",
            out
        ]
        return cmd

    def _bs_render(self):
        if not self.bs_input_var.get() or not self.bs_output_var.get():
            messagebox.showwarning("파일 필요", "입력 영상과 출력 경로를 지정하세요.")
            return
        try:
            cmd = self._build_beatsync_ffmpeg_cmd()
        except Exception as e:
            messagebox.showerror("명령 생성 오류", str(e))
            return

        use_shake   = hasattr(self, 'bs_shake_var')        and self.bs_shake_var.get()
        use_zoom    = hasattr(self, 'bs_zoom_var')         and self.bs_zoom_var.get()
        use_counter = hasattr(self, 'bs_killcounter_var')  and self.bs_killcounter_var.get()
        need_moviepy = use_shake or use_zoom or use_counter

        self.bs_render_btn.config(state="disabled")
        self.bs_status_var.set("렌더링 중…")
        self.bs_prog_var.set(0)

        beat_ts   = [float(v.get()) for v in self.beat_ts_vars]

        # 킬 카운터용: tl_results에서 현재 선택된 펜타킬 victim_champion 가져오기
        victim_champions = []
        sel = self.tree_bs_penta.selection()
        if sel:
            sname = self.tree_bs_penta.set(sel[0], "summoner")
            champ = self.tree_bs_penta.set(sel[0], "champion")
            victim_champions = self._get_victim_champions(sname, champ)

        if need_moviepy:
            import tempfile, os as _os
            tmp_path  = _os.path.join(
                tempfile.gettempdir(), "penta_bs_pre_effects.mp4")
            cmd_tmp   = cmd[:-1] + [tmp_path]
            final_out = cmd[-1]
            self._log("[비트 싱크] FFmpeg 렌더링 후 MoviePy 효과 적용", "info")
            threading.Thread(
                target=self._bs_render_with_effects,
                args=(cmd_tmp, tmp_path, final_out, beat_ts,
                      use_shake, use_zoom, use_counter, victim_champions),
                daemon=True).start()
        else:
            self._log("[비트 싱크] 렌더링 시작 (효과 없음)", "info")
            threading.Thread(target=self._bs_render_worker,
                             args=(cmd,), daemon=True).start()

    def _toggle_icon_src(self):
        """로컬 폴더 ↔ Data Dragon 전환 시 UI 표시/숨김."""
        if self.icon_src_var.get() == "로컬 폴더":
            self.icon_ddragon_frame.pack_forget()
            self.icon_local_frame.pack(fill="x", padx=16, pady=(0, 3),
                                       after=None)   # 이미 pack되어 있음
        else:
            self.icon_local_frame.pack_forget()
            self.icon_ddragon_frame.pack(fill="x", padx=16, pady=(0, 3))

    def _pick_icon_folder(self):
        """로컬 챔피언 아이콘 폴더 선택."""
        folder = filedialog.askdirectory(title="챔피언 아이콘 폴더 선택")
        if folder:
            self.icon_folder_var.set(folder)
            # 폴더 내 파일 수 확인
            import glob as _glob
            pngs = _glob.glob(os.path.join(folder, "*.png"))
            self._log(
                f"[아이콘] 폴더 설정: {folder} ({len(pngs)}개 PNG)", "ok")

    def _fetch_ddragon_version(self):
        """Data Dragon 최신 버전 자동 조회."""
        def _do():
            try:
                r = requests.get(
                    "https://ddragon.leagueoflegends.com/api/versions.json",
                    timeout=5)
                versions = r.json()
                latest   = versions[0]
                self.after(0, lambda v=latest: (
                    self.ddragon_ver_var.set(v),
                    self._log(f"[DDragon] 최신 버전: {v}", "ok")
                ))
            except Exception as e:
                self._log(f"[DDragon] 버전 조회 실패: {e}", "error")
        threading.Thread(target=_do, daemon=True).start()

    def _download_champion_icon(self, champion_name: str,
                                 version: str, size: int):
        """
        챔피언 아이콘 로드.
        - 로컬 폴더 우선 → 없으면 Data Dragon 다운로드 (소스 설정에 따라)
        - 실패 시 회색 블록 반환
        """
        import numpy as np
        from PIL import Image
        import io

        # 챔피언 이름 정규화
        name_map = {
            "Nunu & Willump": "Nunu",
            "Wukong":         "MonkeyKing",
            "Renata Glasc":   "Renata",
            "K'Sante":        "KSante",
            "Bel'Veth":       "Belveth",
            "Cho'Gath":       "Chogath",
            "Kai'Sa":         "Kaisa",
            "Kha'Zix":        "Khazix",
            "LeBlanc":        "Leblanc",
            "Rek'Sai":        "RekSai",
            "Vel'Koz":        "Velkoz",
            "Wukong":         "MonkeyKing",
        }
        api_name = name_map.get(
            champion_name,
            champion_name.replace(" ", "").replace("'", ""))

        def _load_pil(img_path_or_bytes):
            """PIL Image → RGBA numpy 배열 (size × size)."""
            if isinstance(img_path_or_bytes, (str, os.PathLike)):
                img = Image.open(img_path_or_bytes).convert("RGBA")
            else:
                img = Image.open(io.BytesIO(img_path_or_bytes)).convert("RGBA")
            img = img.resize((size, size), Image.LANCZOS)
            return np.array(img)

        def _fallback():
            arr = np.zeros((size, size, 4), dtype=np.uint8)
            arr[:, :, :3] = 60
            arr[:, :,  3] = 200
            return arr

        # ── 로컬 폴더 검색 ─────────────────────────
        use_local  = (hasattr(self, 'icon_src_var') and
                      self.icon_src_var.get() == "로컬 폴더")
        local_dir  = self.icon_folder_var.get() if hasattr(self, 'icon_folder_var') else ""

        if use_local and local_dir and os.path.isdir(local_dir):
            # 여러 파일명 패턴 시도
            candidates = [
                os.path.join(local_dir, f"{api_name}.png"),
                os.path.join(local_dir, f"{champion_name}.png"),
                os.path.join(local_dir, f"{api_name.lower()}.png"),
                # Data Dragon 타일 형식
                os.path.join(local_dir, f"{api_name}_0.jpg"),
            ]
            for path in candidates:
                if os.path.exists(path):
                    try:
                        return _load_pil(path)
                    except Exception:
                        pass
            # 로컬에 없으면 로그 후 fallback
            self._log(
                f"[아이콘] '{champion_name}' 로컬 파일 없음 → 회색 블록 사용", "warn")
            return _fallback()

        # ── Data Dragon 다운로드 ───────────────────
        url = (f"https://ddragon.leagueoflegends.com/cdn/{version}"
               f"/img/champion/{api_name}.png")
        try:
            r = requests.get(url, timeout=5)
            r.raise_for_status()
            return _load_pil(r.content)
        except Exception as e:
            self._log(f"[아이콘] '{champion_name}' 다운로드 실패: {e}", "warn")
            return _fallback()

    def _make_x_overlay(self, size: int):
        """챔피언 아이콘 위에 얹을 빨간 X 이미지 생성."""
        import numpy as np
        from PIL import Image, ImageDraw

        img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        pad  = size // 8
        w    = max(size // 8, 4)
        draw.line([(pad, pad), (size-pad, size-pad)], fill=(220, 40, 40, 230), width=w)
        draw.line([(size-pad, pad), (pad, size-pad)], fill=(220, 40, 40, 230), width=w)
        return np.array(img)

    def _composite_rgba_on_rgb(self, bg, overlay, x: int, y: int):
        """bg(H,W,3) 위에 overlay(h,w,4) RGBA를 (x,y) 위치에 합성."""
        import numpy as np
        H, W = bg.shape[:2]
        h, w = overlay.shape[:2]
        # 경계 클리핑
        x1, y1 = max(x, 0), max(y, 0)
        x2, y2 = min(x + w, W), min(y + h, H)
        if x2 <= x1 or y2 <= y1:
            return bg
        ox1, oy1 = x1 - x, y1 - y
        ox2, oy2 = ox1 + (x2 - x1), oy1 + (y2 - y1)

        alpha = overlay[oy1:oy2, ox1:ox2, 3:4] / 255.0
        src   = overlay[oy1:oy2, ox1:ox2, :3]
        dst   = bg[y1:y2, x1:x2]

        result = bg.copy()
        result[y1:y2, x1:x2] = (src * alpha + dst * (1 - alpha)).astype(np.uint8)
        return result
        """FFmpeg 렌더링 워커 (진행률 표시)."""
        import subprocess, re
        try:
            proc = subprocess.Popen(cmd, stderr=subprocess.PIPE,
                                    universal_newlines=True,
                                    encoding="utf-8", errors="replace")
            duration_s = None
            for line in proc.stderr:
                m = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", line)
                if m and duration_s is None:
                    h, mi, s = int(m.group(1)), int(m.group(2)), float(m.group(3))
                    duration_s = h * 3600 + mi * 60 + s
                m2 = re.search(r"time=(\d+):(\d+):([\d.]+)", line)
                if m2 and duration_s:
                    h, mi, s = int(m2.group(1)), int(m2.group(2)), float(m2.group(3))
                    elapsed = h * 3600 + mi * 60 + s
                    pct = min(elapsed / duration_s * 100, 99)
                    self.after(0, lambda p=pct, e=elapsed, d=duration_s: (
                        self.bs_prog_var.set(p),
                        self.bs_status_var.set(f"{e:.0f}s / {d:.0f}s  ({p:.0f}%)"),
                    ))
            proc.wait()
            if proc.returncode == 0:
                self.after(0, lambda: (
                    self.bs_prog_var.set(100),
                    self.bs_status_var.set("✅ 비트 싱크 렌더링 완료!")
                ))
                self._log(f"[비트 싱크] 완료 → {cmd[-1]}", "ok")
            else:
                self.after(0, lambda: self.bs_status_var.set("❌ FFmpeg 오류"))
                self._log(f"[비트 싱크] 오류 (코드 {proc.returncode})", "error")
        except Exception as e:
            self._log(f"[비트 싱크] 예외: {e}", "error")
        finally:
            self.after(0, lambda: self.bs_render_btn.config(state="normal"))

    def _get_victim_champions(self, sname: str, champ: str) -> list[str]:
        """타임라인 탭에서 해당 소환사 펜타킬의 피해자 챔피언 5개 반환."""
        victims = []
        for row in self.tree_timeline.get_children():
            vals = self.tree_timeline.item(row, "values")
            if vals[0] == sname and vals[1] == champ:
                # values: (summoner, champion, date, penta_num, kill_num, game_time, interval, victim, zone, coords)
                victims.append(vals[7])  # victim_name (summoner name)
        # victim_champion은 저장된 tl_results에서 가져오기 시도
        # 없으면 빈 문자열 (아이콘 다운로드 실패 → 회색 블록)
        return victims[:5]

    def _bs_render_with_effects(self, cmd_tmp: list, tmp_path: str,
                                 final_out: str, beat_ts: list[float],
                                 use_shake: bool, use_zoom: bool,
                                 use_counter: bool, victim_names: list[str]):
        """
        1) FFmpeg 렌더링 (임시 파일)
        2) MoviePy 효과 일괄 적용:
           - 줌인 펀치
           - 화면 흔들림
           - 킬 카운터 오버레이 (챔피언 아이콘 + X + PENTAKILL)
        3) 최종 파일 저장
        """
        import subprocess, re, math, os as _os

        # ── Step 1: FFmpeg ──
        self.after(0, lambda: self.bs_status_var.set("1/2  FFmpeg 렌더링 중…"))
        try:
            proc = subprocess.Popen(cmd_tmp, stderr=subprocess.PIPE,
                                    universal_newlines=True,
                                    encoding="utf-8", errors="replace")
            duration_s = None
            for line in proc.stderr:
                m = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", line)
                if m and duration_s is None:
                    h, mi, s = int(m.group(1)), int(m.group(2)), float(m.group(3))
                    duration_s = h * 3600 + mi * 60 + s
                m2 = re.search(r"time=(\d+):(\d+):([\d.]+)", line)
                if m2 and duration_s:
                    h, mi, s = int(m2.group(1)), int(m2.group(2)), float(m2.group(3))
                    elapsed = h * 3600 + mi * 60 + s
                    pct = min(elapsed / duration_s * 50, 49)
                    self.after(0, lambda p=pct: self.bs_prog_var.set(p))
            proc.wait()
            if proc.returncode != 0:
                self.after(0, lambda: self.bs_status_var.set("❌ FFmpeg 오류"))
                self._log(f"[효과] FFmpeg 오류 (코드 {proc.returncode})", "error")
                return
        except Exception as e:
            self._log(f"[효과] FFmpeg 예외: {e}", "error")
            self.after(0, lambda: self.bs_status_var.set(f"❌ FFmpeg 오류"))
            return

        # ── Step 2: MoviePy 효과 ──
        self.after(0, lambda: self.bs_status_var.set("2/2  MoviePy 효과 적용 중…"))
        try:
            import numpy as np
            from moviepy.editor import VideoFileClip
            from moviepy.video.VideoClip import VideoClip
            from PIL import Image, ImageDraw, ImageFont

            clip = VideoFileClip(tmp_path)
            fps  = clip.fps
            W, H = clip.size

            # 효과 파라미터
            shake_px   = self.bs_shake_px_var.get()   if use_shake   else 0
            shake_dur  = self.bs_shake_dur_var.get()   if use_shake   else 0
            zoom_scale = self.bs_zoom_scale_var.get()  if use_zoom    else 1.0
            zoom_dur   = self.bs_zoom_dur_var.get()    if use_zoom    else 0
            kc_size    = self.bs_kc_size_var.get()     if use_counter else 80
            kc_pos     = self.bs_kc_pos_var.get()      if use_counter else "하단 중앙"
            ddragon_v  = self.ddragon_ver_var.get()    if use_counter else "14.6.1"

            # 챔피언 아이콘 사전 다운로드
            champ_icons: list[np.ndarray] = []
            x_overlay = self._make_x_overlay(kc_size)
            if use_counter:
                self.after(0, lambda: self.bs_status_var.set(
                    "2/2  챔피언 아이콘 다운로드 중…"))
                for vname in victim_names[:5]:
                    icon = self._download_champion_icon(vname, ddragon_v, kc_size)
                    champ_icons.append(icon)
                while len(champ_icons) < 5:
                    blank = np.zeros((kc_size, kc_size, 4), dtype=np.uint8)
                    blank[:, :, :3] = 50; blank[:, :, 3] = 180
                    champ_icons.append(blank)
                self._log(f"[효과] 챔피언 아이콘 {len(champ_icons)}개 준비", "ok")

            # 킬 카운터 위치 계산
            kc_gap    = 10
            kc_total  = kc_size * 5 + kc_gap * 4
            kc_margin = 30
            if kc_pos == "하단 중앙":
                kc_x_start = (W - kc_total) // 2
                kc_y       = H - kc_size - kc_margin
            elif kc_pos == "하단 좌측":
                kc_x_start = kc_margin
                kc_y       = H - kc_size - kc_margin
            elif kc_pos == "하단 우측":
                kc_x_start = W - kc_total - kc_margin
                kc_y       = H - kc_size - kc_margin
            else:  # 상단 중앙
                kc_x_start = (W - kc_total) // 2
                kc_y       = kc_margin

            # PENTAKILL 텍스트용 폰트
            penta_font = None
            for fname in ["malgun.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"]:
                try:
                    penta_font = ImageFont.truetype(fname, H // 8)
                    break
                except: pass
            if penta_font is None:
                penta_font = ImageFont.load_default()

            kill_counter_font = None
            for fname in ["malgun.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"]:
                try:
                    kill_counter_font = ImageFont.truetype(fname, kc_size // 2)
                    break
                except: pass
            if kill_counter_font is None:
                kill_counter_font = ImageFont.load_default()

            def make_frame(t):
                frame = clip.get_frame(t)  # (H, W, 3) uint8

                # ── 줌인 펀치 ──
                if use_zoom:
                    for i, bt in enumerate(beat_ts):
                        if bt <= t <= bt + zoom_dur:
                            progress = (t - bt) / zoom_dur      # 0→1
                            # ease-out: 빠르게 올라가고 천천히 복귀
                            if progress < 0.3:
                                z = 1.0 + (zoom_scale - 1.0) * (progress / 0.3)
                            else:
                                z = zoom_scale - (zoom_scale - 1.0) * ((progress - 0.3) / 0.7)
                            if z > 1.001:
                                # 중앙 기준 줌
                                nH = int(H / z)
                                nW = int(W / z)
                                y0 = (H - nH) // 2
                                x0 = (W - nW) // 2
                                cropped = frame[y0:y0+nH, x0:x0+nW]
                                from PIL import Image as PILImage
                                zoomed = np.array(
                                    PILImage.fromarray(cropped).resize(
                                        (W, H), PILImage.LANCZOS))
                                frame = zoomed
                            break

                # ── 화면 흔들림 ──
                if use_shake:
                    for bt in beat_ts:
                        if bt <= t <= bt + shake_dur:
                            progress = (t - bt) / shake_dur
                            decay    = 1.0 - progress
                            phase    = (t - bt) * 30 * 2 * math.pi
                            dx = int(math.sin(phase)       * shake_px * decay)
                            dy = int(math.sin(phase * 1.3) * shake_px * decay * 0.6)
                            if dx != 0 or dy != 0:
                                frame = np.roll(frame, dy, axis=0)
                                frame = np.roll(frame, dx, axis=1)
                                if dy > 0:  frame[:dy, :] = 0
                                elif dy < 0: frame[dy:, :] = 0
                                if dx > 0:  frame[:, :dx] = 0
                                elif dx < 0: frame[:, dx:] = 0
                            break

                # ── 킬 카운터 오버레이 ──
                if use_counter and champ_icons:
                    # 현재 시점에서 몇 킬까지 발생했는지
                    kills_done = sum(1 for bt in beat_ts if t >= bt)
                    is_penta   = kills_done >= 5 and t >= beat_ts[4]

                    if kills_done > 0:
                        for i in range(5):
                            x_pos = kc_x_start + i * (kc_size + kc_gap)
                            # 아이콘 배경 (어두운 반투명)
                            bg_icon = np.zeros((kc_size, kc_size, 4), dtype=np.uint8)
                            bg_icon[:, :, 3] = 120
                            frame = self._composite_rgba_on_rgb(frame, bg_icon, x_pos, kc_y)

                            if i < kills_done:
                                # 챔피언 아이콘 표시
                                frame = self._composite_rgba_on_rgb(
                                    frame, champ_icons[i], x_pos, kc_y)
                                # X 오버레이
                                frame = self._composite_rgba_on_rgb(
                                    frame, x_overlay, x_pos, kc_y)

                        # 킬 카운트 텍스트 (⚔ × kills_done)
                        pil_frame = Image.fromarray(frame)
                        draw      = ImageDraw.Draw(pil_frame)
                        count_txt = f"{'⚔' * min(kills_done, 5)}"
                        bbox = draw.textbbox((0, 0), count_txt, font=kill_counter_font)
                        tw = bbox[2] - bbox[0]
                        cx = kc_x_start + kc_total // 2 - tw // 2
                        cy = kc_y - kc_size // 2 - 4
                        draw.text((cx+2, cy+2), count_txt,
                                  font=kill_counter_font, fill=(0,0,0,180))
                        draw.text((cx, cy), count_txt,
                                  font=kill_counter_font, fill=(200, 170, 110, 255))
                        frame = np.array(pil_frame)

                    # PENTAKILL 텍스트 (펜타킬 확정 후 2초간)
                    if is_penta and t <= beat_ts[4] + 2.0:
                        fade_in  = min((t - beat_ts[4]) / 0.3, 1.0)
                        fade_out = 1.0 if t < beat_ts[4] + 1.5 else max(0, 1 - (t - beat_ts[4] - 1.5) / 0.5)
                        alpha_f  = int(255 * fade_in * fade_out)

                        pil_frame = Image.fromarray(frame)
                        draw      = ImageDraw.Draw(pil_frame)
                        txt       = "PENTAKILL"
                        bbox      = draw.textbbox((0, 0), txt, font=penta_font)
                        tw = bbox[2] - bbox[0]
                        px = (W - tw) // 2
                        py = H // 3

                        # 그림자
                        draw.text((px+4, py+4), txt, font=penta_font,
                                  fill=(0, 0, 0, alpha_f))
                        # 메인 텍스트 (금색)
                        draw.text((px, py), txt, font=penta_font,
                                  fill=(200, 170, 80, alpha_f))
                        frame = np.array(pil_frame)

                return frame

            self.after(0, lambda: self.bs_status_var.set(
                "2/2  MoviePy 렌더링 중 (시간이 걸립니다)…"))

            result_clip = VideoClip(make_frame, duration=clip.duration)
            result_clip.fps = fps
            result_clip = result_clip.set_audio(clip.audio)

            result_clip.write_videofile(
                final_out, codec="libx264", audio_codec="aac",
                fps=fps, preset="fast", logger=None,
                ffmpeg_params=["-crf", "18", "-movflags", "+faststart"])

            clip.close()
            result_clip.close()
            try: _os.remove(tmp_path)
            except: pass

            self.after(0, lambda: (
                self.bs_prog_var.set(100),
                self.bs_status_var.set("✅ 모든 효과 적용 완료!")
            ))
            self._log(f"[효과] 완료 → {final_out}", "ok")

        except ImportError as e:
            self._log(f"[효과] 패키지 없음: {e} — pip install moviepy Pillow", "error")
            self.after(0, lambda: self.bs_status_var.set(
                f"❌ 패키지 없음: {e}"))
            # 임시 파일 → 최종 파일로 이동
            try:
                import shutil
                shutil.move(tmp_path, final_out)
                self.after(0, lambda: (
                    self.bs_prog_var.set(100),
                    self.bs_status_var.set("✅ 완료 (효과 생략 — 패키지 없음)")
                ))
            except: pass
        except Exception as e:
            self._log(f"[효과] MoviePy 오류: {e}", "error")
            self.after(0, lambda: self.bs_status_var.set(f"❌ 오류: {e}"))
        finally:
            self.after(0, lambda: self.bs_render_btn.config(state="normal"))

    # ══════════════════════════════════════════════
    #  썸네일 생성기 탭
    # ══════════════════════════════════════════════
    def _build_thumbnail_tab(self, parent):
        self._thumb_preview_img = None   # PhotoImage 참조 유지

        # ── 좌우 분할 ──
        body = ttk.Frame(parent)
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)

        # ══ 왼쪽: 설정 ══
        left = ttk.Frame(body, style="Panel.TFrame")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 1))

        ttk.Label(left, text="  🖼 썸네일 자동 생성",
                  background=PANEL, foreground=GOLD,
                  font=("Malgun Gothic", 11, "bold")).pack(anchor="w",
                  padx=12, pady=(10, 6))

        # 프레임 추출
        frame_card = ttk.Frame(left, style="Panel.TFrame", padding=8)
        frame_card.pack(fill="x", padx=12, pady=(0, 6))
        ttk.Label(frame_card, text="① 영상에서 프레임 추출",
                  background=PANEL, foreground=GOLD,
                  font=("Malgun Gothic", 10, "bold")).pack(anchor="w", pady=(0, 5))

        vf_row = ttk.Frame(frame_card, style="Panel.TFrame")
        vf_row.pack(fill="x", pady=(0, 4))
        ttk.Label(vf_row, text="영상 파일:", background=PANEL,
                  foreground=TEXT, font=("Malgun Gothic", 9)).pack(side="left", padx=(0, 6))
        self.thumb_video_var = tk.StringVar()
        tk.Entry(vf_row, textvariable=self.thumb_video_var, width=24,
                 bg=PANEL2, fg=WHITE, insertbackground=GOLD,
                 highlightthickness=0, relief="flat",
                 font=("Malgun Gothic", 9)).pack(side="left", padx=(0, 4))
        ttk.Button(vf_row, text="📂", style="Blue.TButton",
                   command=self._thumb_pick_video).pack(side="left")

        ts_row = ttk.Frame(frame_card, style="Panel.TFrame")
        ts_row.pack(fill="x", pady=(0, 4))
        ttk.Label(ts_row, text="추출 시간(초):", background=PANEL,
                  foreground=TEXT, font=("Malgun Gothic", 9)).pack(side="left", padx=(0, 6))
        self.thumb_ts_var = tk.StringVar(value="0.0")
        tk.Entry(ts_row, textvariable=self.thumb_ts_var, width=8,
                 bg=PANEL2, fg=WHITE, insertbackground=GOLD,
                 highlightthickness=0, relief="flat",
                 font=("Malgun Gothic", 9)).pack(side="left", padx=(0, 8))
        ttk.Label(ts_row, text="← 킬 타임스탬프 직접 입력",
                  background=PANEL, foreground=TEXT,
                  font=("Malgun Gothic", 8, "italic")).pack(side="left")

        ttk.Button(frame_card, text="📸  프레임 추출",
                   style="Blue.TButton",
                   command=self._extract_thumb_frame).pack(anchor="w")

        # 텍스트 오버레이
        text_card = ttk.Frame(left, style="Panel.TFrame", padding=8)
        text_card.pack(fill="x", padx=12, pady=(0, 6))
        ttk.Label(text_card, text="② 텍스트 오버레이 설정",
                  background=PANEL, foreground=GOLD,
                  font=("Malgun Gothic", 10, "bold")).pack(anchor="w", pady=(0, 6))

        for label, attr, default in [
            ("상단 제목",   "thumb_title_var",    "PENTAKILL"),
            ("챔피언명",    "thumb_champ_var",     ""),
            ("소환사명",    "thumb_sname_var",     ""),
            ("KDA",        "thumb_kda_var",        ""),
            ("하단 텍스트", "thumb_bottom_var",   "Master ~ Challenger"),
        ]:
            row = ttk.Frame(text_card, style="Panel.TFrame")
            row.pack(fill="x", pady=2)
            ttk.Label(row, text=f"{label}:", background=PANEL,
                      foreground=TEXT, font=("Malgun Gothic", 9),
                      width=10).pack(side="left", padx=(0, 6))
            var = tk.StringVar(value=default)
            setattr(self, attr, var)
            tk.Entry(row, textvariable=var, width=22,
                     bg=PANEL2, fg=WHITE, insertbackground=GOLD,
                     highlightthickness=0, relief="flat",
                     font=("Malgun Gothic", 9)).pack(side="left")

        # 색상 / 스타일
        style_card = ttk.Frame(left, style="Panel.TFrame", padding=8)
        style_card.pack(fill="x", padx=12, pady=(0, 6))
        ttk.Label(style_card, text="③ 스타일",
                  background=PANEL, foreground=GOLD,
                  font=("Malgun Gothic", 10, "bold")).pack(anchor="w", pady=(0, 5))

        st_row1 = ttk.Frame(style_card, style="Panel.TFrame")
        st_row1.pack(fill="x", pady=2)
        ttk.Label(st_row1, text="레이아웃:", background=PANEL,
                  foreground=TEXT, font=("Malgun Gothic", 9)).pack(side="left", padx=(0, 8))
        self.thumb_layout_var = tk.StringVar(value="🔥 임팩트 (대형 텍스트)")
        ttk.Combobox(st_row1, textvariable=self.thumb_layout_var,
                     values=["🔥 임팩트 (대형 텍스트)",
                             "⚔ 클래식 (상단 타이틀 + 하단 정보)",
                             "🎮 게이머 (어두운 배경 + 네온)",
                             "🏆 심플 (최소한의 텍스트)"],
                     state="readonly", width=26).pack(side="left")

        st_row2 = ttk.Frame(style_card, style="Panel.TFrame")
        st_row2.pack(fill="x", pady=2)
        ttk.Label(st_row2, text="어두운 오버레이:", background=PANEL,
                  foreground=TEXT, font=("Malgun Gothic", 9)).pack(side="left", padx=(0, 8))
        self.thumb_dark_var = tk.IntVar(value=120)
        tk.Scale(st_row2, from_=0, to=200,
                 variable=self.thumb_dark_var, orient="horizontal",
                 length=160, bg=DARK, troughcolor=PANEL2,
                 highlightthickness=0, relief="flat",
                 fg=TEXT, activebackground=GOLD).pack(side="left")
        ttk.Label(st_row2, textvariable=tk.StringVar(),
                  background=PANEL, foreground=TEXT,
                  font=("Malgun Gothic", 9)).pack(side="left")

        # 9:16 강제
        self.thumb_916_var = tk.BooleanVar(value=True)
        tk.Checkbutton(style_card,
                       text="9:16 비율로 크롭 (유튜브 쇼츠 썸네일)",
                       variable=self.thumb_916_var,
                       bg=PANEL, fg=TEXT, selectcolor=PANEL2,
                       activebackground=PANEL, activeforeground=GOLD,
                       font=("Malgun Gothic", 9)).pack(anchor="w")

        # 출력 경로
        out_row = ttk.Frame(left, style="Panel.TFrame")
        out_row.pack(fill="x", padx=12, pady=(4, 6))
        ttk.Label(out_row, text="저장 경로:", background=PANEL,
                  foreground=TEXT, font=("Malgun Gothic", 9)).pack(side="left", padx=(0, 6))
        self.thumb_out_var = tk.StringVar()
        tk.Entry(out_row, textvariable=self.thumb_out_var, width=24,
                 bg=PANEL2, fg=WHITE, insertbackground=GOLD,
                 highlightthickness=0, relief="flat",
                 font=("Malgun Gothic", 9)).pack(side="left", padx=(0, 4))
        ttk.Button(out_row, text="📂", style="Blue.TButton",
                   command=self._thumb_pick_out).pack(side="left")

        # 생성 버튼
        gen_btns = ttk.Frame(left, style="Panel.TFrame")
        gen_btns.pack(fill="x", padx=12, pady=(0, 8))
        ttk.Button(gen_btns, text="🖼  썸네일 생성 & 미리보기",
                   style="Gold.TButton",
                   command=self._generate_thumbnail).pack(side="left", padx=(0, 8))
        ttk.Button(gen_btns, text="💾  저장",
                   style="Blue.TButton",
                   command=self._save_thumbnail).pack(side="left")

        self.thumb_status_var = tk.StringVar(value="영상 파일을 선택하세요")
        ttk.Label(left, textvariable=self.thumb_status_var,
                  background=PANEL, foreground=BLUE,
                  font=("Malgun Gothic", 9)).pack(anchor="w", padx=12)

        # 펜타킬 목록 (클릭 → 정보 자동 입력)
        ttk.Label(left,
                  text="  펜타킬 목록 (클릭 → 챔피언/소환사/KDA 자동 입력)",
                  background=PANEL, foreground=GOLD,
                  font=("Malgun Gothic", 9, "bold")).pack(anchor="w",
                  padx=12, pady=(8, 2))
        cols_th = ("summoner", "champion", "kda", "ts_sec")
        self.tree_thumb_penta = ttk.Treeview(left, columns=cols_th,
                                              show="headings", height=5)
        for cid, hd, w in zip(cols_th,
            ["소환사명", "챔피언", "KDA", "타임스탬프(초)"],
            [130, 110, 90, 90]):
            self.tree_thumb_penta.heading(cid, text=hd)
            self.tree_thumb_penta.column(cid, width=w, anchor="center")
        self.tree_thumb_penta.bind("<<TreeviewSelect>>",
                                    self._on_thumb_penta_select)
        th_vsb = ttk.Scrollbar(left, orient="vertical",
                                command=self.tree_thumb_penta.yview)
        self.tree_thumb_penta.configure(yscrollcommand=th_vsb.set)
        th_vsb.pack(side="right", fill="y")
        self.tree_thumb_penta.pack(fill="x", padx=(12, 0), pady=(0, 8))

        # ══ 오른쪽: 미리보기 ══
        right = ttk.Frame(body)
        right.grid(row=0, column=1, sticky="nsew", padx=(1, 0))

        ttk.Label(right, text="  미리보기 (1080×1920 → 축소)",
                  background=PANEL, foreground=GOLD,
                  font=("Malgun Gothic", 10, "bold")).pack(anchor="w",
                  padx=12, pady=(10, 6))

        # 미리보기 캔버스 (9:16 비율 축소)
        PREV_W, PREV_H = 270, 480
        self.thumb_canvas = tk.Canvas(right, width=PREV_W, height=PREV_H,
                                       bg=PANEL2, highlightthickness=1,
                                       highlightbackground=GOLD_D)
        self.thumb_canvas.pack(padx=12, pady=(0, 8))
        self.thumb_canvas.create_text(
            PREV_W // 2, PREV_H // 2,
            text="썸네일 미리보기\n영상에서 프레임을\n추출하면 표시됩니다",
            fill=TEXT, font=("Malgun Gothic", 10), justify="center")

        # 메타 정보
        self.thumb_meta_var = tk.StringVar(value="")
        ttk.Label(right, textvariable=self.thumb_meta_var,
                  background=DARK, foreground=TEXT,
                  font=("Malgun Gothic", 8)).pack(anchor="w", padx=12)

    # ── 썸네일 메서드 ────────────────────────────
    def _thumb_pick_video(self):
        p = filedialog.askopenfilename(
            title="영상 파일 선택",
            filetypes=[("영상", "*.mp4 *.mkv *.avi *.mov"), ("모든", "*.*")])
        if p: self.thumb_video_var.set(p)

    def _thumb_pick_out(self):
        p = filedialog.asksaveasfilename(
            title="썸네일 저장",
            defaultextension=".jpg",
            filetypes=[("JPEG", "*.jpg"), ("PNG", "*.png")])
        if p: self.thumb_out_var.set(p)

    def _on_thumb_penta_select(self, _=None):
        sel = self.tree_thumb_penta.selection()
        if not sel: return
        try:
            vals = self.tree_thumb_penta.item(sel[0], "values")
            self.thumb_sname_var.set(vals[0])
            self.thumb_champ_var.set(vals[1])
            self.thumb_kda_var.set(vals[2])
            self.thumb_ts_var.set(vals[3])
        except Exception:
            pass

    def _extract_thumb_frame(self):
        """FFmpeg으로 지정 시간의 프레임을 임시 PNG로 추출."""
        video = self.thumb_video_var.get()
        if not video:
            messagebox.showwarning("파일 필요", "영상 파일을 선택하세요.")
            return
        try:
            ts = float(self.thumb_ts_var.get())
        except ValueError:
            messagebox.showerror("오류", "시간을 올바르게 입력하세요.")
            return

        import tempfile, subprocess
        self._thumb_frame_path = os.path.join(
            tempfile.gettempdir(), "penta_thumb_frame.png")
        ffmpeg = self.ffmpeg_path_var.get() or "ffmpeg"
        cmd = [ffmpeg, "-y", "-ss", str(ts), "-i", video,
               "-frames:v", "1", "-q:v", "2", self._thumb_frame_path]

        self.thumb_status_var.set("프레임 추출 중…")
        def _do():
            try:
                result = __import__("subprocess").run(
                    cmd, capture_output=True, timeout=15)
                if result.returncode == 0 and os.path.exists(self._thumb_frame_path):
                    self.after(0, lambda: (
                        self.thumb_status_var.set("✅ 프레임 추출 완료. '썸네일 생성' 클릭!"),
                        self._load_preview_image(self._thumb_frame_path)
                    ))
                    self._log(f"[썸네일] 프레임 추출 완료 @ {ts:.2f}s", "ok")
                else:
                    self.after(0, lambda: self.thumb_status_var.set("❌ 프레임 추출 실패"))
            except Exception as e:
                self.after(0, lambda: self.thumb_status_var.set(f"오류: {e}"))
        threading.Thread(target=_do, daemon=True).start()

    def _load_preview_image(self, path: str):
        """캔버스에 미리보기 이미지 로드."""
        try:
            from PIL import Image, ImageTk
            img = Image.open(path)
            # 9:16 크롭
            if self.thumb_916_var.get():
                w, h = img.size
                new_w = int(h * 9 / 16)
                x0 = (w - new_w) // 2
                img = img.crop((x0, 0, x0 + new_w, h))
            # 캔버스 크기에 맞게 축소
            PREV_W, PREV_H = 270, 480
            img.thumbnail((PREV_W, PREV_H), Image.LANCZOS)
            self._thumb_preview_img = ImageTk.PhotoImage(img)
            self.thumb_canvas.delete("all")
            self.thumb_canvas.create_image(
                PREV_W // 2, PREV_H // 2,
                image=self._thumb_preview_img, anchor="center")
            self.thumb_meta_var.set(f"원본: {img.size[0]}×{img.size[1]}px")
        except ImportError:
            self.thumb_canvas.delete("all")
            self.thumb_canvas.create_text(135, 240,
                text="Pillow 미설치\npip install Pillow",
                fill=RED, font=("Malgun Gothic", 10), justify="center")

    def _generate_thumbnail(self):
        """Pillow로 텍스트 오버레이 합성 후 캔버스에 미리보기."""
        if not hasattr(self, '_thumb_frame_path') or \
           not os.path.exists(self._thumb_frame_path):
            messagebox.showwarning("프레임 없음", "먼저 영상에서 프레임을 추출하세요.")
            return
        threading.Thread(target=self._generate_thumbnail_worker,
                         daemon=True).start()

    def _generate_thumbnail_worker(self):
        try:
            from PIL import Image, ImageDraw, ImageFont
            import io

            img = Image.open(self._thumb_frame_path).convert("RGBA")
            W, H = img.size

            # 9:16 크롭
            if self.thumb_916_var.get():
                new_w = int(H * 9 / 16)
                x0 = (W - new_w) // 2
                img = img.crop((x0, 0, x0 + new_w, H))
                img = img.resize((1080, 1920), Image.LANCZOS)
                W, H = 1080, 1920

            # 어두운 오버레이
            dark = self.thumb_dark_var.get()
            overlay = Image.new("RGBA", (W, H), (0, 0, 0, dark))
            img = Image.alpha_composite(img, overlay)

            draw = ImageDraw.Draw(img)

            # 레이아웃별 텍스트 배치
            layout = self.thumb_layout_var.get()
            title   = self.thumb_title_var.get()
            champ   = self.thumb_champ_var.get()
            sname   = self.thumb_sname_var.get()
            kda     = self.thumb_kda_var.get()
            bottom  = self.thumb_bottom_var.get()

            def draw_text_centered(text, y, size, color="#C8AA6E",
                                    stroke_w=3, stroke_col="#000000"):
                # 시스템 폰트 fallback
                font = None
                for fname in ["malgun.ttf", "NanumGothicBold.ttf",
                               "arialbd.ttf", "DejaVuSans-Bold.ttf"]:
                    try:
                        font = ImageFont.truetype(fname, size)
                        break
                    except Exception:
                        pass
                if font is None:
                    font = ImageFont.load_default()
                bbox = draw.textbbox((0, 0), text, font=font)
                tw = bbox[2] - bbox[0]
                x = (W - tw) // 2
                draw.text((x, y), text, font=font,
                           fill=color,
                           stroke_width=stroke_w,
                           stroke_fill=stroke_col)

            if "임팩트" in layout:
                draw_text_centered(title,  int(H * 0.12), 130, "#C8AA6E", 5)
                if champ: draw_text_centered(champ, int(H * 0.32), 80,  "#FFFFFF", 4)
                if kda:   draw_text_centered(f"KDA  {kda}", int(H * 0.52), 55, "#00B48A", 3)
                if sname: draw_text_centered(sname, int(H * 0.66), 48, "#A9B4C8", 3)
                if bottom:draw_text_centered(bottom,int(H * 0.90), 42, "#785A28", 2)

            elif "클래식" in layout:
                # 상단 타이틀 바
                draw.rectangle([(0, 0), (W, 160)], fill=(0, 0, 0, 180))
                draw_text_centered(title, 30, 90, "#C8AA6E", 4)
                # 하단 정보 바
                draw.rectangle([(0, H - 200), (W, H)], fill=(0, 0, 0, 200))
                if champ: draw_text_centered(champ, H - 180, 70, "#FFFFFF", 3)
                if kda:   draw_text_centered(f"KDA {kda}", H - 100, 50, "#00B48A", 3)
                if sname: draw_text_centered(sname, H - 48,  38, "#A9B4C8", 2)

            elif "게이머" in layout:
                # 네온 효과
                draw_text_centered(title,  int(H * 0.08), 120, "#0BC4E3", 6, "#001020")
                if champ: draw_text_centered(champ, int(H * 0.28), 75,  "#E8A44A", 4, "#200800")
                if kda:   draw_text_centered(f"KDA  {kda}", int(H * 0.48), 55, "#00B48A", 3)
                if sname: draw_text_centered(sname, int(H * 0.64), 46, "#9B59B6", 3)
                if bottom:draw_text_centered(bottom,int(H * 0.88), 40, "#C8AA6E", 2)

            else:  # 심플
                if champ: draw_text_centered(champ, int(H * 0.35), 100, "#FFFFFF", 4)
                draw_text_centered(title,  int(H * 0.55), 80,  "#C8AA6E", 4)
                if sname: draw_text_centered(sname, int(H * 0.72), 50, "#A9B4C8", 3)

            # 저장용 버퍼에 보관
            self._thumbnail_img = img.convert("RGB")

            # 미리보기
            PREV_W, PREV_H = 270, 480
            preview = img.copy()
            preview.thumbnail((PREV_W, PREV_H), Image.LANCZOS)

            from PIL import ImageTk
            photo = ImageTk.PhotoImage(preview)

            def _ui():
                self._thumb_preview_img = photo
                self.thumb_canvas.delete("all")
                self.thumb_canvas.create_image(
                    PREV_W // 2, PREV_H // 2,
                    image=self._thumb_preview_img, anchor="center")
                self.thumb_status_var.set("✅ 썸네일 생성 완료! '저장' 버튼으로 저장하세요.")
                self.thumb_meta_var.set(f"1080×1920  |  {layout}")
            self.after(0, _ui)
            self._log("[썸네일] 생성 완료", "ok")

        except ImportError:
            self.after(0, lambda: self.thumb_status_var.set(
                "❌ Pillow 없음 — pip install Pillow"))
            self._log("[썸네일] Pillow 미설치. pip install Pillow", "error")
        except Exception as e:
            self.after(0, lambda: self.thumb_status_var.set(f"오류: {e}"))
            self._log(f"[썸네일] 오류: {e}", "error")

    def _save_thumbnail(self):
        if not hasattr(self, '_thumbnail_img'):
            messagebox.showwarning("생성 필요", "먼저 썸네일을 생성하세요.")
            return
        out = self.thumb_out_var.get()
        if not out:
            out = filedialog.asksaveasfilename(
                defaultextension=".jpg",
                filetypes=[("JPEG", "*.jpg"), ("PNG", "*.png")])
        if out:
            try:
                self._thumbnail_img.save(out, quality=95)
                self.thumb_status_var.set(f"💾 저장 완료: {out}")
                self._log(f"[썸네일] 저장 → {out}", "ok")
            except Exception as e:
                messagebox.showerror("저장 오류", str(e))

    # ── 공통 트리 생성 ──────────────────────────
    def _make_tree(self, parent, cols, col_defs, hscroll=False):
        tree = ttk.Treeview(parent, columns=cols, show="headings")
        for (hd, w), cid in zip(col_defs, cols):
            tree.heading(cid, text=hd, command=lambda c=cid, t=tree: self._sort(t, c))
            tree.column(cid, width=w, anchor="center")
        vsb = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        if hscroll:
            hsb = ttk.Scrollbar(parent, orient="horizontal", command=tree.xview)
            tree.configure(xscrollcommand=hsb.set)
            hsb.pack(side="bottom", fill="x")
        vsb.pack(side="right", fill="y")
        tree.pack(fill="both", expand=True)
        return tree

    def _sort(self, tree, col):
        key = (id(tree), col)
        rev = self._sort_rev.get(key, False)
        items = [(tree.set(k, col), k) for k in tree.get_children("")]
        try:
            items.sort(
                key=lambda x: float(x[0].replace(",","").replace("–","0")
                                    .replace("+","").replace("s","").replace(":",".")),
                reverse=rev)
        except:
            items.sort(key=lambda x: x[0], reverse=rev)
        for i, (_, k) in enumerate(items): tree.move(k, "", i)
        self._sort_rev[key] = not rev

    def _log(self, msg, tag="info"):
        def _do():
            self.log_text.config(state="normal")
            self.log_text.insert("end", f"[{datetime.now():%H:%M:%S}]  {msg}\n", tag)
            self.log_text.see("end")
            self.log_text.config(state="disabled")
        self.after(0, _do)

    def _set_status(self, msg, prog=None, label=None):
        def _do():
            self.status_var.set(msg)
            if prog  is not None: self.progress_var.set(prog)
            if label is not None: self.prog_label.config(text=label)
        self.after(0, _do)

    # ── 검색 제어 ────────────────────────────────
    def _start_search(self):
        if not self.api_key_var.get().strip():
            messagebox.showwarning("API 키 필요", "Riot API 키를 입력해 주세요.")
            return
        self._stop_flag = False
        self.search_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        for t in (self.tree_summary, self.tree_detail, self.tree_timeline,
                  self.tree_penta_list, self.tree_cam_penta,
                  self.tree_bs_penta, self.tree_thumb_penta):
            t.delete(*t.get_children())
        self._penta_replay_entries.clear()
        for k, v in self.stat_cards.items():
            v.config(text="–" if k == "best_champion" else "0")
        self.progress_var.set(0)
        platform, region = REGIONS[self.region_var.get()]
        threading.Thread(
            target=self._worker,
            args=(self.api_key_var.get().strip(), platform, region,
                  self.tier_var.get(), self.match_count_var.get(), self.sum_limit_var.get()),
            daemon=True).start()

    def _stop_search(self):
        self._stop_flag = True
        self._log("사용자가 검색을 중지했습니다.", "warn")

    def _done(self):
        self.after(0, lambda: (
            self.search_btn.config(state="normal"),
            self.stop_btn.config(state="disabled")))

    # ════════════════════════════════════════════
    #  메인 워커
    # ════════════════════════════════════════════
    def _worker(self, api_key, platform, region, tier, match_count, sum_limit):
        api = RiotAPI(api_key, platform, region)

        try:
            self._log(f"[{tier}] 리그 정보 로딩…", "info")
            self._set_status(f"{tier} 리그 로딩…")
            entries = api.get_league(tier)
        except Exception as e:
            self._log(f"리그 오류: {e}", "error")
            self.after(0, lambda: messagebox.showerror("오류", str(e)))
            self._done(); return

        entries.sort(key=lambda x: x.get("leaguePoints", 0), reverse=True)
        entries = entries[:sum_limit]
        total_s = len(entries)
        self._log(f"대상 {total_s}명 (최근 {match_count}판)", "info")

        # ── 1단계 ──
        self._log("━━━ 1단계: PUUID & 매치 ID 수집", "warn")
        summoner_info   = {}
        match_to_puuids = {}

        for idx, entry in enumerate(entries, 1):
            if self._stop_flag: self._done(); return
            sname = entry.get("summonerName", entry.get("summonerId", "Unknown"))
            sid   = entry.get("summonerId", "")
            lp    = entry.get("leaguePoints", 0)
            self._set_status(f"[1단계 {idx}/{total_s}] {sname}…",
                             idx / total_s * 30, f"1단계 {idx}/{total_s}")
            try:
                puuid = api.get_summoner(sid)["puuid"]
                mids  = api.get_match_ids(puuid, match_count)
                summoner_info[puuid] = {"name": sname, "lp": lp, "match_ids": mids}
                for mid in mids:
                    match_to_puuids.setdefault(mid, set()).add(puuid)
                self._log(f"  [{idx}/{total_s}] {sname} ({lp}LP) — {len(mids)}게임", "info")
            except Exception as e:
                self._log(f"  ⚠ {sname}: {e}", "error")

        total_raw   = sum(len(v["match_ids"]) for v in summoner_info.values())
        unique_mids = list(match_to_puuids.keys())
        total_uniq  = len(unique_mids)
        saved_pct   = (total_raw - total_uniq) / total_raw * 100 if total_raw else 0
        self._log(f"━━━ 원본 {total_raw:,}건 → 유니크 {total_uniq:,}건 (절감 {saved_pct:.1f}%)", "ok")

        # ── 2단계 ──
        self._log("━━━ 2단계: 유니크 매치 분석", "warn")
        results = {p: {"pentas": 0, "details": [], "penta_matches": []}
                   for p in summoner_info}
        champ_counter = {}

        for m_idx, mid in enumerate(unique_mids, 1):
            if self._stop_flag: break
            self._set_status(f"[2단계 {m_idx}/{total_uniq}] 매치 분석…",
                             30 + m_idx / total_uniq * 38, f"2단계 {m_idx}/{total_uniq}")
            try:
                match    = api.get_match(mid)
                info     = match["info"]
                dur_str  = f"{info['gameDuration'] // 60}분"
                date_str = datetime.fromtimestamp(info["gameCreation"] / 1000).strftime("%Y-%m-%d")
                targets  = match_to_puuids[mid]
                game_id  = match_id_to_game_id(mid)   # ← 리플레이 점프용

                pid_to_name = {
                    p["participantId"]: p.get("summonerName", f"P{p['participantId']}")
                    for p in info["participants"]
                }
                pid_to_champion = {
                    p["participantId"]: p.get("championName", "Unknown")
                    for p in info["participants"]
                }

                for p in info["participants"]:
                    if p["puuid"] not in targets: continue
                    pentas = p.get("pentaKills", 0)
                    puuid  = p["puuid"]
                    if pentas > 0:
                        results[puuid]["pentas"] += pentas
                        champ = p["championName"]
                        champ_counter[champ] = champ_counter.get(champ, 0) + pentas
                        results[puuid]["details"].append({
                            "champion": champ, "pentas": pentas,
                            "kda":  f"{p['kills']}/{p['deaths']}/{p['assists']}",
                            "win":  p["win"], "duration": dur_str, "date": date_str,
                        })
                        results[puuid]["penta_matches"].append({
                            "puuid":           puuid,
                            "match_id":        mid,
                            "game_id":         game_id,
                            "part_id":         p["participantId"],
                            "pid_to_name":     dict(pid_to_name),
                            "pid_to_champion": dict(pid_to_champion),
                            "champion":        champ,
                            "date":            date_str,
                            "sname":           summoner_info[puuid]["name"],
                        })
            except Exception as e:
                self._log(f"  ⚠ {mid}: {e}", "error")

        # ── 2.5단계: 타임라인 fetch ──
        self._log("━━━ 2.5단계: 펜타킬 타임라인 fetch", "warn")
        tl_jobs = {}
        for puuid, res in results.items():
            for pm in res["penta_matches"]:
                tl_jobs.setdefault(pm["match_id"], []).append(pm)

        tl_total   = len(tl_jobs)
        tl_fetched = 0
        tl_results = {p: [] for p in summoner_info}

        for tl_idx, (mid, jobs) in enumerate(tl_jobs.items(), 1):
            if self._stop_flag: break
            self._set_status(f"[2.5단계 {tl_idx}/{tl_total}] 타임라인 fetch…",
                             68 + tl_idx / tl_total * 22, f"타임라인 {tl_idx}/{tl_total}")
            try:
                timeline = api.get_timeline(mid)
                tl_fetched += 1
                for job in jobs:
                    seqs = extract_pentakill_sequences(
                        timeline, job["part_id"], job["pid_to_name"],
                        job.get("pid_to_champion", {}))
                    for s_idx, seq in enumerate(seqs, 1):
                        entry = {
                            "penta_idx": s_idx,
                            "champion":  job["champion"],
                            "date":      job["date"],
                            "sname":     job["sname"],
                            "game_id":   job["game_id"],    # ← 리플레이 점프용
                            "kills":     seq,
                        }
                        tl_results[job["puuid"]].append(entry)
                self._log(f"  타임라인 [{tl_idx}/{tl_total}] {mid}", "info")
            except Exception as e:
                self._log(f"  ⚠ 타임라인 {mid}: {e}", "error")

        # ── 3단계: UI 반영 ──
        self._log("━━━ 3단계: 결과 UI 반영", "warn")
        penta_summoners = total_pentas = 0

        for rank, (puuid, sinfo) in enumerate(
                sorted(summoner_info.items(), key=lambda x: x[1]["lp"], reverse=True), 1):
            sname  = sinfo["name"]
            lp     = sinfo["lp"]
            pentas = results[puuid]["pentas"]
            total_pentas += pentas
            if pentas > 0: penta_summoners += 1

            tag = "penta" if pentas > 0 else "nopenta"
            self.after(0, lambda r=rank, sn=sname, l=lp, p=pentas, m=len(sinfo["match_ids"]), tg=tag: (
                self.tree_summary.insert("", "end",
                    values=(r, sn, tier, f"{l:,}", p, m), tags=(tg,))
            ))
            for d in results[puuid]["details"]:
                has_tl = "✔" if tl_results.get(puuid) else "–"
                wt = "win" if d["win"] else "loss"
                rt = "✔ 승" if d["win"] else "✘ 패"
                self.after(0,
                    lambda sn=sname, ch=d["champion"], kda=d["kda"],
                           p=d["pentas"], rt=rt, dur=d["duration"],
                           dt=d["date"], wt=wt, ht=has_tl: (
                        self.tree_detail.insert("", "end",
                            values=(sn, ch, kda, p, rt, dur, dt, ht), tags=(wt,))
                    ))
                self.after(0,
                    lambda sn=sname, ch=d["champion"], kda=d["kda"]: (
                        self.tree_thumb_penta.insert("", "end",
                            values=(sn, ch, kda, "0.0"))
                    ))

        # 타임라인 탭 + 리플레이 목록 탭
        kill_event_count = 0
        for puuid, tl_list in tl_results.items():
            for entry in tl_list:
                first_kill_ts = entry["kills"][0]["timestamp_s"]
                gid = entry.get("game_id")

                # 리플레이 탭 목록에 추가 (펜타킬 확정 킬 = 5번째 기준)
                penta_ts = entry["kills"][4]["timestamp_s"]  # 5번째 킬 타임스탬프
                gt_str   = entry["kills"][4]["game_time"]

                self.after(0,
                    lambda sn=entry["sname"], ch=entry["champion"],
                           gt=gt_str, dt=entry["date"],
                           gid=gid, ts=penta_ts: (
                        self.tree_penta_list.insert("", "end",
                            values=(sn, ch, gt, dt,
                                    gid if gid else "–",
                                    f"{ts:.1f}"),
                            tags=("no_replay",)),
                        self.tree_cam_penta.insert("", "end",
                            values=(sn, ch, gt, f"{ts:.1f}")),
                        self.tree_bs_penta.insert("", "end",
                            values=(sn, ch, gt, f"{ts:.1f}")),
                    ))

                for kill in entry["kills"]:
                    kn  = kill["kill_num"]
                    kill_event_count += 1
                    self.after(0,
                        lambda sn=entry["sname"], ch=entry["champion"],
                               dt=entry["date"], pn=entry["penta_idx"], knum=kn,
                               gt=kill["game_time"], iv=kill["interval_s"],
                               vic=kill["victim_name"], z=kill["zone"],
                               cx=kill["pos_x"], cy=kill["pos_y"], tg=f"kill{kn}": (
                            self.tree_timeline.insert("", "end",
                                values=(sn, ch, dt, pn,
                                        f"{'⚔' * knum} {knum}킬",
                                        gt, iv, vic, z, f"({cx}, {cy})"),
                                tags=(tg,))
                        ))

        best_champ = max(champ_counter, key=champ_counter.get) if champ_counter else "–"
        self.after(0, lambda ts=total_s, ps=penta_summoners, tp=total_pentas,
                   tf=tl_fetched, ke=kill_event_count, bc=best_champ: (
            self.stat_cards["total_summoners"].config(text=str(ts)),
            self.stat_cards["penta_summoners"].config(text=str(ps)),
            self.stat_cards["total_pentas"].config(text=str(tp)),
            self.stat_cards["timeline_fetched"].config(text=str(tf)),
            self.stat_cards["kill_events"].config(text=str(ke)),
            self.stat_cards["best_champion"].config(text=bc),
        ))
        # LCU 연결 중이면 태그 갱신
        self.after(500, self._update_replay_list_tags)

        # ── 세션 데이터 수집 (저장용) ──────────────────────────
        self._session_data = {
            "meta": {
                "saved_at":        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "tier":            tier,
                "region":          self.region_var.get(),
                "match_count":     match_count,
                "total_summoners": total_s,
            },
            "stats": {
                "total_summoners":  total_s,
                "penta_summoners":  penta_summoners,
                "total_pentas":     total_pentas,
                "timeline_fetched": tl_fetched,
                "kill_events":      kill_event_count,
                "best_champion":    best_champ,
            },
            "summary":   [],
            "detail":    [],
            "timeline":  [],
            "penta_list":[],
        }
        # 트리 데이터를 세션에 백업
        for row in self.tree_summary.get_children():
            self._session_data["summary"].append(
                self.tree_summary.item(row, "values"))
        for row in self.tree_detail.get_children():
            self._session_data["detail"].append(
                list(self.tree_detail.item(row, "values")) +
                [self.tree_detail.item(row, "tags")[0] if
                 self.tree_detail.item(row, "tags") else ""])
        for row in self.tree_timeline.get_children():
            self._session_data["timeline"].append(
                list(self.tree_timeline.item(row, "values")) +
                [self.tree_timeline.item(row, "tags")[0] if
                 self.tree_timeline.item(row, "tags") else ""])
        for row in self.tree_penta_list.get_children():
            self._session_data["penta_list"].append(
                self.tree_penta_list.item(row, "values"))

        # 자동 저장 (마지막 검색 결과)
        self._autosave_session()

        self._set_status(
            f"✅ 완료! 절감 {saved_pct:.1f}%  |  타임라인 {tl_fetched}매치  |  킬 이벤트 {kill_event_count}개",
            100, "완료")
        self._log(
            f"검색 완료 | 달성자 {penta_summoners}명 / 총 {total_pentas}회 / "
            f"타임라인 {tl_fetched}매치 / 킬 이벤트 {kill_event_count}개", "ok")
        self._done()



    # ════════════════════════════════════════════
    #  세션 저장 / 불러오기
    # ════════════════════════════════════════════

    AUTOSAVE_PATH = "penta_autosave.json"

    def _autosave_session(self):
        try:
            with open(self.AUTOSAVE_PATH, "w", encoding="utf-8") as f:
                json.dump(self._session_data, f, ensure_ascii=False, indent=2)
            self.after(0, lambda: self.session_file_var.set(
                f"자동저장: {self.AUTOSAVE_PATH}  "
                f"({self._session_data['meta']['saved_at']})"))
            self._log(f"[저장] 자동 저장 완료 → {self.AUTOSAVE_PATH}", "ok")
        except Exception as e:
            self._log(f"[저장] 자동 저장 오류: {e}", "error")

    def _save_session(self):
        if not self._session_data:
            messagebox.showwarning("데이터 없음",
                "저장할 데이터가 없습니다.\n먼저 검색을 실행해 주세요.")
            return
        path = filedialog.asksaveasfilename(
            title="세션 저장",
            defaultextension=".json",
            initialfile=f"penta_{self._session_data['meta']['tier']}_"
                        f"{self._session_data['meta']['saved_at'][:10]}.json",
            filetypes=[("JSON", "*.json"), ("모든 파일", "*.*")])
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self._session_data, f, ensure_ascii=False, indent=2)
            self.session_file_var.set(f"저장됨: {os.path.basename(path)}")
            self._log(f"[저장] 세션 저장 완료 → {path}", "ok")
            messagebox.showinfo("저장 완료",
                f"저장 완료!\n{path}\n\n"
                f"소환사: {self._session_data['stats']['total_summoners']}명  |  "
                f"펜타킬: {self._session_data['stats']['total_pentas']}회")
        except Exception as e:
            messagebox.showerror("저장 오류", str(e))

    def _load_session(self):
        path = filedialog.askopenfilename(
            title="세션 불러오기",
            filetypes=[("JSON", "*.json"), ("모든 파일", "*.*")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._restore_session(data, path)
        except json.JSONDecodeError:
            messagebox.showerror("파일 오류", "올바른 JSON 파일이 아닙니다.")
        except Exception as e:
            messagebox.showerror("불러오기 오류", str(e))

    def _restore_session(self, data: dict, path: str):
        meta  = data.get("meta",  {})
        stats = data.get("stats", {})

        for t in (self.tree_summary, self.tree_detail, self.tree_timeline,
                  self.tree_penta_list, self.tree_cam_penta,
                  self.tree_bs_penta, self.tree_thumb_penta):
            t.delete(*t.get_children())
        self._penta_replay_entries.clear()

        for row in data.get("summary", []):
            if len(row) >= 6:
                tag = "penta" if str(row[4]) != "0" else "nopenta"
                self.tree_summary.insert("", "end", values=tuple(row), tags=(tag,))

        for row in data.get("detail", []):
            if len(row) >= 8:
                vals = row[:8]
                tag  = row[8] if len(row) > 8 else "win"
                self.tree_detail.insert("", "end", values=tuple(vals), tags=(tag,))

        for row in data.get("timeline", []):
            if len(row) >= 10:
                vals = row[:10]
                tag  = row[10] if len(row) > 10 else "kill1"
                self.tree_timeline.insert("", "end", values=tuple(vals), tags=(tag,))

        for row in data.get("penta_list", []):
            if len(row) >= 6:
                sn, ch, gt, dt, gid, ts = row[:6]
                self.tree_penta_list.insert("", "end",
                    values=(sn, ch, gt, dt, gid, ts), tags=("no_replay",))
                self.tree_cam_penta.insert("", "end", values=(sn, ch, gt, ts))
                self.tree_bs_penta.insert("", "end",  values=(sn, ch, gt, ts))
                self.tree_thumb_penta.insert("", "end", values=(sn, ch, "–", ts))

        for key in ("total_summoners", "penta_summoners", "total_pentas",
                    "timeline_fetched", "kill_events", "best_champion"):
            if key in stats and key in self.stat_cards:
                self.stat_cards[key].config(text=str(stats[key]))

        if "region" in meta: self.region_var.set(meta["region"])
        if "tier"   in meta: self.tier_var.set(meta["tier"])

        self._session_data = data
        saved_at = meta.get("saved_at", "알 수 없음")
        tier     = meta.get("tier",     "–")
        region   = meta.get("region",   "–")
        fname    = os.path.basename(path)

        self.session_file_var.set(f"불러옴: {fname}  ({saved_at})")
        self.status_var.set(
            f"✅ 세션 불러오기 완료  |  {tier} {region}  |  저장: {saved_at}")
        self._log(
            f"[불러오기] {fname} 복원 완료 | "
            f"소환사 {stats.get('total_summoners',0)}명 / "
            f"펜타킬 {stats.get('total_pentas',0)}회", "ok")
        self.after(300, self._update_replay_list_tags)
        messagebox.showinfo("불러오기 완료",
            f"세션 복원 완료!\n\n"
            f"저장 시각:  {saved_at}\n"
            f"티어/지역:  {tier} / {region}\n"
            f"소환사:     {stats.get('total_summoners',0)}명\n"
            f"펜타킬:     {stats.get('total_pentas',0)}회\n"
            f"킬 이벤트: {stats.get('kill_events',0)}개")



if __name__ == "__main__":
    app = PentakillTracker()
    autosave = PentakillTracker.AUTOSAVE_PATH
    if os.path.exists(autosave):
        try:
            with open(autosave, "r", encoding="utf-8") as f:
                saved = json.load(f)
            meta = saved.get("meta", {})
            stats = saved.get("stats", {})
            if messagebox.askyesno("자동저장 발견",
                f"마지막 검색 결과를 불러올까요?\n\n"
                f"저장 시각: {meta.get('saved_at','알 수 없음')}\n"
                f"티어: {meta.get('tier','?')}  지역: {meta.get('region','?')}\n"
                f"소환사: {stats.get('total_summoners',0)}명  "
                f"펜타킬: {stats.get('total_pentas',0)}회"):
                app._restore_session(saved, autosave)
        except Exception:
            pass
    app.mainloop()
