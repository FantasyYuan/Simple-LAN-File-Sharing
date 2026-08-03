/* upload.js — 文件上传、拖拽、进度条 */
"use strict";

// ---------------- 事件绑定 ----------------
$("pickBtn").onclick = function() { $("fileInput").click(); };
$("fileInput").onchange = async function() {
  await doUpload($("fileInput").files);
  $("fileInput").value = "";
};

var dz = $("dropzone");
["dragover", "dragenter"].forEach(function(ev) {
  dz.addEventListener(ev, function(e) { e.preventDefault(); dz.classList.add("over"); });
});
["dragleave", "drop"].forEach(function(ev) {
  dz.addEventListener(ev, function(e) { e.preventDefault(); dz.classList.remove("over"); });
});
dz.addEventListener("drop", async function(e) {
  if (e.dataTransfer && e.dataTransfer.files) await doUpload(e.dataTransfer.files);
});

// ---------------- 上传核心 ----------------
async function doUpload(fileList) {
  var files = Array.from(fileList || []);
  if (!files.length) return;

  var fd = new FormData();
  files.forEach(function(f) { fd.append("file", f, f.name); });
  var mode = document.querySelector('input[name="uploadMode"]:checked').value;
  fd.append("mode", mode);
  if (mode === "public") {
    fd.append("expire_minutes", $("expireSelect").value);
  } else {
    fd.append("expire_after_download", $("autoDelCheck").checked ? "1" : "0");
  }

  var uid = "up_" + Date.now() + "_" + Math.random().toString(36).slice(2, 6);
  var totalBytes = files.reduce(function(s, f) { return s + f.size; }, 0);

  var item = document.createElement("div");
  item.className = "progress-item";
  item.id = uid;
  item.innerHTML =
    '<div class="progress-head">' +
      "<span>上传 " + files.length + " 个文件 (" + fmtSize(totalBytes) + ")</span>" +
      '<span class="pct">0%</span>' +
    "</div>" +
    '<div class="progress-track"><div class="progress-fill" style="width:0%"></div></div>' +
    '<div class="progress-speed"></div>';
  $("progressArea").appendChild(item);

  return new Promise(function(resolve) {
    var xhr = new XMLHttpRequest();
    var startTime = Date.now();

    xhr.upload.onprogress = function(e) {
      if (!e.lengthComputable) return;
      var it = document.getElementById(uid);
      if (!it) return;
      var pct = Math.round(e.loaded / e.total * 100);
      it.querySelector(".pct").textContent = pct + "%";
      it.querySelector(".progress-fill").style.width = pct + "%";
      var elapsed = (Date.now() - startTime) / 1000;
      if (elapsed > 0.5) {
        var speed = e.loaded / elapsed;
        var remain = e.total - e.loaded;
        var eta = speed > 0 ? remain / speed : 0;
        it.querySelector(".progress-speed").textContent =
          fmtSize(speed) + "/s" + (eta > 1 ? " · 剩余 " + Math.ceil(eta) + " 秒" : "");
      }
    };

    xhr.onload = async function() {
      var it = document.getElementById(uid);
      if (it) it.remove();
      try {
        var j = JSON.parse(xhr.responseText);
        if (j.ok) {
          toast("上传成功：" + j.files.length + " 个文件");
          $("uploadHint").textContent = "已上传 " + j.files.length + " 个文件";
          await loadState();
          await loadLogs();
        } else {
          toast("上传失败：" + (j.error || ""), false);
        }
      } catch (e) { toast("上传错误：" + e.message, false); }
      resolve();
    };

    xhr.onerror = function() {
      var it = document.getElementById(uid);
      if (it) it.remove();
      toast("上传错误：网络连接失败", false);
      resolve();
    };

    xhr.open("POST", "/api/upload");
    xhr.send(fd);
  });
}
