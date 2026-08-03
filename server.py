#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
局域网文件共享服务器 (LAN File Sharing Server)
================================================

运行方式:
    python server.py                 # 默认 0.0.0.0:8000
    python server.py --port 9000     # 指定端口
    python server.py --host 0.0.0.0 --port 8000

功能:
  1. 用户通过浏览器连入后, 服务器返回其局域网 IP (client_address)。
  2. 显示同一局域网内 "在线" 的其它用户 IP (基于最近访问时间)。
  3. 支持批量上传文件 (multipart/form-data)。
  4. 用户可从 "我的文件" 中勾选, 并指定一个目标 IP, 把文件推送给对方。
  5. 接收方在 "收件箱" 看到来自他人的文件并可下载。
  6. 每一次操作 (上传 / 发送 / 下载 / 删除 / 上线) 都写入 logs/uploader_YYYY-MM-DD.log。
  7. 前端 index.html / style.css / app.js 三者分离, 自适应电脑与手机。

说明:
  - 所有人连接的是同一台运行本服务器的机器 (服务器即中转枢纽), 因此服务器掌握每个客户端的 IP。
  - 主机自身在浏览器中用 http://<本机局域网IP>:<端口> 打开, 即可看到自己的真实局域网 IP。
"""

import argparse
import atexit
import datetime
import json
import mimetypes
import os
import re
import socket
import sys
import threading
import traceback
from email.parser import BytesParser
from email.policy import default
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, quote, parse_qs

# --------------------------------------------------------------------------- #
# 路径与常量
# --------------------------------------------------------------------------- #
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
LOG_DIR = os.path.join(BASE_DIR, "logs")
FILES_DB = os.path.join(BASE_DIR, "files.json")
PEERS_DB = os.path.join(BASE_DIR, "peers.json")

ONLINE_WINDOW = 10 * 60          # 多少秒内有访问记录算 "在线"
MAX_UPLOAD = 50 * 1024 * 1024 * 1024   # 单次上传防御性上限 50GB（实际取决于服务器内存）
STATIC = {
    "/style.css": ("style.css", "text/css; charset=utf-8"),
    "/utils.js": ("utils.js", "application/javascript; charset=utf-8"),
    "/app.js": ("app.js", "application/javascript; charset=utf-8"),
    "/upload.js": ("upload.js", "application/javascript; charset=utf-8"),
}


# --------------------------------------------------------------------------- #
# 工具函数
# --------------------------------------------------------------------------- #
def get_lan_ip():
    """获取服务器自身的局域网 IP (通过 UDP 探测, 不真正发包)。"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


def safe_name(name):
    """清洗文件名, 仅保留安全字符, 并限制长度。"""
    name = os.path.basename(name or "file")
    name = re.sub(r'[^\w.\-\u4e00-\u9fff]+', '_', name)
    if not name:
        name = "file"
    return name[:120]


def content_disposition(name):
    ascii_name = name.encode("ascii", "ignore").decode() or "file"
    return f'attachment; filename="{ascii_name}"; filename*=UTF-8\'\'{quote(name)}'


def parse_multipart(body, content_type):
    """手动解析 multipart/form-data, 返回 (fields, files)。
    files 元素为 (field_name, filename, bytes_data)。
    (Python 3.13 已移除 cgi 模块, 这里用 email 解析 MIME。)
    """
    m = re.search(r'boundary=([^;]+)', content_type or "")
    if not m:
        return {}, []
    boundary = m.group(1).strip().strip('"').encode()
    raw = b"Content-Type: " + (content_type or "").encode() + b"\r\n\r\n" + body
    msg = BytesParser(policy=default).parsebytes(raw)
    fields, files = {}, []
    for part in msg.walk():
        if part.is_multipart():
            continue
        cd = part.get("Content-Disposition", "") or ""
        name = re.search(r'name="([^"]*)"', cd)
        fname = re.search(r'filename="([^"]*)"', cd)
        payload = part.get_payload(decode=True) or b""
        fname_val = fname.group(1) if fname else None
        name_val = name.group(1) if name else ""
        if fname_val:
            files.append((name_val, fname_val, payload))
        else:
            fields[name_val] = payload.decode("utf-8", "replace")
    return fields, files


