// ===== 备忘录页交互（仿 todos.js，去掉日期/类别/完成状态）=====
// 后端注入的配置：window.MEMOS_CONFIG = {memoData: {id: {title, content}}, urls: {...}}
var MEMO_DATA = window.MEMOS_CONFIG.memoData;

var editMask = document.getElementById("edit-mask");
var delMask = document.getElementById("del-mask");
var editTitle = document.getElementById("edit-title");
var editMemoTitle = document.getElementById("edit-memo-title");
var editContent = document.getElementById("edit-content");
var editingId = null;   // null=新增；数字=正在编辑的备忘 id
var pendingDel = null;  // 待删除的备忘 id

// ===== 打开 / 关闭弹窗 =====
function openEdit(id) {
    editingId = id || null;
    if (editingId) {
        editTitle.textContent = "✏️ 编辑备忘";
        // 编辑预填：标题 + 内容
        var rec = MEMO_DATA[String(editingId)] || {};
        editMemoTitle.value = rec.title || "";
        editContent.value = rec.content || "";
    } else {
        editTitle.textContent = "🗒 新增备忘";
        editMemoTitle.value = "";
        editContent.value = "";
    }
    editMask.hidden = false;
    editMemoTitle.focus();
}
function closeEdit() { editMask.hidden = true; editingId = null; }
function closeDel() { delMask.hidden = true; pendingDel = null; }

document.getElementById("fab-add").onclick = function () { openEdit(null); };
document.getElementById("edit-cancel").onclick = closeEdit;
editMask.addEventListener("click", function (ev) { if (ev.target === editMask) closeEdit(); });
// 弹窗内 Ctrl+Enter 快捷保存
editContent.addEventListener("keydown", function (ev) {
    if ((ev.ctrlKey || ev.metaKey) && ev.key === "Enter") saveMemo();
});

// ===== 保存（新增 / 更新共用）=====
function saveMemo() {
    var title = editMemoTitle.value.trim();
    var content = editContent.value.trim();
    if (!content) { toast("内容不能为空", true); return; }
    var btn = document.getElementById("edit-save");
    btn.disabled = true;
    var body = new URLSearchParams({ title: title, content: content });
    var url = editingId
        ? window.MEMOS_CONFIG.urls.update
        : window.MEMOS_CONFIG.urls.add;
    if (editingId) body.set("id", editingId);
    fetch(url, { method: "POST", body: body })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (!data.ok) { toast(data.error || "保存失败", true); btn.disabled = false; return; }
            // 维护编辑预填缓存：编辑覆盖原记录；新增记录后端返回的新 id
            if (editingId) {
                MEMO_DATA[String(editingId)] = { title: title, content: content };
            } else if (data.id) {
                MEMO_DATA[String(data.id)] = { title: title, content: content };
            }
            closeEdit();
            btn.disabled = false;
            refreshList();  // 局部刷新列表，避免整页刷新闪烁
        })
        .catch(function () { toast("网络错误，请重试", true); btn.disabled = false; });
}
document.getElementById("edit-save").onclick = saveMemo;

// ===== 局部刷新：编辑 / 删除后只更新列表区域，避免整页刷新闪烁 =====
function refreshList() {
    var q = document.getElementById("memo-q");
    var kw = q ? q.value : "";  // 记住当前搜索词，刷新后重新过滤
    fetch(window.location.pathname, {
        headers: { "X-Requested-With": "XMLHttpRequest" },
        cache: "no-store"  // 禁止缓存，保证拿到最新数据
    }).then(function (r) { return r.text(); }).then(function (html) {
        // 从新页面 HTML 中提取列表容器，整体替换旧列表（服务端渲染，顺序一致）
        var doc = new DOMParser().parseFromString(html, "text/html");
        var fresh = doc.getElementById("memo-list");
        var cur = document.getElementById("memo-list");
        if (fresh && cur) cur.innerHTML = fresh.innerHTML;
        // 同步总数统计
        var statTotal = document.getElementById("stat-total");
        var freshTotal = doc.getElementById("stat-total");
        if (statTotal && freshTotal) statTotal.textContent = freshTotal.textContent;
        // 兜底：操作成功后关闭可能仍打开的所有弹窗（删除 / 编辑等）
        document.querySelectorAll(".modal-mask").forEach(function (m) { m.hidden = true; });
        pendingDel = null;
        editingId = null;
        applySearch(kw);  // 保留当前搜索过滤
    }).catch(function () { toast("刷新列表失败，请手动刷新页面", true); });
}

// ===== 卡片点击编辑 / 删除（事件委托，列表局部刷新后依然有效）=====
document.addEventListener("click", function (ev) {
    // 删除按钮：弹确认框
    var delBtn = ev.target.closest(".memo-ops .op-btn.danger");
    if (delBtn) {
        ev.stopPropagation();
        pendingDel = delBtn.getAttribute("data-id");
        delMask.hidden = false;
        return;
    }
    // 编辑按钮
    var editBtn = ev.target.closest(".memo-ops .op-btn:not(.danger)");
    if (editBtn) {
        ev.stopPropagation();
        openEdit(Number(editBtn.getAttribute("data-id")));
        return;
    }
    // 点击卡片空白处 = 编辑
    var card = ev.target.closest(".memo-card");
    if (card) openEdit(Number(card.getAttribute("data-id")));
});

document.getElementById("del-cancel").onclick = closeDel;
delMask.addEventListener("click", function (ev) { if (ev.target === delMask) closeDel(); });

// ===== 删除 =====
document.getElementById("del-ok").onclick = function () {
    if (!pendingDel) return;
    var id = pendingDel;
    this.disabled = true;
    fetch(window.MEMOS_CONFIG.urls.delete, {
        method: "POST",
        body: new URLSearchParams({ id: id })
    }).then(function (r) { return r.json(); }).then(function (data) {
        this.disabled = false;
        if (!data.ok) { toast(data.error || "删除失败", true); closeDel(); return; }
        delete MEMO_DATA[String(id)];  // 同步预填缓存
        closeDel();
        refreshList();
    }.bind(this)).catch(function () {
        this.disabled = false;
        toast("网络错误，请重试", true);
    }.bind(this));
};

// ===== 前端搜索：按标题 / 内容过滤（不回后端，纯客户端过滤）=====
function applySearch(kw) {
    kw = (kw || "").trim().toLowerCase();
    document.querySelectorAll(".memo-card").forEach(function (card) {
        if (!kw) { card.style.display = ""; return; }
        var title = card.querySelector(".memo-title");
        var content = card.querySelector(".memo-content");
        var hit = (title && title.textContent.toLowerCase().indexOf(kw) >= 0) ||
                  (content && content.textContent.toLowerCase().indexOf(kw) >= 0);
        card.style.display = hit ? "" : "none";
    });
}
var memoQ = document.getElementById("memo-q");
if (memoQ) memoQ.addEventListener("input", function () { applySearch(memoQ.value); });
