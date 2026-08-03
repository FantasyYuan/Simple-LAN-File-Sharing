/* app.js — 核心逻辑：状态管理、渲染、交互 */
"use strict";

var MY_IP = "";
var SERVER_IP = "";

// ---------------- 状态 ----------------
async function loadState() {
  try {
    var s = await api("/api/state");
    MY_IP = s.ip;
    SERVER_IP = s.server_ip;
    $("myIp").textContent = s.ip;
    $("serverIp").textContent = s.server_ip;

    var editing = (document.activeElement === $("nameInput"));
    if (!editing) {
      $("nameInput").value = s.my_name || "";
    }

    if (!editing && !s.my_name && !localStorage.getItem("uploader_name_set")) {
      var guessed = guessDeviceName();
      if (guessed) {
        $("nameInput").value = guessed;
        localStorage.setItem("uploader_name_set", "1");
        fetch("/api/set-name", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name: guessed }),
        }).catch(function(){});
      }
    }

    var sel = $("peerSelect");
    var cur = sel.value;
    sel.innerHTML = '<option value="">— 选择对方 IP —</option>';
    (s.peers || []).forEach(function(p) {
      var o = document.createElement("option");
      o.value = p.ip;
      o.textContent = (p.name ? p.name + " · " : "") + p.ip + (p.online ? "（在线）" : "（离线）");
      sel.appendChild(o);
    });
    if (cur) sel.value = cur;

    renderMyFiles(s.my_files || []);
    renderInbox(s.inbox || []);
    renderPublicFiles(s.public_files || []);
  } catch (e) {
    console.warn("loadState failed:", e.message);
  }
}

function renderMyFiles(files) {
  var box = $("myFiles");
  var checkedIds = Array.from(document.querySelectorAll(".pick:checked")).map(function(c) { return c.value; });
  if (!files.length) {
    box.innerHTML = '<p class="empty">还没有文件，先在 ① 上传</p>';
    return;
  }
  box.innerHTML = "";
  files.forEach(function(f) {
    var delivered = (f.deliveries || []).map(function(d) { return d.name || d.to; }).join("、");
    var pubTag = f.mode === "public" ? '<span class="tag pub">公共</span>' : "";
    var div = document.createElement("div");
    div.className = "item";
    div.innerHTML =
      '<label class="row">' +
      '<input type="checkbox" class="pick" value="' + f.id + '">' +
      '<span class="fname" title="' + escapeHtml(f.name) + '">' + escapeHtml(f.name) + "</span>" +
      '<span class="meta">' + fmtSize(f.size) + "</span>" +
      pubTag +
      (delivered ? '<span class="tag">已发→' + escapeHtml(delivered) + "</span>" : "") +
      '<button class="btn tiny del" data-id="' + f.id + '" type="button">删除</button>' +
      "</label>";
    box.appendChild(div);
  });
  box.querySelectorAll(".pick").forEach(function(cb) {
    if (checkedIds.indexOf(cb.value) !== -1) cb.checked = true;
  });
  box.querySelectorAll(".del").forEach(function(b) {
    b.onclick = function() { delFile(b.dataset.id); };
  });
}

function renderInbox(items) {
  var box = $("inbox");
  if (!items.length) { box.innerHTML = '<p class="empty">暂无接收的文件</p>'; return; }
  box.innerHTML = "";
  items.forEach(function(f) {
    var div = document.createElement("div");
    div.className = "item";
    var fromLabel = f.owner_name ? f.owner_name + " (" + f.owner + ")" : f.owner;
    var dlBtn = f.downloaded
      ? '<a class="btn tiny done" href="/api/download/' + f.id + '" download>已下载</a>'
      : '<a class="btn tiny primary" href="/api/download/' + f.id + '" download>下载</a>';
    div.innerHTML =
      '<div class="row">' +
      '<span class="fname" title="' + escapeHtml(f.name) + '">' + escapeHtml(f.name) + "</span>" +
      '<span class="meta">' + fmtSize(f.size) + "</span>" +
      '<span class="tag">来自 ' + escapeHtml(fromLabel) + "</span>" +
      dlBtn + "</div>";
    box.appendChild(div);
  });
}

function renderPublicFiles(files) {
  var box = $("publicFiles");
  if (!files.length) { box.innerHTML = '<p class="empty">暂无公共文件</p>'; return; }
  box.innerHTML = "";
  files.forEach(function(f) {
    var div = document.createElement("div");
    div.className = "item";
    var ownerLabel = f.owner_name ? f.owner_name + " (" + f.owner + ")" : f.owner;
    var expireText = f.expires_at ? " · 过期: " + new Date(f.expires_at).toLocaleString() : " · 永久";
    div.innerHTML =
      '<div class="row">' +
      '<span class="fname" title="' + escapeHtml(f.name) + '">' + escapeHtml(f.name) + "</span>" +
      '<span class="meta">' + fmtSize(f.size) + "</span>" +
      '<span class="tag">来自 ' + escapeHtml(ownerLabel) + expireText + "</span>" +
      '<a class="btn tiny primary" href="/api/download/' + f.id + '" download>下载</a>' +
      "</div>";
    box.appendChild(div);
  });
}

// ---------------- 发送 ----------------
$("sendBtn").onclick = async function() {
  var ids = Array.from(document.querySelectorAll(".pick:checked")).map(function(c) { return c.value; });
  var to = $("peerSelect").value;
  if (!ids.length) return toast("请先勾选要发送的文件", false);
  if (!to) return toast("请选择接收方 IP", false);
  try {
    var r = await fetch("/api/send", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ file_ids: ids, to_ip: to }),
    });
    var j = await r.json();
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
    var r = await fetch("/api/delete", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ids: [id] }),
    });
    var j = await r.json();
    if (j.ok) { toast("已删除"); await loadState(); await loadLogs(); }
    else { toast("删除失败", false); }
  } catch (e) { toast("删除失败：" + e.message, false); }
}

// ---------------- 昵称 ----------------
async function saveName() {
  var name = $("nameInput").value.trim();
  try {
    var r = await fetch("/api/set-name", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: name }),
    });
    var j = await r.json();
    if (j.ok) {
      localStorage.setItem("uploader_name_set", "1");
      toast(name ? "昵称已更新：" + name : "昵称已清除");
      await loadLogs();
    } else { toast("保存失败：" + (j.error || ""), false); }
  } catch (e) { toast("保存错误：" + e.message, false); }
}
$("saveNameBtn").onclick = function() { saveName(); };
$("nameInput").addEventListener("keydown", function(e) {
  if (e.key === "Enter") { e.preventDefault(); saveName(); }
});

// ---------------- 日志 ----------------
async function loadLogs() {
  try {
    var j = await api("/api/logs?n=40");
    $("logBox").textContent = (j.lines || []).join("\n") || "（暂无日志）";
    $("logBox").scrollTop = $("logBox").scrollHeight;
  } catch (e) { /* ignore */ }
}

// ---------------- 初始化 ----------------
document.querySelectorAll('input[name="uploadMode"]').forEach(function(r) {
  r.onchange = function() {
    $("expireOpts").style.display = (r.value === "public") ? "" : "none";
    $("autoDelOpts").style.display = (r.value === "private") ? "" : "none";
  };
});

loadState();
loadLogs();
setInterval(loadState, 3000);
setInterval(loadLogs, 5000);
