// 编辑预填数据：{id: 内容}，由后端渲染（内容中的 < 已在后端转义，不会提前闭合本脚本标签）
var LOG_CONTENT = window.LOGS_CONFIG.logContent;

var editMask = document.getElementById("edit-mask");
var delMask = document.getElementById("del-mask");
var editTitle = document.getElementById("edit-title");
var editDate = document.getElementById("edit-date");
var editContent = document.getElementById("edit-content");
var editingId = null;   // null=新增；数字=正在编辑的日志 id
var pendingDel = null;  // 待删除的日志 id

// ===== 打开 / 关闭弹窗 =====
function openEdit(id) {
    editingId = id || null;
    if (editingId) {
        editTitle.textContent = "✏️ 编辑日志";
        editContent.value = LOG_CONTENT[String(editingId)] || "";
        // 编辑时保持原日期不变，用户可手动改
    } else {
        editTitle.textContent = "📝 新增日志";
        editContent.value = "";
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
    var content = editContent.value.trim();
    if (!date) { alert("请选择日期"); return; }
    if (!content) { alert("内容不能为空"); return; }
    var btn = document.getElementById("edit-save");
    btn.disabled = true;
    var body = new URLSearchParams({ log_date: date, content: content });
    var url = editingId
        ? window.LOGS_CONFIG.urls.update
        : window.LOGS_CONFIG.urls.add;
    if (editingId) body.set("id", editingId);
    fetch(url, { method: "POST", body: body })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (!data.ok) { alert(data.error || "保存失败"); btn.disabled = false; return; }
            location.reload();  // 保存成功后刷新，保证分组/顺序一致
        })
        .catch(function () { alert("网络错误，请重试"); btn.disabled = false; });
}
document.getElementById("edit-save").onclick = saveLog;

// ===== 日期分组折叠：点击标题展开 / 收起 =====
document.querySelectorAll(".log-group-head").forEach(function (head) {
    head.addEventListener("click", function () {
        head.closest(".log-group").classList.toggle("collapsed");
    });
    // 键盘支持：Enter / 空格也可切换（无障碍）
    head.addEventListener("keydown", function (ev) {
        if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); head.click(); }
    });
});

// ===== 编辑 / 删除按钮（事件委托，避免动态内容绑定）=====
document.addEventListener("click", function (ev) {
    var editBtn = ev.target.closest(".log-item .op-btn:not(.danger)");
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
        if (!data.ok) { alert(data.error || "删除失败"); return; }
        location.reload();
    }).catch(function () { alert("网络错误，请重试"); }).finally(function () {
        document.getElementById("del-ok").disabled = false;
    });
};

// ===== 客户端即时搜索：按内容过滤，空分组自动隐藏 =====
document.getElementById("log-q").addEventListener("input", function () {
    var kw = this.value.trim().toLowerCase();
    var matched = 0;
    document.querySelectorAll(".log-group").forEach(function (group) {
        var showGroup = false;
        group.querySelectorAll(".log-item").forEach(function (item) {
            var text = item.querySelector(".log-body").textContent.toLowerCase();
            var show = !kw || text.indexOf(kw) !== -1;
            item.style.display = show ? "" : "none";
            if (show) showGroup = true;
        });
        group.style.display = showGroup ? "" : "none";
        // 搜索联动：有匹配的分组自动展开；清空搜索后恢复默认折叠
        if (kw) {
            if (showGroup) group.classList.remove("collapsed");
        } else {
            group.classList.add("collapsed");
        }
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
});