# --------------------------------------------------------------------------- #
# 服务器状态 (中枢)
# --------------------------------------------------------------------------- #
class State:
    def __init__(self):
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        os.makedirs(LOG_DIR, exist_ok=True)
        self.lock = threading.Lock()
        self.files = self._load(FILES_DB, {})
        self.peers = self._load(PEERS_DB, {})
        self.server_ip = get_lan_ip()

    def _load(self, path, default):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default

    def _save_files(self):
        with open(FILES_DB, "w", encoding="utf-8") as f:
            json.dump(self.files, f, ensure_ascii=False, indent=2)

    def _save_peers(self):
        with open(PEERS_DB, "w", encoding="utf-8") as f:
            json.dump(self.peers, f, ensure_ascii=False, indent=2)

    # ---- 日志 ----
    def log(self, ip, action, detail=""):
        now = datetime.datetime.now()
        line = f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] IP={ip} ACTION={action} {detail}\n"
        path = os.path.join(LOG_DIR, f"uploader_{now.strftime('%Y-%m-%d')}.log")
        with open(path, "a", encoding="utf-8") as f:
            f.write(line)
        # 终端实时输出
        name = self.get_name(ip)
        tag = f" ({name})" if name else ""
        print(f"[{action}] {ip}{tag} {detail}")

    def logs(self, n=50):
        now = datetime.datetime.now()
        path = os.path.join(LOG_DIR, f"uploader_{now.strftime('%Y-%m-%d')}.log")
        if not os.path.isfile(path):
            return []
        with open(path, "r", encoding="utf-8") as f:
            return f.read().splitlines()[-n:]

    # ---- 同伴 (在线 IP) ----
    def touch_peer(self, ip):
        if ip in ("127.0.0.1", "::1"):
            return
        now = datetime.datetime.now().isoformat()
        is_new = ip not in self.peers
        entry = self.peers.get(ip)
        if isinstance(entry, str):
            self.peers[ip] = {"seen": now, "name": ""}
        elif isinstance(entry, dict):
            entry["seen"] = now
            if is_new:
                self._save_peers()
            return          # 已有 IP 仅更新时间戳, 不写盘 (省 IO)
        else:
            self.peers[ip] = {"seen": now, "name": ""}
        if is_new:
            self._save_peers()
            name = self.get_name(ip)
            tag = f" ({name})" if name else ""
            print(f"[CONNECT] {ip}{tag}")

    def peer_list(self, my_ip):
        now = datetime.datetime.now()
        out = []
        for ip, entry in self.peers.items():
            if ip == my_ip or ip in ("127.0.0.1", "::1"):
                continue
            name = ""
            if isinstance(entry, dict):
                seen_str = entry.get("seen", "")
                name = entry.get("name", "")
            else:
                seen_str = entry  # 兼容旧纯时间戳格式
            try:
                online = (now - datetime.datetime.fromisoformat(seen_str)).total_seconds() < ONLINE_WINDOW
            except Exception:
                online = False
            out.append({"ip": ip, "online": online, "name": name})
        return out

    def set_name(self, ip, name):
        """设置或清除某个 IP 的昵称 (最长20字符)。"""
        old = self.get_name(ip)
        name = (name or "").strip()[:20]
        entry = self.peers.get(ip)
        if isinstance(entry, dict):
            entry["name"] = name
        elif isinstance(entry, str):
            self.peers[ip] = {"seen": entry, "name": name}
        else:
            self.peers[ip] = {"seen": datetime.datetime.now().isoformat(), "name": name}
        self._save_peers()
        if old != name:
            print(f"[NAME] {ip} → {name or '(未设置)'}")

    def get_name(self, ip):
        """获取某个 IP 的昵称，无则返回空字符串。"""
        entry = self.peers.get(ip)
        if isinstance(entry, dict):
            return entry.get("name", "")
        return ""

    # ---- 文件元信息视图 ----
    def my_files(self, ip):
        out = []
        for f in self.files.values():
            if f["owner"] == ip:
                out.append({
                    "id": f["id"], "name": f["name"], "size": f["size"],
                    "uploaded_at": f["uploaded_at"],
                    "mode": f.get("mode", "private"),
                    "expires_at": f.get("expires_at"),
                    "deliveries": [{"to": d["to"], "name": self.get_name(d["to"])} for d in f.get("deliveries", [])],
                })
        return out

    def cleanup_expired(self):
        """删除已过期的文件（物理文件 + 元信息）。"""
        now = datetime.datetime.now()
        to_delete = []
        for fid, f in list(self.files.items()):
            exp = f.get("expires_at")
            if exp and datetime.datetime.fromisoformat(exp) < now:
                to_delete.append(fid)
        if not to_delete:
            return
        for fid in to_delete:
            try:
                if os.path.isfile(self.files[fid]["stored"]):
                    os.remove(self.files[fid]["stored"])
            except Exception:
                pass
            del self.files[fid]
        self._save_files()

    def public_files(self):
        """返回所有公共寄存文件（自动过滤已过期）。"""
        self.cleanup_expired()
        out = []
        for f in self.files.values():
            if f.get("mode") != "public":
                continue
            out.append({
                "id": f["id"], "name": f["name"], "size": f["size"],
                "owner": f["owner"], "owner_name": self.get_name(f["owner"]),
                "uploaded_at": f["uploaded_at"],
                "expires_at": f.get("expires_at"),
            })
        return out

    def inbox(self, ip):
        out = []
        for f in self.files.values():
            for d in f.get("deliveries", []):
                if d["to"] == ip:
                    owner_ip = f["owner"]
                    out.append({
                        "id": f["id"], "name": f["name"], "size": f["size"],
                        "owner": owner_ip, "at": d["at"], "downloaded": d.get("downloaded", False),
                        "owner_name": self.get_name(owner_ip),
                    })
        return out


