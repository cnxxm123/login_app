// ===== 轻提示 =====
function toast(msg, isErr) {
    var t = document.createElement("div");
    t.className = "toast" + (isErr ? " err" : "");
    t.textContent = msg;
    document.body.appendChild(t);
    setTimeout(function () { t.classList.add("hide"); }, 2000);
    setTimeout(function () { t.remove(); }, 2600);
}

// ===== 保存：表单 POST /save/<path>，成功后跳回查看页（带 saved=1 显示"已保存"）=====
function saveFile() {
    var btn = document.getElementById("save-btn");
    var editor = document.getElementById("editor");
    if (btn.disabled) return;
    btn.disabled = true;
    btn.textContent = "保存中…";
    var fd = new FormData();
    fd.append("content", editor.value);
    fetch(window.EDITOR_CONFIG.urls.save, { method: "POST", body: fd })
        .then(function (r) {
            if (r.redirected) { location.href = r.url; return; }  // 成功：跟随 302 到查看页
            if (r.ok) { location.reload(); return; }
            btn.disabled = false;
            btn.textContent = "💾 保存";
            toast("保存失败（状态码 " + r.status + "）", true);
        })
        .catch(function () {
            btn.disabled = false;
            btn.textContent = "💾 保存";
            toast("保存失败：网络错误", true);
        });
}
document.getElementById("save-btn").addEventListener("click", saveFile);

// ===== 未保存修改标记 + 离开前确认 =====
var editor = document.getElementById("editor");
var dirty = false, original = editor.value;
editor.addEventListener("input", function () {
    dirty = editor.value !== original;
    document.getElementById("dirty-mark").classList.toggle("show", dirty);
});
window.addEventListener("beforeunload", function (e) {
    if (editor.value !== original) { e.preventDefault(); e.returnValue = ""; }  // 触发浏览器"确定离开"提示
});

// ===== Ctrl+S 保存 =====
document.addEventListener("keydown", function (e) {
    if ((e.ctrlKey || e.metaKey) && (e.key === "s" || e.key === "S")) {
        e.preventDefault();
        saveFile();
    }
});