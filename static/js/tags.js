// ===== 删除标签 =====
var pendingTag = null;   // 待删除的标签名
var mask = document.getElementById("del-mask");

// 事件委托：避免标签名含引号时内联 onclick 语法错误；data-name 由 Jinja 自动转义，读取安全
// 绑在 document 上，标签为空（无 #tag-cloud）时也不报错
document.addEventListener("click", function (ev) {
    var btn = ev.target.closest(".tag-del");
    if (!btn) return;
    ev.preventDefault();
    pendingTag = btn.getAttribute("data-name");
    document.getElementById("del-name").textContent = pendingTag;
    mask.hidden = false;
});
function closeDel() {
    mask.hidden = true;
    pendingTag = null;
}
document.getElementById("del-cancel").onclick = closeDel;
mask.addEventListener("click", function (ev) { if (ev.target === mask) closeDel(); });

document.getElementById("del-ok").onclick = function () {
    if (!pendingTag) return;
    var name = pendingTag;
    this.disabled = true;  // 防重复提交
    fetch(window.TAGS_CONFIG.urls.tagDelete, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: "tag=" + encodeURIComponent(name)
    }).then(function (r) { return r.json(); }).then(function (data) {
        if (data.ok) {
            // 移除对应胶囊，并更新计数；全部删完则显示空提示
            var wrap = document.querySelector('.tag-wrap[data-name="' + CSS.escape(name) + '"]');
            if (wrap) wrap.remove();
            var countEl = document.getElementById("tag-count");
            var left = document.querySelectorAll(".tag-wrap").length;
            countEl.textContent = left;
            if (left === 0) {
                var cloud = document.getElementById("tag-cloud");
                if (cloud) {
                    var empty = document.createElement("div");
                    empty.className = "empty";
                    empty.textContent = "还没有任何标签。在文件浏览页点击卡片上的 🏷 按钮即可给文件打标签。";
                    cloud.replaceWith(empty);
                }
            }
        } else {
            toast(data.error || "删除失败", true);
        }
        closeDel();
    }).catch(function () {
        toast("网络错误，请重试", true);
        closeDel();
    }).finally(function () {
        document.getElementById("del-ok").disabled = false;
    });
};