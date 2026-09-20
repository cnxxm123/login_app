// ===== 待办事项页交互（含截止日期、拖拽排序）=====
var TODO_DATA = window.TODOS_CONFIG.todoData;

var editMask = document.getElementById("edit-mask");
var delMask = document.getElementById("del-mask");
var editTitle = document.getElementById("edit-title");
var editDate = document.getElementById("edit-date");
var editDue = document.getElementById("edit-due");
var editContent = document.getElementById("edit-content");
var editingId = null;
var pendingDel = null;

// ===== 打开 / 关闭弹窗 =====
function openEdit(id) {
    editingId = id || null;
    if (editingId) {
        editTitle.textContent = "\u270f\ufe0f \u7f16\u8f91\u5f85\u529e";
        var rec = TODO_DATA[String(editingId)] || {};
        editContent.value = rec.content || "";
        editDue.value = rec.due_date || "";
    } else {
        editTitle.textContent = "\ud83d\udccb \u65b0\u589e\u5f85\u529e";
        editContent.value = "";
        editDue.value = "";
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
editContent.addEventListener("keydown", function (ev) {
    if ((ev.ctrlKey || ev.metaKey) && ev.key === "Enter") saveTodo();
});

// ===== 保存 =====
function saveTodo() {
    var date = editDate.value;
    var content = editContent.value.trim();
    var dueDate = (editDue ? editDue.value : "").trim();
    if (!date) { toast("\u8bf7\u9009\u62e9\u65e5\u671f", true); return; }
    if (!content) { toast("\u5185\u5bb9\u4e0d\u80fd\u4e3a\u7a7a", true); return; }
    var btn = document.getElementById("edit-save");
    btn.disabled = true;
    var body = new URLSearchParams({ todo_date: date, content: content });
    if (dueDate) body.set("due_date", dueDate);
    var url = editingId
        ? window.TODOS_CONFIG.urls.update
        : window.TODOS_CONFIG.urls.add;
    if (editingId) body.set("id", editingId);
    fetch(url, { method: "POST", body: body })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (!data.ok) { toast(data.error || "\u4fdd\u5b58\u5931\u8d25", true); btn.disabled = false; return; }
            if (editingId) {
                TODO_DATA[String(editingId)] = { content: content, due_date: dueDate };
            } else if (data.id) {
                TODO_DATA[String(data.id)] = { content: content, due_date: dueDate };
            }
            closeEdit();
            btn.disabled = false;
            refreshList();
        })
        .catch(function () { toast("\u7f51\u7edc\u9519\u8bef\uff0c\u8bf7\u91cd\u8bd5", true); btn.disabled = false; });
}
document.getElementById("edit-save").onclick = saveTodo;

// ===== 拖拽排序 =====
var dragSrc = null;  // 被拖拽的待办元素

document.addEventListener("dragstart", function (ev) {
    var item = ev.target.closest(".todo-item[draggable]");
    if (!item) return;
    dragSrc = item;
    item.classList.add("dragging");
    ev.dataTransfer.effectAllowed = "move";
    ev.dataTransfer.setData("text/plain", item.getAttribute("data-id"));
});

document.addEventListener("dragend", function (ev) {
    var item = ev.target.closest(".todo-item");
    if (item) item.classList.remove("dragging");
    document.querySelectorAll(".todo-item").forEach(function (el) {
        el.classList.remove("drag-over");
    });
    dragSrc = null;
});

document.addEventListener("dragover", function (ev) {
    ev.preventDefault();
    var item = ev.target.closest(".todo-item");
    if (!item || item === dragSrc) return;
    ev.dataTransfer.dropEffect = "move";
    // 高亮目标位置
    document.querySelectorAll(".todo-item").forEach(function (el) { el.classList.remove("drag-over"); });
    item.classList.add("drag-over");
});

