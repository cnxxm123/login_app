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
// 还原：POST /game/restore/<name>，成功后跳回大厅
function restoreGame(name, displayName) {
    openModal({ title: "还原游戏", message: "确定将游戏「" + (displayName || name) + "」还原到大厅？", okText: "还原" })
        .then(function (ok) {
            if (!ok) return;
            fetch(window.GU_CONFIG.urls.restore + encodeURIComponent(name), { method: "POST" })
                .then(function (r) {
                    if (r.redirected) { location.href = r.url; return; }
                    if (r.ok) { location.reload(); }
                    else if (r.status === 409) { notify("大厅里已存在同名游戏，请先处理冲突"); }
                    else { notify("还原失败"); }
                });
        });
}
// 彻底删除已卸载游戏：POST /game/purge/<name>
function purgeGame(name, displayName) {
    openModal({ title: "彻底删除", message: "确定彻底删除游戏「" + (displayName || name) + "」？此操作不可恢复！", okText: "删除", danger: true })
        .then(function (ok) {
            if (!ok) return;
            fetch(window.GU_CONFIG.urls.purge + encodeURIComponent(name), { method: "POST" })
                .then(function (r) {
                    if (r.redirected) { location.href = r.url; return; }
                    if (r.ok) { location.reload(); }
                    else { notify("删除失败"); }
                });
        });
}