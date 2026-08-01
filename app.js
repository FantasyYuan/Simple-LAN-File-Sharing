/* 局域网文件共享 - 前端逻辑 */
(function () {
  "use strict";

  const $ = (id) => document.getElementById(id);
  let MY_IP = "";
  let SERVER_IP = "";

  // ---------------- 工具 ----------------
  function toast(msg, ok = true) {
    const t = $("toast");
    t.textContent = msg;
    t.className = "toast show " + (ok ? "ok" : "err");
    clearTimeout(toast._t);
    toast._t = setTimeout(() => (t.className = "toast"), 2600);
  }

  function fmtSize(n) {
    if (n < 1024) return n + " B";
    if (n < 1048576) return (n / 1024).toFixed(1) + " KB";
    return (n / 1048576).toFixed(1) + " MB";
  }

  function escapeHtml(s) {
    return (s || "").replace(/[&<>"]/g, (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])
    );
  }

  async function api(path, opts) {
    const r = await fetch(path, opts);
    if (!r.ok) throw new Error("HTTP " + r.status);
    const ct = r.headers.get("content-type") || "";
    return ct.includes("application/json") ? r.json() : r;
  }

  // ---------------- 状态 ----------------
  async function loadState() {
    try {
      const s = await api("/api/state");
      MY_IP = s.ip;
      SERVER_IP = s.server_ip;
      $("myIp").textContent = s.ip;
      $("serverIp").textContent = s.server_ip;

      const sel = $("peerSelect");
      const cur = sel.value;
      sel.innerHTML = '<option value="">— 选择对方 IP —</option>';
      (s.peers || []).forEach((p) => {
        const o = document.createElement("option");
        o.value = p.ip;
        o.textContent = p.ip + (p.online ? "（在线）" : "（离线）");
        sel.appendChild(o);
      });
      if (cur) sel.value = cur;

      renderMyFiles(s.my_files || []);
      renderInbox(s.inbox || []);
    } catch (e) {
      // 轮询失败不频繁打扰用户
      console.warn("loadState failed:", e.message);
    }
  }

  function renderMyFiles(files) {
    const box = $("myFiles");
    if (!files.length) {
      box.innerHTML = '<p class="empty">还没有文件，先在 ① 上传</p>';
      return;
    }
    box.innerHTML = "";
    files.forEach((f) => {
      const delivered = (f.deliveries || []).join("、");
      const div = document.createElement("div");
      div.className = "item";
      div.innerHTML =
        '<label class="row">' +
        '<input type="checkbox" class="pick" value="' + f.id + '">' +
        '<span class="fname" title="' + escapeHtml(f.name) + '">' + escapeHtml(f.name) + "</span>" +
        '<span class="meta">' + fmtSize(f.size) + "</span>" +
        (delivered ? '<span class="tag">已发→' + escapeHtml(delivered) + "</span>" : "") +
        '<button class="btn tiny del" data-id="' + f.id + '" type="button">删除</button>' +
        "</label>";
      box.appendChild(div);
    });
    box.querySelectorAll(".del").forEach((b) => {
      b.onclick = () => delFile(b.dataset.id);
    });
  }

  function renderInbox(items) {
    const box = $("inbox");
    if (!items.length) {
      box.innerHTML = '<p class="empty">暂无接收的文件</p>';
      return;
    }
    box.innerHTML = "";
    items.forEach((f) => {
      const div = document.createElement("div");
      div.className = "item";
      div.innerHTML =
        '<div class="row">' +
        '<span class="fname" title="' + escapeHtml(f.name) + '">' + escapeHtml(f.name) + "</span>" +
        '<span class="meta">' + fmtSize(f.size) + "</span>" +
        '<span class="tag">来自 ' + escapeHtml(f.owner) + "</span>" +
        '<a class="btn tiny primary" href="/api/download/' + f.id + '" download>下载</a>' +
        "</div>";
      box.appendChild(div);
    });
  }

  // ---------------- 上传 ----------------
  $("pickBtn").onclick = () => $("fileInput").click();
  $("fileInput").onchange = async () => {
    await doUpload($("fileInput").files);
    $("fileInput").value = "";
  };

  const dz = $("dropzone");
  ["dragover", "dragenter"].forEach((ev) =>
    dz.addEventListener(ev, (e) => {
      e.preventDefault();
      dz.classList.add("over");
    })
  );
  ["dragleave", "drop"].forEach((ev) =>
    dz.addEventListener(ev, (e) => {
      e.preventDefault();
      dz.classList.remove("over");
    })
  );
  dz.addEventListener("drop", async (e) => {
    if (e.dataTransfer && e.dataTransfer.files) await doUpload(e.dataTransfer.files);
  });

  async function doUpload(fileList) {
    const files = Array.from(fileList || []);
    if (!files.length) return;
    const fd = new FormData();
    files.forEach((f) => fd.append("file", f, f.name));
    $("uploadHint").textContent = "上传中…";
    try {
      const r = await fetch("/api/upload", { method: "POST", body: fd });
      const j = await r.json();
      if (j.ok) {
        toast("上传成功：" + j.files.length + " 个文件");
        $("uploadHint").textContent = "已上传 " + j.files.length + " 个文件";
        await loadState();
        await loadLogs();
      } else {
        toast("上传失败：" + (j.error || ""), false);
        $("uploadHint").textContent = "";
      }
    } catch (e) {
      toast("上传错误：" + e.message, false);
      $("uploadHint").textContent = "";
    }
  }

  // ---------------- 发送 ----------------
  $("sendBtn").onclick = async () => {
    const ids = Array.from(document.querySelectorAll(".pick:checked")).map((c) => c.value);
    const to = $("peerSelect").value;
    if (!ids.length) return toast("请先勾选要发送的文件", false);
    if (!to) return toast("请选择接收方 IP", false);
    try {
      const r = await fetch("/api/send", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ file_ids: ids, to_ip: to }),
      });
      const j = await r.json();
      if (j.ok) {
        toast("已发送给 " + to);
        await loadState();
        await loadLogs();
      } else {
        toast("发送失败：" + (j.error || ""), false);
      }
    } catch (e) {
      toast("发送错误：" + e.message, false);
    }
  };

  // ---------------- 删除 ----------------
  async function delFile(id) {
    try {
      const r = await fetch("/api/delete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ids: [id] }),
      });
      const j = await r.json();
      if (j.ok) {
        toast("已删除");
        await loadState();
        await loadLogs();
      } else {
        toast("删除失败", false);
      }
    } catch (e) {
      toast("删除失败：" + e.message, false);
    }
  }

  // ---------------- 日志 ----------------
  async function loadLogs() {
    try {
      const j = await api("/api/logs?n=40");
      $("logBox").textContent = (j.lines || []).join("\n") || "（暂无日志）";
      $("logBox").scrollTop = $("logBox").scrollHeight;
    } catch (e) {
      /* 忽略 */
    }
  }

  // ---------------- 初始化 ----------------
  loadState();
  loadLogs();
  setInterval(loadState, 3000); // 轮询状态 / 收件箱
  setInterval(loadLogs, 5000); // 轮询日志
})();
