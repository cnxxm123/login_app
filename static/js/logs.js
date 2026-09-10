// 编辑预填数据：{id: {category, content}}，由后端渲染（内容中的 < 已在后端转义，不会提前闭合本脚本标签）
var LOG_CONTENT = window.LOGS_CONFIG.logContent;

var editMask = document.getElementById("edit-mask");
var delMask = document.getElementById("del-mask");
var editTitle = document.getElementById("edit-title");
var editDate = document.getElementById("edit-date");
var editCategory = document.getElementById("edit-category");
var editContent = document.getElementById("edit-content");
var editingId = null;   // null=新增；数字=正在编辑的日志 id
var pendingDel = null;  // 待删除的日志 id

// ===== 打开 / 关闭弹窗 =====
function openEdit(id) {
    editingId = id || null;
    if (editingId) {
        editTitle.textContent = "✏️ 编辑日志";
        // 编辑预填：内容 + 类别（日期保持原样，用户可手动改）
        var rec = LOG_CONTENT[String(editingId)] || {};
        editContent.value = rec.content || "";
        editCategory.value = rec.category || editCategory.options[0].value;
    } else {
        editTitle.textContent = "📝 新增日志";
        editContent.value = "";
        editCategory.selectedIndex = 0;  // 默认选中第一个类别
        var t = new Date();
        editDate.value = t.getFullYear() + "-" +
            String(t.getMonth() + 1).padStart(2, "0") + "-" +
            String(t.getDate()).padStart(2, "0");
    }
    editMask.hidden = false;
    editContent.focus();
}
function closeEdit() { editMask.hidden = true; editingId = null; }
function closeDel() { delMask.hidden = true; pendingDel = null; }

document.getElementById("fab-add").onclick = function () { openEdit(null); };
document.getElementById("edit-cancel").onclick = closeEdit;
editMask.addEventListener("click", function (ev) { if (ev.target === editMask) closeEdit(); });
// 弹窗内 Ctrl+Enter 快捷保存
editContent.addEventListener("keydown", function (ev) {
    if ((ev.ctrlKey || ev.metaKey) && ev.key === "Enter") saveLog();
});

// ===== 保存（新增 / 更新共用）=====
function saveLog() {
    var date = editDate.value;
    var category = editCategory.value;
    var content = editContent.value.trim();
    if (!date) { toast("请选择日期", true); return; }
    if (!category) { toast("请选择类别", true); return; }
    if (!content) { toast("内容不能为空", true); return; }
    var btn = document.getElementById("edit-save");
    btn.disabled = true;
    var body = new URLSearchParams({ log_date: date, category: category, content: content });
    var url = editingId
        ? window.LOGS_CONFIG.urls.update
        : window.LOGS_CONFIG.urls.add;
    if (editingId) body.set("id", editingId);
    fetch(url, { method: "POST", body: body })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (!data.ok) { toast(data.error || "保存失败", true); btn.disabled = false; return; }
            // 维护编辑预填缓存：编辑覆盖原记录；新增记录后端返回的新 id
            if (editingId) {
                LOG_CONTENT[String(editingId)] = { category: category, content: content };
            } else if (data.id) {
                LOG_CONTENT[String(data.id)] = { category: category, content: content };
            }
            closeEdit();
            btn.disabled = false;
            refreshList();  // 局部刷新列表，保持展开状态，避免整页刷新闪烁
        })
        .catch(function () { toast("网络错误，请重试", true); btn.disabled = false; });
}
document.getElementById("edit-save").onclick = saveLog;

// ===== 折叠状态记忆：手风琴模式，同一时间只展开一个日期分组、一个类别分组 =====
// 原理：刷新/编辑后从 localStorage 恢复上次唯一展开的日期/类别分组。
// 默认状态是"全部折叠"。
var EXPAND_KEY = "logs_expanded";  // 每个页面独立命名空间，互不干扰

function loadExpanded() {
    try { return JSON.parse(localStorage.getItem(EXPAND_KEY)) || {}; }
    catch (e) { return {}; }  // localStorage 不可用或数据损坏时按无记忆处理
}

// 页面加载时恢复：把记录过"展开"的日期 / 类别分组取消折叠
function restoreExpanded() {
    var expanded = loadExpanded();
    document.querySelectorAll(".log-group").forEach(function (group) {
        var date = group.getAttribute("data-date");
        if (expanded[date]) group.classList.remove("collapsed");
        group.querySelectorAll(".log-cat-group").forEach(function (catGroup) {
            if (expanded[date + "|" + catGroup.getAttribute("data-cat")]) {
                catGroup.classList.remove("collapsed");
            }
        });
    });
}
restoreExpanded();  // 首次加载恢复记忆的展开状态

