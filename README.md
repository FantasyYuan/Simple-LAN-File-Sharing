<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
  <img src="https://img.shields.io/badge/Zero_Dependencies-%E2%9C%93-success" alt="Zero Dependencies">
</p>

<h1 align="center">Simple LAN File Sharing<br><small>局域网简易文件共享</small></h1>

<p align="center">
  <b>EN</b> — A lightweight, zero-config file sharing hub for your local network.
  One machine runs the Python server; everyone else opens a web browser to upload, send, and receive files over WiFi.
  <br>
  <b>中文</b> — 一个轻量的零配置局域网文件共享中枢。一台机器运行 Python 服务器，其他人用浏览器打开即可互传文件。
</p>

---

## ✨ Features · 功能

| EN | 中文 |
|---|---|
| Shows your LAN IP and online peers | 显示本机 IP 及在线同伴 IP |
| Batch upload (drag & drop, up to 200 MB) | 批量上传（支持拖拽，单批上限 200MB） |
| Send files to a specific peer by IP | 指定目标 IP 发送文件 |
| Inbox — receive and download files | 收件箱接收并下载他人发来的文件 |
| Access control — only sender & recipient can download | 权限控制 — 仅发送者和指定接收者可下载 |
| Operation log (`logs/uploader_YYYY-MM-DD.log`) | 操作日志记录每次上传/发送/下载/删除 |
| Responsive UI, works on desktop & mobile | 响应式界面，适配电脑与手机 |
| No framework, no internet required, no third-party deps | 纯 Python 标准库，无框架、无需联网 |

---

## 🚀 Quick Start · 快速开始

### 1. Start the server · 启动服务器

```bash
cd Simple-LAN-File-Sharing
python server.py
```

Optional flags · 可选参数：

```bash
python server.py --port 9000        # 自定义端口 / custom port
python server.py --host 0.0.0.0     # 绑定地址 / bind address
```

Console output · 控制台输出：

```
========================================================
  局域网文件共享服务器已启动
  本机局域网 IP : 192.168.1.100
  访问地址      : http://192.168.1.100:8000
========================================================
```

### 2. Open in browser · 浏览器打开

> ⚠️ Use the **LAN IP** (from the console), NOT `localhost`.
> 请用控制台打印的**局域网 IP**，不要用 `localhost`。

| Device · 设备 | URL · 地址 |
|---|---|
| Server machine · 服务器本机 | `http://192.168.1.100:8000` |
| Phone / tablet / another PC · 手机/平板/其他电脑 | Same URL · 同上（同一 WiFi 下） |

### 3. How to use · 使用步骤

1. **Upload** — drag & drop files, or click to select multiple · **上传** — 拖拽或点击批量选择文件
2. **My Files** — uploaded files appear here · **我的文件** — 上传后的文件在此展示
3. **Send** — check a file, pick a peer IP, click Send · **发送** — 勾选文件，选目标 IP，点发送
4. **Inbox** — the peer sees and downloads the file · **收件箱** — 对方在收件箱中下载

---

## 📁 Project Structure · 项目结构

```
Simple-LAN-File-Sharing/
├── server.py          # Python HTTP server · 服务器中枢
├── index.html         # Page structure · 页面结构
├── style.css          # Responsive styles · 响应式样式
├── app.js             # Frontend logic · 前端逻辑
├── .gitignore
├── README.md
├── uploads/           # Uploaded files · 用户上传文件 (gitignored)
└── logs/              # Operation logs · 操作日志 (gitignored)
```

---

## 🔧 How It Works · 工作原理

All devices connect to the **same machine** running `server.py`.
The server identifies each visitor by their `client_address` (LAN IP), tracks uploaded files and deliveries in memory + JSON, and only allows authorized recipients to download.

所有设备连接到运行 `server.py` 的**同一台机器**。服务器通过 `client_address` 识别每个访问者的局域网 IP，在内存和 JSON 中管理上传文件及投递记录，仅允许授权的发送者与接收者下载。

> No internet connection required — only the local WiFi.
> 不需要互联网，仅需局域网 WiFi。

---

## 🛠 Tech Stack · 技术栈

| Layer · 层 | Technology · 技术 |
|---|---|
| Backend · 后端 | Python 3.8+ (`http.server`, `email`, `json`, `threading`) |
| Frontend · 前端 | Vanilla HTML / CSS / JS (no framework · 无框架) |
| Transport · 传输 | HTTP multipart upload + JSON API |

---

## 📄 License · 许可证

MIT
