<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
  <img src="https://img.shields.io/badge/Zero_Dependencies-%E2%9C%93-success" alt="Zero Dependencies">
</p>

<h1 align="center">Simple LAN File Sharing</h1>

<p align="center">
  <b><a href="#english">English</a></b> &nbsp;|&nbsp;
  <b><a href="#中文">中文</a></b>
</p>

<p align="center">
  A zero-config file sharing hub for your local network — one Python server, any browser on the same WiFi.
  <br>
  零配置局域网文件共享中枢 —— 一台跑 Python，同 WiFi 下任意浏览器互传。
</p>

---

<h2 id="english">English</h2>

### ✨ Features

- Shows your own LAN IP and all online peer IPs
- Batch upload — drag & drop or select multiple files (up to 200 MB per batch)
- Send to a specific peer by IP
- Inbox — receive files and download with one click
- Access control — only the sender and the intended recipient can download (403 otherwise)
- Operation log — every upload / send / download / delete is written to `logs/uploader_YYYY-MM-DD.log`
- Responsive UI — HTML / CSS / JS separated, works on desktop and mobile
- Zero dependencies — Python stdlib only, no internet required

### 🚀 Quick Start

#### 1. Start the server

```bash
cd Simple-LAN-File-Sharing
python server.py
```

Optional flags:

```bash
python server.py --port 9000        # custom port
python server.py --host 0.0.0.0     # bind address (default: 0.0.0.0)
```

Console output:

```
========================================================
  局域网文件共享服务器已启动
  本机局域网 IP : 192.168.1.100
  访问地址      : http://192.168.1.100:8000
========================================================
```

#### 2. Open in browser

> ⚠️ Use the **LAN IP** from the console, NOT `localhost`.

- **Server machine**: `http://192.168.1.100:8000`
- **Any other device** (phone, tablet, another PC): same URL — as long as it's on the same WiFi

#### 3. Usage

1. Upload files via the upload area (drag & drop works)
2. Your files appear in "My Files"
3. Check a file, pick a peer IP, click "Send"
4. The peer sees it in their "Inbox" and downloads it

### 📁 Project Structure

```
Simple-LAN-File-Sharing/
├── server.py          # Python HTTP server (the hub)
├── index.html         # Page structure
├── style.css          # Responsive styles
├── app.js             # Frontend logic
├── .gitignore
├── README.md
├── uploads/           # Uploaded files (gitignored)
└── logs/              # Operation logs (gitignored)
```

### 🔧 How It Works

All devices connect to the **same machine** running `server.py`. The server identifies each visitor by `client_address` (LAN IP), tracks files and deliveries in memory + JSON, and only allows authorized recipients to download.

No internet required — only local WiFi.

### 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.8+ (`http.server`, `email`, `json`, `threading`) |
| Frontend | Vanilla HTML / CSS / JS (no framework) |
| Transport | HTTP multipart upload + JSON API |

### 📄 License

MIT

---

<h2 id="中文">中文</h2>

### ✨ 功能

- 显示本机局域网 IP 及所有在线同伴 IP
- 批量上传，支持拖拽，单批上限 200MB
- 指定目标 IP 发送文件
- 收件箱，接收并一键下载他人发来的文件
- 权限控制，仅发送者与指定接收者可下载（否则 403）
- 操作日志，每次上传/发送/下载/删除写入 `logs/uploader_YYYY-MM-DD.log`
- 响应式界面，HTML/CSS/JS 分离，适配电脑与手机
- 零依赖，纯 Python 标准库，无需联网

### 🚀 快速开始

#### 1. 启动服务器

```bash
cd Simple-LAN-File-Sharing
python server.py
```

可选参数：

```bash
python server.py --port 9000        # 自定义端口
python server.py --host 0.0.0.0     # 绑定地址（默认 0.0.0.0）
```

控制台输出：

```
========================================================
  局域网文件共享服务器已启动
  本机局域网 IP : 192.168.1.100
  访问地址      : http://192.168.1.100:8000
========================================================
```

#### 2. 浏览器打开

> ⚠️ 请用控制台打印的**局域网 IP**，不要用 `localhost`。

- **服务器本机**：`http://192.168.1.100:8000`
- **其他设备**（手机、平板、另一台电脑）：同一网址，只要在同一个 WiFi 下即可

#### 3. 使用步骤

1. 在上传区上传文件（支持拖拽）
2. 上传后的文件出现在"我的文件"中
3. 勾选文件，选择目标 IP，点击发送
4. 对方在"收件箱"中看到并下载文件

### 📁 项目结构

```
Simple-LAN-File-Sharing/
├── server.py          # Python 服务器（中枢）
├── index.html         # 页面结构
├── style.css          # 响应式样式
├── app.js             # 前端逻辑
├── .gitignore
├── README.md
├── uploads/           # 用户上传文件（gitignored）
└── logs/              # 操作日志（gitignored）
```

### 🔧 工作原理

所有设备连接到运行 `server.py` 的**同一台机器**。服务器通过 `client_address` 识别每个访问者的局域网 IP，在内存与 JSON 中管理文件及投递记录，仅允许授权的发送者与接收者下载。

不需要互联网，仅需局域网 WiFi。

### 🛠 技术栈

| 层级 | 技术 |
|---|---|
| 后端 | Python 3.8+（`http.server`、`email`、`json`、`threading`） |
| 前端 | 原生 HTML / CSS / JS（无框架） |
| 传输 | HTTP multipart 上传 + JSON API |

### 📄 许可证

MIT
