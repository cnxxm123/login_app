// ===== 待办事项页交互（仿 logs.js，增加类别选择与完成勾选）=====
// 后端注入的配置：window.TODOS_CONFIG = {todoData: {id: {category, content}}, urls: {...}}
var TODO_DATA = window.TODOS_CONFIG.todoData;

var editMask = document.getElementById("edit-mask");
var delMask = document.getElementById("del-mask");
var editTitle = document.getElementById("edit-title");
var editDate = document.getElementById("edit-date");
var editCategory = document.getElementById("edit-category");
var editContent = document.getElementById("edit-content");
var editingId = null;   // null=新增；数字=正在编辑的待办 id
var pendingDel = null;  // 待删除的待办 id

// ===== 打开 / 关闭弹窗 =====
function openEdit(id) {
    editingId = id || null;
    if (editingId) {
        editTitle.textContent = "✏️ 编辑待办";
        // 编辑预填：内容 + 类别（日期保持原样，用户可手动改）
        var rec = TODO_DATA[String(editingId)] || {};
        editContent.value = rec.content || "";
        editCategory.value = rec.category || editCategory.options[0].value;
    } else {
        editTitle.textContent = "📋 新增待办";
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
    if ((ev.ctrlKey || ev.metaKey) && ev.key === "Enter") saveTodo();
});

// ===== 保存（新增 / 更新共用）=====
function saveTodo() {
    var date = editDate.value;
    var category = editCategory.value;
    var content = editContent.value.trim();
    if (!date) { toast("请选择日期", true); return; }
    if (!category) { toast("请选择类别", true); return; }
    if (!content) { toast("内容不能为空", true); return; }
    var btn = document.getElementById("edit-save");
    btn.disabled = true;
    var body = new URLSearchParams({ todo_date: date, category: category, content: content });
    var url = editingId
        ? window.TODOS_CONFIG.urls.update
        : window.TODOS_CONFIG.urls.add;
    if (editingId) body.set("id", editingId);
    fetch(url, { method: "POST", body: body })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (!data.ok) { toast(data.error || "保存失败", true); btn.disabled = false; return; }
            // 维护编辑预填缓存：编辑覆盖原记录；新增记录后端返回的新 id
            if (editingId) {
                TODO_DATA[String(editingId)] = { category: category, content: content };
            } else if (data.id) {
                TODO_DATA[String(data.id)] = { category: category, content: content };
            }
            closeEdit();
            btn.disabled = false;
            refreshList();  // 局部刷新列表，保持展开状态，避免整页刷新闪烁
        })
        .catch(function () { toast("网络错误，请重试", true); btn.disabled = false; });
}
document.getElementById("edit-save").onclick = saveTodo;

// ===== 折叠状态记忆：刷新 / 编辑后保持各分组的展开 / 折叠状态 =====
// 原理：用户手动展开的分组 key 记录到 localStorage，页面加载时据此恢复。
// 默认状态是"全部折叠"，因此只需记录"被展开"的分组。
var EXPAND_KEY = "todos_expanded";  // 每个页面独立命名空间，互不干扰

function loadExpanded() {
    try { return JSON.parse(localStorage.getItem(EXPAND_KEY)) || {}; }
    catch (e) { return {}; }  // localStorage 不可用或数据损坏时按无记忆处理
}

// 记录日期分组的展开状态：展开则记 key，折叠则移除
function rememberDateGroup(group) {
    var expanded = loadExpanded();
    var date = group.getAttribute("data-date");
    if (group.classList.contains("collapsed")) delete expanded[date];
    else expanded[date] = true;
    localStorage.setItem(EXPAND_KEY, JSON.stringify(expanded));
}

// 页面加载时恢复：把记录过"展开"的日期分组取消折叠
function restoreExpanded() {
    var expanded = loadExpanded();
    document.querySelectorAll(".todo-group").forEach(function (group) {
        var date = group.getAttribute("data-date");
        if (expanded[date]) group.classList.remove("collapsed");
    });
}
restoreExpanded();  // 首次加载恢复记忆的展开状态

