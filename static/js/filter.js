// 取消标签：POST /tag/remove 后刷新。event 阻止点击冒泡，避免触发跳转
function removeTag(path, ev) {
    if (ev) { ev.preventDefault(); ev.stopPropagation(); }
    if (!confirm("移除标签「" + window.FILTER_CONFIG.tag + "」？")) return;
    var fd = new FormData();
    fd.append("path", path);
    fd.append("tag", window.FILTER_CONFIG.tag);
    fetch(window.FILTER_CONFIG.urls.tagRemove, { method: "POST", body: fd })
        .then(function (r) { return r.json(); })
        .then(function (res) { if (res.ok) location.reload(); });
}