// 手风琴模式：收起所有兄弟分组后，将当前展开状态写入 localStorage
function saveAllExpanded() {
    var expanded = {};
    document.querySelectorAll(".log-group:not(.collapsed)").forEach(function (g) {
        var date = g.getAttribute("data-date");
        expanded[date] = true;
        g.querySelectorAll(".log-cat-group:not(.collapsed)").forEach(function (cg) {
            expanded[date + "|" + cg.getAttribute("data-cat")] = true;
        });
    });
    localStorage.setItem(EXPAND_KEY, JSON.stringify(expanded));
}

// ===== 局部刷新：编辑 / 删除 / 转移后只更新列表区域，避免整页刷新闪烁 =====
function refreshList() {
    var q = document.getElementById("log-q");
    var kw = q ? q.value : "";  // 记住当前搜索词，刷新后重新过滤
    fetch(window.location.pathname, {
        headers: { "X-Requested-With": "XMLHttpRequest" },
        cache: "no-store"  // 禁止缓存，保证拿到最新数据
    }).then(function (r) { return r.text(); }).then(function (html) {
        // 从新页面 HTML 中提取列表容器，整体替换旧列表（服务端渲染，分组/顺序/统计一致）
        var doc = new DOMParser().parseFromString(html, "text/html");
        var fresh = doc.getElementById("log-list");
        var cur = document.getElementById("log-list");
        if (fresh && cur) cur.innerHTML = fresh.innerHTML;
        // 兜底：操作成功后关闭可能仍打开的所有弹窗（删除 / 转移 / 编辑等）
        document.querySelectorAll(".modal-mask").forEach(function (m) { m.hidden = true; });
        pendingDel = null;
        pendingMove = null;
        editingId = null;
        restoreExpanded();  // 恢复用户展开的分组
        applySearch(kw);    // 保留当前搜索过滤
    }).catch(function () { toast("刷新列表失败，请手动刷新页面", true); });
}

// ===== 日期/类别分组折叠 —— 手风琴模式（事件委托，列表局部刷新后依然有效）=====
// 日期分组：同一时间只展开一个日期；类别分组：同一日期下只展开一个类别
document.addEventListener("click", function (ev) {
    var head = ev.target.closest(".log-group-head");
    if (head) {
        var group = head.closest(".log-group");
        var wasCollapsed = group.classList.contains("collapsed");
        // 手风琴：先折叠所有日期分组
        document.querySelectorAll(".log-group").forEach(function (g) {
            g.classList.add("collapsed");
        });
        // 如果原来是折叠的，则展开当前分组；否则保持折叠（点击已展开的 = 折叠）
        if (wasCollapsed) group.classList.remove("collapsed");
        saveAllExpanded();
        return;
    }
    var catHead = ev.target.closest(".log-cat-head");
    if (catHead) {
        var catGroup = catHead.closest(".log-cat-group");
        var wasCollapsed = catGroup.classList.contains("collapsed");
        var dateGroup = catGroup.closest(".log-group");
        // 手风琴：先折叠同一日期下的所有类别分组
        dateGroup.querySelectorAll(".log-cat-group").forEach(function (cg) {
            cg.classList.add("collapsed");
        });
        // 如果原来是折叠的，则展开当前分组；否则保持折叠
        if (wasCollapsed) catGroup.classList.remove("collapsed");
        saveAllExpanded();
    }
});
// 键盘支持：聚焦到分组标题时按 Enter / 空格切换（委托绑定）
document.addEventListener("keydown", function (ev) {
    if (ev.key !== "Enter" && ev.key !== " ") return;
    var t = ev.target;
    if (t && t.closest(".log-group-head, .log-cat-head")) {
        ev.preventDefault();
        t.click();
    }
});

// ===== 编辑 / 转为待办 / 删除按钮（事件委托，避免动态内容绑定）=====
document.addEventListener("click", function (ev) {
    var moveBtn = ev.target.closest(".log-item .op-btn.move");
    if (moveBtn) {
        pendingMove = moveBtn.getAttribute("data-id");
        moveMask.hidden = false;
        return;
    }
    var editBtn = ev.target.closest(".log-item .op-btn:not(.danger):not(.move)");
    if (editBtn) {
        var id = editBtn.getAttribute("data-id");
        var item = editBtn.closest(".log-item");
        // 预填日期：从所在分组的 data-date 读取
        var group = item.closest(".log-group");
        editDate.value = group.getAttribute("data-date");
        openEdit(Number(id));
        return;
    }
    var delBtn = ev.target.closest(".log-item .op-btn.danger");
    if (delBtn) {
        pendingDel = delBtn.getAttribute("data-id");
        delMask.hidden = false;
    }
});