// ===== 局部刷新：编辑 / 删除 / 转移后只更新列表区域，避免整页刷新闪烁 =====
function refreshList() {
    var q = document.getElementById("todo-q");
    var kw = q ? q.value : "";  // 记住当前搜索词，刷新后重新过滤
    fetch(window.location.pathname, {
        headers: { "X-Requested-With": "XMLHttpRequest" },
        cache: "no-store"  // 禁止缓存，保证拿到最新数据
    }).then(function (r) { return r.text(); }).then(function (html) {
        // 从新页面 HTML 中提取列表容器，整体替换旧列表（服务端渲染，分组/顺序/统计一致）
        var doc = new DOMParser().parseFromString(html, "text/html");
        var fresh = doc.getElementById("todo-list");
        var cur = document.getElementById("todo-list");
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

// ===== 日期分组折叠（事件委托，列表局部刷新后依然有效）=====
document.addEventListener("click", function (ev) {
    var head = ev.target.closest(".todo-group-head");
    if (head) {
        var group = head.closest(".todo-group");
        group.classList.toggle("collapsed");
        rememberDateGroup(group);  // 记忆当前展开状态
    }
});
// 键盘支持：聚焦到分组标题时按 Enter / 空格切换（委托绑定）
document.addEventListener("keydown", function (ev) {
    if (ev.key !== "Enter" && ev.key !== " ") return;
    var t = ev.target;
    if (t && t.closest(".todo-group-head")) {
        ev.preventDefault();
        t.click();
    }
});

// ===== 完成勾选（事件委托，列表局部刷新后依然有效）=====
// 勾选"完成"需确认，确认后转移到今天的工作日志
document.addEventListener("change", function (ev) {
    var box = ev.target.closest(".todo-item .todo-check input");
    if (!box) return;
    var item = box.closest(".todo-item");
    var id = item.getAttribute("data-id");
    if (box.checked) {
        // 勾选"完成"：先弹确认框，确认后才执行转移（后端 toggle 会写入今天的日志并删除待办）
        pendingMove = id;
        moveMask.hidden = false;
        return;
    }
    // 取消勾选（历史遗留的"已完成"数据恢复为未完成）：直接调接口，不转移
    fetch(window.TODOS_CONFIG.urls.toggle, {
        method: "POST",
        body: new URLSearchParams({ id: id })
    }).then(function (r) { return r.json(); }).then(function (data) {
        if (!data.ok) { toast(data.error || "操作失败", true); box.checked = true; return; }
        item.classList.toggle("done", false);  // 恢复未完成样式
        updateUndoneCount(1);                  // 未完成数 +1
    }).catch(function () { toast("网络错误，请重试", true); box.checked = true; });
});

// ===== 完成确认弹窗：确定 → 转移；取消 → 恢复勾选框 =====
var moveMask = document.getElementById("move-mask");
var pendingMove = null;  // 待确认完成的待办 id

function restoreMoveCheck() {
    // 取消时把勾选框恢复为未勾选（因为确认前它已被浏览器勾上）
    var box = document.querySelector('.todo-item[data-id="' + pendingMove + '"] .todo-check input');
    if (box) box.checked = false;
    moveMask.hidden = true;
    pendingMove = null;
}
document.getElementById("move-cancel").onclick = restoreMoveCheck;
moveMask.addEventListener("click", function (ev) { if (ev.target === moveMask) restoreMoveCheck(); });

document.getElementById("move-ok").onclick = function () {
    if (!pendingMove) return;
    var id = pendingMove;
    this.disabled = true;
    fetch(window.TODOS_CONFIG.urls.toggle, {
        method: "POST",
        body: new URLSearchParams({ id: id })
    }).then(function (r) { return r.json(); }).then(function (data) {
        if (!data.ok) { toast(data.error || "操作失败", true); }
        delete TODO_DATA[String(id)];  // 已完成的待办转移到日志，移除缓存
        refreshList();  // 局部刷新：待办消失、今天日志新增（成功或失败都恢复最新列表）
    }).catch(function () { toast("网络错误，请重试", true); }).finally(function () {
        document.getElementById("move-ok").disabled = false;
        moveMask.hidden = true;
        pendingMove = null;
    });
};

// 未完成统计联动：+1 / -1
function updateUndoneCount(delta) {
    var el = document.getElementById("stat-undone");
    if (el) el.textContent = Math.max(0, parseInt(el.textContent || "0", 10) + delta);
}

// ===== 编辑 / 删除按钮（事件委托，避免动态内容绑定）=====
document.addEventListener("click", function (ev) {
    var editBtn = ev.target.closest(".todo-item .op-btn:not(.danger)");
    if (editBtn) {
        var id = editBtn.getAttribute("data-id");
        var item = editBtn.closest(".todo-item");
        // 预填日期：从所在分组的 data-date 读取
        var group = item.closest(".todo-group");
        editDate.value = group.getAttribute("data-date");
        openEdit(Number(id));
        return;
    }
    var delBtn = ev.target.closest(".todo-item .op-btn.danger");
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
    fetch(window.TODOS_CONFIG.urls.delete, {
        method: "POST",
        body: new URLSearchParams({ id: id })
    }).then(function (r) { return r.json(); }).then(function (data) {
        if (!data.ok) { toast(data.error || "删除失败", true); return; }
        delete TODO_DATA[String(id)];  // 移除编辑预填缓存
        delMask.hidden = true;         // 立即关闭删除确认弹窗
        pendingDel = null;
        refreshList();
    }).catch(function () { toast("网络错误，请重试", true); }).finally(function () {
        document.getElementById("del-ok").disabled = false;
    });
};

// ===== 客户端即时搜索：按内容过滤，空分组自动隐藏 =====
// 抽成独立函数：输入时调用；列表局部刷新后也用当前搜索词重新过滤
function applySearch(kw) {
    kw = (kw || "").trim().toLowerCase();
    var matched = 0;
    document.querySelectorAll(".todo-group").forEach(function (group) {
        var showGroup = false;
        group.querySelectorAll(".todo-item").forEach(function (item) {
            var text = item.querySelector(".todo-content").textContent.toLowerCase();
            var show = !kw || text.indexOf(kw) !== -1;
            item.style.display = show ? "" : "none";
            if (show) showGroup = true;
        });
        // 日期分组：全部无匹配则整组隐藏；搜索时自动展开有匹配的分组
        // （清空搜索时保持用户手动展开的分组，由 restoreExpanded 决定）
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
            noneTip.textContent = "没有匹配「" + kw + "」的待办。";
            document.querySelector(".content").appendChild(noneTip);
        }
        noneTip.style.display = "";
    } else if (noneTip) {
        noneTip.style.display = "none";
    }
}
document.getElementById("todo-q").addEventListener("input", function () {
    applySearch(this.value);
});