STATE = State()


# --------------------------------------------------------------------------- #
# HTTP 处理器
# --------------------------------------------------------------------------- #
class Handler(BaseHTTPRequestHandler):
    server_version = "LAN-Uploader/1.0"
    protocol_version = "HTTP/1.1"

    # ---------------- 辅助 ----------------
    def handle_one_request(self):
        """覆写以静默客户端断连 (ConnectionResetError)，避免控制台刷屏。"""
        try:
            super().handle_one_request()
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            pass

    def _client_ip(self):
        # 反向代理不存在, 直接用 socket 对端地址
        return self.client_address[0]

    def _send_json(self, obj, code=200):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _serve_static(self, fname, ctype):
        path = os.path.join(BASE_DIR, fname)
        if not os.path.isfile(path):
            self.send_error(404)
            return
        with open(path, "rb") as f:
            data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0) or 0)
        if length <= 0:
            return b""
        if length > MAX_UPLOAD:
            return None
        return self.rfile.read(length)

    def log_message(self, fmt, *args):  # 静默默认访问日志 (操作日志由我们自定义)
        return

    # ---------------- GET ----------------
    def do_GET(self):
        try:
            parsed = urlparse(self.path)
            path = parsed.path
            ip = self._client_ip()
            STATE.touch_peer(ip)

            if path in ("/", "/index.html"):
                self._serve_static("index.html", "text/html; charset=utf-8")
                return
            if path in STATIC:
                self._serve_static(*STATIC[path])
                return
            if path == "/favicon.ico":
                self.send_response(204)
                self.end_headers()
                return
            if path == "/api/state":
                self._send_json({
                    "ip": ip,
                    "server_ip": STATE.server_ip,
                    "my_name": STATE.get_name(ip),
                    "peers": STATE.peer_list(ip),
                    "my_files": STATE.my_files(ip),
                    "inbox": STATE.inbox(ip),
                    "public_files": STATE.public_files(),
                })
                return
            if path == "/api/logs":
                qs = parse_qs(parsed.query)
                n = int(qs.get("n", [50])[0])
                self._send_json({"lines": STATE.logs(n)})
                return
            if path.startswith("/api/download/"):
                fid = path.split("/api/download/", 1)[1]
                self._download(fid, ip)
                return
            self.send_error(404)
        except Exception as e:
            traceback.print_exc()
            try:
                self._send_json({"ok": False, "error": str(e)}, 500)
            except Exception:
                pass

    # ---------------- POST ----------------
    def do_POST(self):
        try:
            parsed = urlparse(self.path)
            path = parsed.path
            ip = self._client_ip()
            STATE.touch_peer(ip)

            if path == "/api/upload":
                self._upload(ip)
                return
            if path == "/api/send":
                self._send(ip)
                return
            if path == "/api/delete":
                self._delete(ip)
                return
            if path == "/api/set-name":
                self._set_name(ip)
                return
            self.send_error(404)
        except Exception as e:
            traceback.print_exc()
            try:
                self._send_json({"ok": False, "error": str(e)}, 500)
            except Exception:
                pass

    # ---------------- 业务逻辑 ----------------
    def _upload(self, ip):
        body = self._read_body()
        if body is None:
            self._send_json({"ok": False, "error": "文件过大，超出服务器限制"}, 413)
            return
        ctype = self.headers.get("Content-Type", "")
        fields, files = parse_multipart(body, ctype)
        if not files:
            self._send_json({"ok": False, "error": "未收到文件"}, 400)
            return
        # 读取上传选项
        mode = fields.get("mode", "private")
        if mode not in ("private", "public"):
            mode = "private"
        expire_minutes = int(fields.get("expire_minutes", "0") or "0")
        expire_after_download = fields.get("expire_after_download", "") == "1"
        saved = []
        now = datetime.datetime.now()
        STATE.cleanup_expired()  # 顺便清理已过期文件
        with STATE.lock:
            for _, filename, data in files:
                sid = now.strftime("%Y%m%d%H%M%S") + "_" + os.urandom(4).hex()
                stored = os.path.join(UPLOAD_DIR, sid + "_" + safe_name(filename))
                with open(stored, "wb") as f:
                    f.write(data)
                expires_at = None
                if mode == "public" and expire_minutes > 0:
                    expires_at = (now + datetime.timedelta(minutes=expire_minutes)).isoformat()
                STATE.files[sid] = {
                    "id": sid, "stored": stored, "name": filename,
                    "owner": ip, "size": len(data),
                    "uploaded_at": now.isoformat(),
                    "mode": mode,
                    "expires_at": expires_at,
                    "expire_after_download": (expire_after_download and mode == "private"),
                    "deliveries": [],
                }
                saved.append(filename)
            STATE._save_files()
        STATE.log(ip, "UPLOAD", "files=" + ",".join(saved))
        self._send_json({"ok": True, "files": saved})

    def _send(self, ip):
        body = self._read_body()
        try:
            payload = json.loads(body.decode("utf-8"))
            fids = payload.get("file_ids", [])
            to_ip = payload.get("to_ip", "")
        except Exception:
            self._send_json({"ok": False, "error": "参数错误"}, 400)
            return
        if not to_ip or not fids:
            self._send_json({"ok": False, "error": "缺少目标IP或文件"}, 400)
            return
        if to_ip == ip:
            self._send_json({"ok": False, "error": "不能发送给自己"}, 400)
            return
        now = datetime.datetime.now()
        names = []
        with STATE.lock:
            for fid in fids:
                f = STATE.files.get(fid)
                if not f or f["owner"] != ip:
                    continue
                # 避免重复投递给同一 IP
                if any(d["to"] == to_ip for d in f.get("deliveries", [])):
                    continue
                f.setdefault("deliveries", []).append({
                    "to": to_ip, "at": now.isoformat(), "downloaded": False,
                })
                names.append(f["name"])
            STATE._save_files()
        STATE.log(ip, "SEND", "to=" + to_ip + " files=" + ",".join(names))
        self._send_json({"ok": True, "sent": names})

    def _delete(self, ip):
        body = self._read_body()
        try:
            payload = json.loads(body.decode("utf-8"))
            ids = payload.get("ids", [])
        except Exception:
            self._send_json({"ok": False, "error": "参数错误"}, 400)
            return
        removed = []
        with STATE.lock:
            for fid in ids:
                f = STATE.files.get(fid)
                if not f or f["owner"] != ip:
                    continue
                try:
                    if os.path.isfile(f["stored"]):
                        os.remove(f["stored"])
                except Exception:
                    pass
                removed.append(f["name"])
                del STATE.files[fid]
            STATE._save_files()
        STATE.log(ip, "DELETE", "files=" + ",".join(removed))
        self._send_json({"ok": True, "removed": removed})

    def _set_name(self, ip):
        body = self._read_body()
        try:
            payload = json.loads(body.decode("utf-8"))
            name = payload.get("name", "")
        except Exception:
            self._send_json({"ok": False, "error": "参数错误"}, 400)
            return
        STATE.set_name(ip, name)
        STATE.log(ip, "SETNAME", "name=" + (name or "(cleared)"))
        self._send_json({"ok": True, "name": name})

    def _download(self, fid, ip):
        with STATE.lock:
            f = STATE.files.get(fid)
            if not f:
                self.send_error(404)
                return
            is_owner = f["owner"] == ip
            hit = None
            for d in f.get("deliveries", []):
                if d["to"] == ip:
                    hit = d
                    break
            if not (is_owner or hit):
                self.send_error(403)
                return
            stored = f["stored"]
            name = f["name"]
            if hit and not hit.get("downloaded"):
                hit["downloaded"] = True
                STATE._save_files()
        if not os.path.isfile(stored):
            self.send_error(404)
            return
        mime, _ = mimetypes.guess_type(name)
        mime = mime or "application/octet-stream"
        size = os.path.getsize(stored)
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(size))
        self.send_header("Content-Disposition", content_disposition(name))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        with open(stored, "rb") as fh:
            while True:
                chunk = fh.read(64 * 1024)
                if not chunk:
                    break
                self.wfile.write(chunk)
        STATE.log(ip, "DOWNLOAD", "file=" + name + (" (owner)" if is_owner else " (from " + f["owner"] + ")"))

        # 如果开启了"对方下载后自动删除"，接收者下载完就清理
        if f.get("expire_after_download") and hit:
            try:
                if os.path.isfile(stored):
                    os.remove(stored)
            except Exception:
                pass
            STATE.files.pop(fid, None)
            STATE._save_files()
            STATE.log(ip, "AUTODEL", "file=" + name + " (downloaded by recipient)")


