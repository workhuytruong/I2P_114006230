import queue
import requests
import threading
import time
from src.utils import Logger, GameSettings

POLL_INTERVAL = 0.4  # relaxed to reduce load
POLL_INTERVAL_IDLE = 1.0
UPDATE_INTERVAL = 0.1  # up to 10 Hz when moving
KEEPALIVE_INTERVAL = 1.0

class OnlineManager:
    list_players: list[dict]
    player_id: int
    
    _stop_event: threading.Event
    _thread: threading.Thread | None
    _send_thread: threading.Thread | None
    _lock: threading.Lock
    _session: requests.Session
    _poll_session: requests.Session
    _send_queue: queue.Queue
    
    def __init__(self):
        self.base: str = GameSettings.ONLINE_SERVER_URL
        self.player_id = -1
        self.list_players = []

        self._thread = None
        self._send_thread = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._on_error = None
        self._session = requests.Session()
        self._poll_session = requests.Session()
        self._send_queue = queue.Queue(maxsize=1)
        self._last_sent_state: dict | None = None
        self._last_send_time: float = 0.0
        Logger.info("OnlineManager initialized")
        
    def enter(self):
        self.register()
        self.start()
            
    def exit(self):
        self.stop()
        
    def get_list_players(self) -> list[dict]:
        with self._lock:
            return list(self.list_players)

    # Chat API
    def send_chat(self, text: str) -> bool:
        if self.player_id == -1:
            return False
        payload = {"id": self.player_id, "text": str(text)}
        try:
            resp = self._session.post(f"{self.base}/chat", json=payload, timeout=(0.2, 0.5))
            return resp.status_code == 200
        except Exception as e:
            Logger.warning(f"Online chat send error: {e}")
            return False

    def get_recent_chat(self, since_id: int, limit: int = 50) -> list[dict]:
        try:
            resp = self._poll_session.get(
                f"{self.base}/chat",
                params={"since": since_id, "limit": limit},
                timeout=(0.2, 0.5),
            )
            if resp.status_code == 200:
                return resp.json().get("messages", [])
        except Exception as e:
            Logger.warning(f"Online chat poll error: {e}")
        return []
    
    # ------------------------------------------------------------------
    # Threading and API Calling Below
    # ------------------------------------------------------------------
    def register(self):
        try:
            url = f"{self.base}/register"
            resp = requests.get(url, timeout=1)
            resp.raise_for_status()
            data = resp.json()
            if resp.status_code == 200:
                self.player_id = data["id"]
                Logger.info(f"OnlineManager registered with id={self.player_id}")
            else:
                Logger.error("Registration failed:", data)
        except Exception as e:
            Logger.warning(f"OnlineManager registration error: {e}")
        return

    def update(self, x: float, y: float, map_name: str, direction: str, moving: bool) -> bool:
        if self.player_id == -1:
            # Try to register again
            return False
        
        url = f"{self.base}/players"
        body = {"id": self.player_id, "x": x, "y": y, "map": map_name, "direction": direction, "moving": moving}
        now = time.monotonic()
        # skip if unchanged and keepalive not due
        if self._last_sent_state == body and (now - self._last_send_time) < KEEPALIVE_INTERVAL:
            return True
        try:
            self._send_queue.put_nowait(body)
        except queue.Full:
            try:
                _ = self._send_queue.get_nowait()
            except queue.Empty:
                pass
            try:
                self._send_queue.put_nowait(body)
            except queue.Full:
                pass
        return True

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._loop,
            name="OnlineManagerPoller",
            daemon=True
        )
        self._thread.start()
        # Sender thread for outgoing updates
        self._send_thread = threading.Thread(
            target=self._send_loop,
            name="OnlineManagerSender",
            daemon=True
        )
        self._send_thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        if self._send_thread and self._send_thread.is_alive():
            self._send_thread.join(timeout=2)

    def _loop(self) -> None:
        idle_intervals = 0
        while not self._stop_event.wait(POLL_INTERVAL if idle_intervals < 3 else POLL_INTERVAL_IDLE):
            moved = self._fetch_players()
            if moved:
                idle_intervals = 0
            else:
                idle_intervals += 1

    def _send_loop(self) -> None:
        last_send = 0.0
        while not self._stop_event.is_set():
            try:
                body = self._send_queue.get(timeout=UPDATE_INTERVAL)
            except queue.Empty:
                continue

            # keep only the newest state if multiple queued
            while True:
                try:
                    body = self._send_queue.get_nowait()
                except queue.Empty:
                    break

            now = time.monotonic()
            wait_time = UPDATE_INTERVAL - (now - last_send)
            if wait_time > 0 and self._stop_event.wait(wait_time):
                break

            self._send_player_state(body)
            last_send = time.monotonic()
            self._last_send_time = last_send
            self._last_sent_state = body.copy()

    def _send_player_state(self, body: dict) -> None:
        try:
            resp = self._session.post(f"{self.base}/players", json=body, timeout=(0.2, 0.5))
            if resp.status_code != 200:
                Logger.warning(f"Update failed: {resp.status_code} {resp.text}")
        except Exception as e:
            if self._on_error:
                try:
                    self._on_error(e)
                except Exception:
                    pass
            Logger.warning(f"Online update error: {e}")
            
    def _fetch_players(self) -> bool:
        try:
            url = f"{self.base}/players"
            resp = self._poll_session.get(url, timeout=(0.2, 0.5))
            resp.raise_for_status()
            all_players = resp.json().get("players", [])

            pid = self.player_id
            filtered = [p for key, p in all_players.items() if int(key) != pid]
            with self._lock:
                self.list_players = filtered

            return any(p.get("moving") for p in filtered)
        except Exception as e:
            Logger.warning(f"OnlineManager fetch error: {e}")
        return False
