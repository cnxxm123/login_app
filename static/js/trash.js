// ===== 通用确认弹窗：resolve true / false =====
function openModal(opts) {
    return new Promise(function (resolve) {
        var mask = document.getElementById("modal-mask");
        document.getElementById("modal-title").textContent = opts.title || "提示";
        document.getElementById("modal-msg").textContent = opts.message || "";
        var okBtn = document.getElementById("modal-ok");
        okBtn.textContent = opts.okText || "确定";
        okBtn.classList.toggle("danger", !!opts.danger);
        document.getElementById("modal-cancel").textContent = opts.cancelText || "取消";
        function close() { mask.hidden = true; }
        okBtn.onclick = function () { close(); resolve(true); };
        document.getElementById("modal-cancel").onclick = function () { close(); resolve(false); };
        mask.onclick = function (e) { if (e.target === mask) { close(); resolve(false); } };
        mask.hidden = false;
    });
}
// 轻提示：复用弹窗做纯提示（沙箱禁用 alert）
function notify(msg) {
    openModal({ title: "提示", message: msg, okText: "知道了" });
}
// 还原：POST /trash/restore/<name>，成功后跳回原位置目录
function restoreItem(name) {
    openModal({ title: "还原", message: "确定将此项还原到原位置？", okText: "还原" })
        .then(function (ok) {
            if (!ok) return;
            fetch(window.TRASH_CONFIG.urls.restore + encodeURIComponent(name), { method: "POST" })
                .then(function (r) {
                    if (r.redirected) { location.href = r.url; return; }
                    if (r.ok) { location.reload(); }
                    else if (r.status === 409) { notify("原位置已存在同名文件/文件夹，请先处理冲突"); }
                    else { notify("还原失败"); }
                });
        });
}
// 彻底删除单个条目：POST /trash/delete/<name>
function deleteItem(name) {
    openModal({ title: "彻底删除", message: "确定彻底删除？此操作不可恢复！", okText: "删除", danger: true })
        .then(function (ok) {
            if (!ok) return;
            fetch(window.TRASH_CONFIG.urls.delete + encodeURIComponent(name), { method: "POST" })
                .then(function (r) {
                    if (r.redirected) { location.href = r.url; return; }
                    if (r.ok) { location.reload(); }
                    else { notify("删除失败"); }
                });
        });
}
// 清空回收站：POST /trash/empty
function emptyTrash() {
    openModal({ title: "清空回收站", message: "确定清空回收站？所有内容将被彻底删除，不可恢复！", okText: "清空", danger: true })
        .then(function (ok) {
            if (!ok) return;
            fetch(window.TRASH_CONFIG.urls.empty, { method: "POST" })
                .then(function (r) {
                    if (r.redirected) { location.href = r.url; return; }
                    if (r.ok) { location.reload(); }
                    else { notify("清空失败"); }
                });
        });
}