document.getElementById("del-cancel").onclick = closeDel;
delMask.addEventListener("click", function (ev) { if (ev.target === delMask) closeDel(); });

document.getElementById("del-ok").onclick = function () {
    if (!pendingDel) return;
    var id = pendingDel;
    this.disabled = true;
    fetch(window.LOGS_CONFIG.urls.delete, {
        method: "POST",
        body: new URLSearchParams({ id: id })
    }).then(function (r) { return r.json(); }).then(function (data) {
        if (!data.ok) { toast(data.error || "删除失败", true); return; }
        delete LOG_CONTENT[String(id)];  // 移除编辑预填缓存
        delMask.hidden = true;           // 立即关闭删除确认弹窗
        pendingDel = null;
        refreshList();
    }).catch(function () { toast("网络错误，请重试", true); }).finally(function () {
        document.getElementById("del-ok").disabled = false;
    });
};

// ===== 转为待办：确认后转移到今天的待办并删除原日志 =====
var moveMask = document.getElementById("move-mask");
var pendingMove = null;
document.getElementById("move-cancel").onclick = function () { moveMask.hidden = true; pendingMove = null; };
moveMask.addEventListener("click", function (ev) { if (ev.target === moveMask) { moveMask.hidden = true; pendingMove = null; } });

document.getElementById("move-ok").onclick = function () {
    if (!pendingMove) return;
    var id = pendingMove;
    this.disabled = true;
    fetch(window.LOGS_CONFIG.urls.moveTodo, {
        method: "POST",
        body: new URLSearchParams({ id: id })
    }).then(function (r) { return r.json(); }).then(function (data) {
        if (!data.ok) { toast(data.error || "转移失败", true); return; }
        delete LOG_CONTENT[String(id)];  // 原日志已转移，移除编辑预填缓存
        moveMask.hidden = true;          // 立即关闭转移确认弹窗
        pendingMove = null;
        refreshList();  // 局部刷新：日志消失、今天的待办新增
    }).catch(function () { toast("网络错误，请重试", true); }).finally(function () {
        document.getElementById("move-ok").disabled = false;
    });
};

// ===== 客户端即时搜索：按内容过滤，空分组自动隐藏 =====
// 抽成独立函数：输入时调用；列表局部刷新后也用当前搜索词重新过滤
function applySearch(kw) {
    kw = (kw || "").trim().toLowerCase();
    var matched = 0;
    document.querySelectorAll(".log-group").forEach(function (group) {
        var showGroup = false;
        // 先逐类别分组过滤：类别内无匹配则整组隐藏
        group.querySelectorAll(".log-cat-group").forEach(function (catGroup) {
            var showCat = false;
            catGroup.querySelectorAll(".log-item").forEach(function (item) {
                var text = item.querySelector(".log-body").textContent.toLowerCase();
                var show = !kw || text.indexOf(kw) !== -1;
                item.style.display = show ? "" : "none";
                if (show) showCat = true;
            });
            catGroup.style.display = showCat ? "" : "none";
            // 搜索联动：有匹配的类别分组自动展开（仅在搜索词非空时干预折叠状态，
            // 清空搜索时保持用户手动展开的分组，由 restoreExpanded 决定）
            if (kw && showCat) catGroup.classList.remove("collapsed");
            if (showCat) showGroup = true;
        });
        // 日期分组：类别全部无匹配则整组隐藏
        group.style.display = showGroup ? "" : "none";
        if (kw && showGroup) group.classList.remove("collapsed");
        if (showGroup) matched++;
    });
    // 无匹配时显示提示
    var noneTip = document.getElementById("filter-none");
    if (!matched && kw) {
        if (!noneTip) {
            noneTip = document.createElement("div");
            noneTip.id = "filter-none";
            noneTip.className = "empty";
            noneTip.textContent = "没有匹配「" + kw + "」的日志。";
            document.querySelector(".content").appendChild(noneTip);
        }
        noneTip.style.display = "";
    } else if (noneTip) {
        noneTip.style.display = "none";
    }
}
document.getElementById("log-q").addEventListener("input", function () {
    applySearch(this.value);
});