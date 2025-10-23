from flask import Flask, request
from threading import Thread, Lock
import os, time, queue
from datetime import datetime
import tkinter as tk
from tkinter import ttk, scrolledtext

# --- Flask server setup ---
app = Flask(__name__)
DATA_DIR = "received"
PORT = 8081
STALE_SEC = 20  # consider client offline if no uploads within this many seconds
os.makedirs(DATA_DIR, exist_ok=True)

_clients = {}
_clients_lock = Lock()
_log_q = queue.Queue()


def _log(msg: str):
    _log_q.put(f"{datetime.now().strftime('%H:%M:%S')} {msg}")


@app.route("/<client_id>/<monitor_num>/upload", methods=["POST"])
def upload(client_id: str, monitor_num: str):
    # Save to received/<client_id>/<YYYYMMDD>/<monitor_num>/
    date_str = datetime.now().strftime("%Y%m%d")
    mon_folder = os.path.join(DATA_DIR, client_id, date_str, monitor_num)
    os.makedirs(mon_folder, exist_ok=True)

    saved_count = 0
    for file_key in request.files:
        f = request.files[file_key]
        ts = datetime.now().strftime("%Y%m%d%H%M%S%f")
        filename = f"{ts}_{file_key}.webp"
        f.save(os.path.join(mon_folder, filename))
        saved_count += 1

    now = time.time()
    with _clients_lock:
        client = _clients.get(client_id)
        if not client:
            client = {"monitors": {}}
            _clients[client_id] = client
            _log(f"New client discovered: {client_id}")
        mon_key = str(monitor_num)
        mon_entry = client["monitors"].get(mon_key)
        if not mon_entry:
            mon_entry = {"last_seen": 0.0, "uploads": 0, "status": "red"}
            client["monitors"][mon_key] = mon_entry
            _log(f"{client_id} monitor {monitor_num} discovered")
        mon_entry["last_seen"] = now
        mon_entry["uploads"] += saved_count

    _log(f"{client_id} m{monitor_num}: received {saved_count} file(s)")
    return "OK", 200


def _run_flask():
    _log(f"Server starting on 0.0.0.0:{PORT}")
    app.run(host="0.0.0.0", port=PORT, threaded=True, debug=False, use_reloader=False)


# --- Tkinter GUI ---
def _format_age(ts: float) -> str:
    d = max(0, int(time.time() - ts))
    return f"{d}s" if d < 60 else f"{d//60}m{d%60:02d}s"


def _launch_gui():
    root = tk.Tk()
    root.title("SilentBeam Server")
    root.geometry("780x520")

    frame = ttk.Frame(root)
    frame.pack(fill="both", expand=True, padx=8, pady=8)

    # Bigger row height and emoji-capable font for larger colored circles
    style = ttk.Style(root)
    try:
        style.configure("Treeview", rowheight=32, font=("Segoe UI Emoji", 14))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
    except Exception:
        style.configure("Treeview", rowheight=32)

    cols = ("status", "client", "monitors", "last_seen", "uploads")
    tree = ttk.Treeview(frame, columns=cols, show="headings", height=12)
    tree.heading("status", text="Status")
    tree.heading("client", text="Client")
    tree.heading("monitors", text="Monitors")
    tree.heading("last_seen", text="Last Seen")
    tree.heading("uploads", text="Uploads")
    tree.column("status", width=80, anchor="center")
    tree.column("client", width=260)
    tree.column("monitors", width=220, anchor="center")
    tree.column("last_seen", width=120, anchor="center")
    tree.column("uploads", width=90, anchor="center")
    tree.tag_configure("green", foreground="green")
    tree.tag_configure("red", foreground="red")
    tree.pack(fill="both", expand=True)

    ttk.Label(frame, text="Log").pack(anchor="w", pady=(8, 0))
    logbox = scrolledtext.ScrolledText(frame, height=10, state="disabled")
    logbox.pack(fill="both", expand=False)

    def refresh_clients():
        now = time.time()
        with _clients_lock:
            snapshot = {
                cid: {"monitors": {mk: me.copy() for mk, me in c.get("monitors", {}).items()}}
                for cid, c in _clients.items()
            }
        # One row per client; aggregate monitor statuses as emojis
        for cid, data in snapshot.items():
            monitors = data.get("monitors", {})
            mon_parts = []
            overall_green = False
            latest_seen = 0.0
            total_uploads = 0
            # Sort monitors numerically when possible
            for mk, me in sorted(monitors.items(), key=lambda kv: int(kv[0]) if str(kv[0]).isdigit() else str(kv[0])):
                is_green = (now - me.get("last_seen", 0)) <= STALE_SEC
                emoji = "\U0001F7E2" if is_green else "\U0001F534"  # 🟢 / 🔴
                mon_parts.append(f"{mk}:{emoji}")
                overall_green = overall_green or is_green
                latest_seen = max(latest_seen, me.get("last_seen", 0))
                total_uploads += int(me.get("uploads", 0))
                # Update stored status and log transitions per monitor
                with _clients_lock:
                    current = _clients.get(cid, {}).get("monitors", {}).get(mk, {}).get("status")
                    desired = "green" if is_green else "red"
                    if current != desired:
                        _clients[cid]["monitors"][mk]["status"] = desired
                        _log(f"{cid} monitor {mk} status -> {desired.upper()}")
            overall_status = "green" if overall_green else "red"
            status_emoji = "\U0001F7E2" if overall_green else "\U0001F534"
            vals = (
                status_emoji,
                cid,
                " ".join(mon_parts) if mon_parts else "-",
                _format_age(latest_seen) if latest_seen else "-",
                total_uploads,
            )
            if tree.exists(cid):
                tree.item(cid, values=vals, tags=(overall_status,))
            else:
                tree.insert("", "end", iid=cid, values=vals, tags=(overall_status,))
        root.after(1000, refresh_clients)

    def pump_logs():
        changed = False
        while True:
            try:
                msg = _log_q.get_nowait()
            except queue.Empty:
                break
            else:
                if not changed:
                    logbox.configure(state="normal")
                    changed = True
                logbox.insert("end", msg + "\n")
        if changed:
            logbox.see("end")
            logbox.configure(state="disabled")
        root.after(250, pump_logs)

    root.after(250, pump_logs)
    root.after(1000, refresh_clients)
    root.mainloop()


if __name__ == "__main__":
    t = Thread(target=_run_flask, daemon=True)
    t.start()
    _launch_gui()
