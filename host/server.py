from flask import Flask, request
from threading import Thread, Lock
import os, time, queue
from datetime import datetime
import tkinter as tk
from tkinter import ttk, scrolledtext, font as tkfont

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
        just_created = False
        if not mon_entry:
            mon_entry = {"last_seen": 0.0, "uploads": 0, "status": "red"}
            client["monitors"][mon_key] = mon_entry
            just_created = True
            _log(f"{client_id} monitor {monitor_num} discovered")
        mon_entry["last_seen"] = now
        mon_entry["uploads"] += saved_count
        if just_created:
            # Include initial per-monitor stats in the log once it's registered
            try:
                age = _format_age(mon_entry["last_seen"]) if mon_entry["last_seen"] else "-"
            except Exception:
                age = "0s"
            _log(f"{client_id} monitor {monitor_num} registered: last_seen={age}, uploads={mon_entry['uploads']}")

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
    root.geometry("680x520")

    # Use a vertical PanedWindow so status table and log are same size and both scrollable
    pw = ttk.Panedwindow(root, orient=tk.VERTICAL)
    pw.pack(fill="both", expand=True, padx=8, pady=8)

    top = ttk.Frame(pw)
    bottom = ttk.Frame(pw)
    pw.add(top, weight=1)
    pw.add(bottom, weight=1)

    # Bigger row height and emoji-capable font for larger colored circles
    style = ttk.Style(root)
    try:
        style.configure("Treeview", rowheight=26, font=("Segoe UI Emoji", 12))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
    except Exception:
        style.configure("Treeview", rowheight=26)

    cols = ("status", "last_seen", "uploads")
    tree = ttk.Treeview(top, columns=cols, show="tree headings")
    tree.heading("#0", text="Client / Monitor")
    tree.heading("status", text="Status")
    tree.heading("last_seen", text="Last Seen")
    tree.heading("uploads", text="Uploads")
    tree.column("#0", width=220)
    tree.column("status", width=64, anchor="center")
    tree.column("last_seen", width=100, anchor="center")
    tree.column("uploads", width=80, anchor="center")
    tree.tag_configure("green", foreground="green")
    tree.tag_configure("red", foreground="red")

    # Add vertical scrollbar for the status table
    tree_ys = ttk.Scrollbar(top, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=tree_ys.set)

    top.rowconfigure(0, weight=1)

    top.columnconfigure(0, weight=1)
    tree.grid(row=0, column=0, sticky="nsew")
    tree_ys.grid(row=0, column=1, sticky="ns")

    # Log area in the bottom pane (already scrollable)
    bottom.rowconfigure(0, weight=1)
    bottom.columnconfigure(0, weight=1)
    logbox = scrolledtext.ScrolledText(bottom, state="disabled")
    logbox.grid(row=0, column=0, sticky="nsew")

    # Make status table font size match the log's font size
    try:
        log_font = tkfont.nametofont(logbox.cget("font"))
        _size = int(log_font.cget("size"))
        if _size <= 0:
            _size = 10
        style.configure("Treeview", font=("Segoe UI Emoji", _size))
        style.configure("Treeview", rowheight=max(20, _size + 8))
    except Exception:
        pass

    def refresh_clients():
        now = time.time()
        with _clients_lock:
            snapshot = {
                cid: {"monitors": {mk: me.copy() for mk, me in c.get("monitors", {}).items()}}
                for cid, c in _clients.items()
            }
        # Group by client (parent row) with one child row per monitor
        for cid, data in snapshot.items():

            monitors = data.get("monitors", {})
            overall_green = False
            latest_seen = 0.0
            total_uploads = 0

            # Ensure parent row exists and is expanded
            if not tree.exists(cid):
                tree.insert("", "end", iid=cid, text=cid, open=True)
            else:
                tree.item(cid, open=True)

            # Per-monitor child rows
            for mk, me in sorted(monitors.items(), key=lambda kv: int(kv[0]) if str(kv[0]).isdigit() else str(kv[0])):
                last_seen = me.get("last_seen", 0)
                uploads = int(me.get("uploads", 0))
                is_green = (now - last_seen) <= STALE_SEC
                emoji = "\U0001F7E2" if is_green else "\U0001F534"
                overall_green = overall_green or is_green
                latest_seen = max(latest_seen, last_seen)
                total_uploads += uploads

                row_id = f"{cid}:{mk}"
                vals = (emoji, _format_age(last_seen) if last_seen else "-", uploads)
                if tree.exists(row_id):
                    tree.item(row_id, values=vals, tags=(("green" if is_green else "red"),))
                else:
                    tree.insert(cid, "end", iid=row_id, text=f"Monitor {mk}", values=vals, tags=(("green" if is_green else "red"),))

                # Update stored status and log transitions per monitor
                with _clients_lock:
                    current = _clients.get(cid, {}).get("monitors", {}).get(mk, {}).get("status")
                    desired = "green" if is_green else "red"
                    if current != desired:
                        _clients[cid]["monitors"][mk]["status"] = desired
                        _log(f"{cid} monitor {mk} status -> {desired.upper()}")

            # Update parent row aggregate
            overall_status = "green" if overall_green else "red"
            status_emoji = "\U0001F7E2" if overall_green else "\U0001F534"
            parent_vals = (status_emoji, _format_age(latest_seen) if latest_seen else "-", total_uploads)
            tree.item(cid, values=parent_vals, tags=(overall_status,))

        tree.update_idletasks()
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