document.addEventListener("drop", function (ev) {
    ev.preventDefault();
    var target = ev.target.closest(".todo-item");
    if (!target || !dragSrc || target === dragSrc) return;
    target.classList.remove("drag-over");

    var srcGroup = dragSrc.closest(".todo-items");
    var tgtGroup = target.closest(".todo-items");
    if (srcGroup !== tgtGroup) return;  // 只允许同日期分组内拖拽

    // DOM 层面移动
    var children = Array.prototype.slice.call(srcGroup.querySelectorAll(".todo-item"));
    var srcIdx = children.indexOf(dragSrc);
    var tgtIdx = children.indexOf(target);
    if (srcIdx < 0 || tgtIdx < 0) return;

    if (srcIdx < tgtIdx) {
        srcGroup.insertBefore(dragSrc, target.nextSibling);
    } else {
        srcGroup.insertBefore(dragSrc, target);
    }

    // 构建新顺序并发送到后端
    var newChildren = srcGroup.querySelectorAll(".todo-item");
    var orders = [];
    Array.prototype.forEach.call(newChildren, function (el, i) {
        orders.push({ id: Number(el.getAttribute("data-id")), sort_order: i });
    });
    fetch(window.TODOS_CONFIG.urls.reorder, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(orders)
    }).then(function (r) { return r.json(); }).then(function (data) {
        if (data.ok) {
            toast("\u6392\u5e8f\u5df2\u4fdd\u5b58");
        }
    }).catch(function () { /* 静默失败，下次刷新恢复 */ });
});

// ===== 局部刷新 =====
function refreshList() {
    var q = document.getElementById("todo-q");
    var kw = q ? q.value : "";
    fetch(window.location.pathname, {
        headers: { "X-Requested-With": "XMLHttpRequest" },
        cache: "no-store"
    }).then(function (r) { return r.text(); }).then(function (html) {
        var doc = new DOMParser().parseFromString(html, "text/html");
        var fresh = doc.getElementById("todo-list");
        var cur = document.getElementById("todo-list");
        if (fresh && cur) cur.innerHTML = fresh.innerHTML;
        document.querySelectorAll(".modal-mask").forEach(function (m) { m.hidden = true; });
        pendingDel = null;
        editingId = null;
        applySearch(kw);
    }).catch(function () { toast("\u5237\u65b0\u5217\u8868\u5931\u8d25\uff0c\u8bf7\u624b\u52a8\u5237\u65b0\u9875\u9762", true); });
}

// ===== 完成勾选 =====
document.addEventListener("change", function (ev) {
    var box = ev.target.closest(".todo-item .todo-check input");
    if (!box) return;
    var item = box.closest(".todo-item");
    var id = item.getAttribute("data-id");
    var wasDone = item.classList.contains("done");
    fetch(window.TODOS_CONFIG.urls.toggle, {
        method: "POST",
        body: new URLSearchParams({ id: id })
    }).then(function (r) { return r.json(); }).then(function (data) {
        if (!data.ok) { toast(data.error || "\u64cd\u4f5c\u5931\u8d25", true); box.checked = wasDone; return; }
        item.classList.toggle("done");
        updateUndoneCount(wasDone ? 1 : -1);
    }).catch(function () { toast("\u7f51\u7edc\u9519\u8bef\uff0c\u8bf7\u91cd\u8bd5", true); box.checked = wasDone; });
});

function updateUndoneCount(delta) {
    var el = document.getElementById("stat-undone");
    if (el) el.textContent = Math.max(0, parseInt(el.textContent || "0", 10) + delta);
}

// ===== 编辑 / 删除按钮 =====
document.addEventListener("click", function (ev) {
    var editBtn = ev.target.closest(".todo-item .op-btn:not(.danger)");
    if (editBtn) {
        var id = editBtn.getAttribute("data-id");
        var item = editBtn.closest(".todo-item");
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
        if (!data.ok) { toast(data.error || "\u5220\u9664\u5931\u8d25", true); return; }
        delete TODO_DATA[String(id)];
        delMask.hidden = true;
        pendingDel = null;
        refreshList();
    }).catch(function () { toast("\u7f51\u7edc\u9519\u8bef\uff0c\u8bf7\u91cd\u8bd5", true); }).finally(function () {
        document.getElementById("del-ok").disabled = false;
    });
};

// ===== 搜索过滤 =====
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
        group.style.display = showGroup ? "" : "none";
        if (showGroup) matched++;
    });
    var noneTip = document.getElementById("filter-none");
    if (!matched && kw) {
        if (!noneTip) {
            noneTip = document.createElement("div");
            noneTip.id = "filter-none";
            noneTip.className = "empty";
            noneTip.textContent = "\u6ca1\u6709\u5339\u914d\u300c" + kw + "\u300d\u7684\u5f85\u529e\u3002";
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