# --------------------------------------------------------------------------- #
# 启动
# --------------------------------------------------------------------------- #
def main():
    parser = argparse.ArgumentParser(description="局域网文件共享服务器")
    parser.add_argument("--host", default="0.0.0.0", help="监听地址 (默认 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="监听端口 (默认 8000)")
    args = parser.parse_args()

    httpd = ThreadingHTTPServer((args.host, args.port), Handler)
    lan = STATE.server_ip
    start_time = datetime.datetime.now()

    def _on_exit():
        """无论 Ctrl+C / 点 X 关闭窗口 / 正常退出, 都会保存运行摘要。"""
        end_time = datetime.datetime.now()
        runtime = end_time - start_time
        stop_log = os.path.join(LOG_DIR, f"server_{start_time.strftime('%Y%m%d_%H%M%S')}.log")
        try:
            with open(stop_log, "w", encoding="utf-8") as f:
                f.write(f"启动时间: {start_time.isoformat()}\n")
                f.write(f"停止时间: {end_time.isoformat()}\n")
                f.write(f"运行时长: {runtime}\n")
                f.write(f"本机 IP : {lan}\n")
                f.write(f"监听地址: {args.host}:{args.port}\n")
                f.write(f"连接过 IP: {list(STATE.peers.keys())}\n")
            print(f"运行摘要已保存: {stop_log}")
        except Exception:
            pass

    atexit.register(_on_exit)
    print("=" * 56)
    print("  局域网文件共享服务器已启动")
    print("  本机局域网 IP :", lan)
    print("  访问地址      : http://%s:%d" % (lan, args.port))
    print("  同一 WiFi 下的其他设备用上述地址打开即可。")
    print("  文件保存在    :", UPLOAD_DIR)
    print("  日志保存在    :", LOG_DIR)
    print("  按 Ctrl+C 停止")
    print("=" * 56)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n服务器已停止。")
        httpd.shutdown()


if __name__ == "__main__":
    main()
