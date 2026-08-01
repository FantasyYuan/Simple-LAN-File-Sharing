# Simple LAN File Sharing

A lightweight, zero-config file sharing hub for your local network.  
One machine runs the Python server — everyone else opens a web browser to upload, send, and receive files over WiFi.

一个轻量的局域网文件共享中枢，同一 WiFi 下的设备打开网页即可互传文件。

---

## Features / 功能

- **See who's online** — displays your own LAN IP and all peer IPs that have connected recently
- **Batch upload** — drag & drop or select multiple files at once (up to 200 MB per batch)
- **Send to a specific IP** — pick files from your library, choose a target peer, and push them
- **Inbox** — receive files from others and download with one click
- **Access control** — only the sender and the intended recipient can download a file (403 otherwise)
- **Operation log** — every upload / send / download / delete is written to `logs/uploader_YYYY-MM-DD.log`
- **Responsive UI** — HTML / CSS / JS separated, works on desktop and mobile

---

## Quick Start / 快速开始

### 1. Start the server / 启动服务器

```bash
cd Simple-LAN-File-Sharing
python server.py
```

Optional flags:

```bash
python server.py --port 9000        # custom port
python server.py --host 0.0.0.0     # bind address (default: 0.0.0.0)
```

The console will print your LAN IP and the access URL:

```
========================================================
  局域网文件共享服务器已启动
  本机局域网 IP : 192.168.1.100
  访问地址      : http://192.168.1.100:8000
========================================================
```

### 2. Open in browser / 浏览器打开

- **On the server machine**: `http://192.168.1.100:8000` (use the LAN IP, NOT `localhost`)
- **On any other device** (phone, tablet, another PC): same URL — as long as it's on the same WiFi

### 3. Use it / 开始用

1. Upload files via the upload area (drag & drop works)
2. Your files appear in "My Files"
3. Check a file, pick a peer IP, click "Send"
4. The peer sees it in their "Inbox" and downloads it

---

## Project structure / 项目结构

```
Simple-LAN-File-Sharing/
├── server.py         # Python HTTP server (the hub)
├── index.html        # Page structure
├── style.css         # Responsive styles (mobile + desktop)
├── app.js            # Frontend logic (fetch API)
├── uploads/          # Uploaded files (gitignored)
├── logs/             # Operation logs (gitignored)
└── README.md
```

## How it works / 原理

All devices connect to the **same machine** running `server.py`.  
The server identifies each visitor by their `client_address` (LAN IP), tracks uploaded files and deliveries in memory + JSON, and relays downloads to authorized recipients only.

No internet connection required — only the local WiFi.

## Tech stack

- **Backend**: Python 3 (stdlib only — `http.server`, `email`, `json`, `threading`)
- **Frontend**: Vanilla HTML / CSS / JS, no framework
- **Transport**: HTTP multipart upload, JSON API

## License

MIT
