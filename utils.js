/* utils.js — 工具函数，无外部依赖 */
"use strict";

var $ = function(id) { return document.getElementById(id); };

function toast(msg, ok) {
  if (ok === void 0) ok = true;
  var t = $("toast");
  t.textContent = msg;
  t.className = "toast show " + (ok ? "ok" : "err");
  clearTimeout(toast._t);
  toast._t = setTimeout(function() { t.className = "toast"; }, 2600);
}

function fmtSize(n) {
  if (n < 1024) return n + " B";
  if (n < 1048576) return (n / 1024).toFixed(1) + " KB";
  return (n / 1048576).toFixed(1) + " MB";
}

function escapeHtml(s) {
  return (s || "").replace(/[&<>"]/g, function(c) {
    return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
  });
}

function guessDeviceName() {
  var ua = navigator.userAgent || "";
  if (/iPhone|iPad|iPod/.test(ua)) {
    var m = ua.match(/OS (\d+)/);
    return m ? "iPhone (iOS " + m[1] + ")" : "iPhone";
  }
  if (/Android/.test(ua)) {
    var m = ua.match(/Android (\d+(\.\d+)?)/);
    return m ? "Android " + m[1] : "Android 设备";
  }
  if (/Windows/.test(ua)) return "Windows PC";
  if (/Mac OS/.test(ua)) return "Mac";
  if (/Linux/.test(ua)) return "Linux";
  return "";
}

async function api(path, opts) {
  var r = await fetch(path, opts);
  if (!r.ok) throw new Error("HTTP " + r.status);
  var ct = r.headers.get("content-type") || "";
  return ct.includes("application/json") ? r.json() : r;
}
