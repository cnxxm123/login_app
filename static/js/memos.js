// ===== 备忘录页交互（仿 todos.js，去掉日期/类别/完成状态）=====
// 后端注入的配置：window.MEMOS_CONFIG = {memoData: {id: {title, content, category, images}}, categories: [], imageUrl, urls: {...}}
var MEMO_DATA = window.MEMOS_CONFIG.memoData;

var editMask = document.getElementById("edit-mask");
var delMask = document.getElementById("del-mask");
var editTitle = document.getElementById("edit-title");
var editMemoTitle = document.getElementById("edit-memo-title");
var editMemoCategory = document.getElementById("edit-memo-category");
var editContent = document.getElementById("edit-content");
var editImgGrid = document.getElementById("memo-img-grid");
var editImgInput = document.getElementById("memo-img-input");
var editingId = null;   // null=新增；数字=正在编辑的备忘 id
var pendingDel = null;  // 待删除的备忘 id
var currentImages = []; // 当前编辑弹窗的图片文件名列表（新增为空，编辑从 MEMO_DATA 恢复）

// 图片访问 URL：把模板里的 __NAME__ 占位符替换成实际文件名
function imageUrl(name) {
    return window.MEMOS_CONFIG.imageUrl.replace("__NAME__", name);
}

// ===== 图片放大查看（lightbox）：点缩略图看大图，支持前后切换 =====
var lbMask = document.getElementById("img-lightbox");
var lbImg = document.getElementById("lb-img");
var lbImages = [];  // 当前可浏览的图片 URL 列表
var lbIndex = 0;    // 当前显示到第几张

function showLightbox() {
    if (!lbImages.length) return;
    lbImg.src = lbImages[lbIndex];
    lbMask.hidden = false;
    // 只有一张图时隐藏前后切换按钮
    document.getElementById("lb-prev").style.display = lbImages.length > 1 ? "" : "none";
    document.getElementById("lb-next").style.display = lbImages.length > 1 ? "" : "none";
}
function openLightbox(urls, index) {
    if (!urls || !urls.length) return;
    lbImages = urls.slice();
    lbIndex = Math.max(0, Math.min(index || 0, urls.length - 1));
    showLightbox();
}
function closeLightbox() { lbMask.hidden = true; }
function stepLightbox(delta) {
    if (lbImages.length < 2) return;
    lbIndex = (lbIndex + delta + lbImages.length) % lbImages.length;
    showLightbox();
}
if (lbMask) {
    document.getElementById("lb-close").onclick = closeLightbox;
    document.getElementById("lb-prev").onclick = function () { stepLightbox(-1); };
    document.getElementById("lb-next").onclick = function () { stepLightbox(1); };
    // 点遮罩空白处关闭
    lbMask.addEventListener("click", function (ev) { if (ev.target === lbMask) closeLightbox(); });
    // 键盘：Esc 关闭，左右方向键切换
    document.addEventListener("keydown", function (ev) {
        if (lbMask.hidden) return;
        if (ev.key === "Escape") closeLightbox();
        else if (ev.key === "ArrowLeft") stepLightbox(-1);
        else if (ev.key === "ArrowRight") stepLightbox(1);
    });
}

// ===== 渲染编辑弹窗内的图片预览网格 =====
function renderImages() {
    if (!editImgGrid) return;
    editImgGrid.innerHTML = "";
    currentImages.forEach(function (name) {
        var item = document.createElement("div");
        item.className = "memo-img-item";
        var img = document.createElement("img");
        img.src = imageUrl(name);
        img.alt = "";
        // 点击编辑弹窗内的预览图也放大查看
        img.onclick = function () {
            openLightbox(currentImages.map(imageUrl), currentImages.indexOf(name));
        };
        var del = document.createElement("button");
        del.type = "button";
        del.className = "memo-img-del";
        del.title = "移除这张图片";
        del.textContent = "×";
        del.onclick = function () {
            // 只从预览移除，保存时才真正删除服务器上的文件
            currentImages = currentImages.filter(function (n) { return n !== name; });
            renderImages();
        };
        item.appendChild(img);
        item.appendChild(del);
        editImgGrid.appendChild(item);
    });
    // input 复用：清空 value，让再次选择同一张图片时也能触发 change
    if (editImgInput) editImgInput.value = "";
}

// ===== 选择图片后逐个上传 =====
function uploadImages(files) {
    Array.prototype.forEach.call(files, function (file) {
        if (!file.type || file.type.indexOf("image/") !== 0) {
            toast("「" + file.name + "」不是图片，已跳过", true);
            return;
        }
        var fd = new FormData();
        fd.append("image", file);
        fetch(window.MEMOS_CONFIG.urls.uploadImage, { method: "POST", body: fd })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (!data.ok) { toast(data.error || "图片上传失败", true); return; }
                currentImages.push(data.filename);  // 记录后端返回的文件名
                renderImages();
            })
            .catch(function () { toast("图片上传失败，请重试", true); });
    });
}
if (editImgInput) {
    editImgInput.addEventListener("change", function () {
        if (this.files && this.files.length) uploadImages(this.files);
    });
}

// ===== 打开 / 关闭弹窗 =====
function openEdit(id) {
    editingId = id || null;
    if (editingId) {
        editTitle.textContent = "✏️ 编辑备忘";
        // 编辑预填：标题 + 分类 + 内容 + 图片
        var rec = MEMO_DATA[String(editingId)] || {};
        editMemoTitle.value = rec.title || "";
        editMemoCategory.value = rec.category || "";
        editContent.value = rec.content || "";
        currentImages = (rec.images || []).slice();
    } else {
        editTitle.textContent = "🗒 新增备忘";
        editMemoTitle.value = "";
        editMemoCategory.value = "";
        editContent.value = "";
        currentImages = [];
    }
    renderImages();
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
    var category = (editMemoCategory ? editMemoCategory.value.trim() : "");
    var content = editContent.value.trim();
    if (!content) { toast("内容不能为空", true); return; }
    var btn = document.getElementById("edit-save");
    btn.disabled = true;
    var body = new URLSearchParams({ title: title, content: content });
    if (category) body.set("category", category);
    // 把当前图片文件名列表作为可重复的 images 字段一并提交
    currentImages.forEach(function (name) { body.append("images", name); });
    var url = editingId
        ? window.MEMOS_CONFIG.urls.update
        : window.MEMOS_CONFIG.urls.add;
    if (editingId) body.set("id", editingId);
    fetch(url, { method: "POST", body: body })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (!data.ok) { toast(data.error || "保存失败", true); btn.disabled = false; return; }
            // 维护编辑预填缓存：编辑覆盖原记录；新增记录后端返回的新 id
            var rec = { title: title, content: content, category: category, images: currentImages.slice() };
            if (editingId) {
                MEMO_DATA[String(editingId)] = rec;
            } else if (data.id) {
                MEMO_DATA[String(data.id)] = rec;
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
        // 同步分类筛选下拉选项（新增分类后可能多出选项）
        var freshCatFilter = doc.getElementById("memo-cat-filter");
        var curCatFilter = document.getElementById("memo-cat-filter");
        if (freshCatFilter && curCatFilter) {
            var curVal = curCatFilter.value;
            curCatFilter.innerHTML = freshCatFilter.innerHTML;
            curCatFilter.value = curVal;  // 保持当前选中项
        }
        // 同步 MEMO_DATA 缓存（提取所有卡片的 data-id 和分类信息）
        var cards = cur.querySelectorAll(".memo-card");
        cards.forEach(function (card) {
            var cid = card.getAttribute("data-id");
            var badge = card.querySelector(".memo-cat-badge");
            var catText = badge ? badge.textContent : "";
            if (MEMO_DATA[cid]) {
                MEMO_DATA[cid].category = catText;
            }
        });
        // 兜底：操作成功后关闭可能仍打开的所有弹窗（删除 / 编辑等）
        document.querySelectorAll(".modal-mask").forEach(function (m) { m.hidden = true; });
        pendingDel = null;
        editingId = null;
        applySearch(kw);  // 保留当前搜索过滤
    }).catch(function () { toast("刷新列表失败，请手动刷新页面", true); });
}

// ===== 卡片点击编辑 / 删除（事件委托，列表局部刷新后依然有效）=====
document.addEventListener("click", function (ev) {
    // 点击卡片缩略图 = 放大查看（不触发卡片编辑）
    var thumb = ev.target.closest(".memo-thumbs img");
    if (thumb) {
        ev.stopPropagation();
        var thumbs = thumb.closest(".memo-thumbs");
        var imgs = thumbs.querySelectorAll("img");
        var urls = Array.prototype.map.call(imgs, function (i) { return i.getAttribute("src"); });
        var idx = Array.prototype.indexOf.call(imgs, thumb);
        openLightbox(urls, idx);
        return;
    }
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

var memoQ = document.getElementById("memo-q");
if (memoQ) memoQ.addEventListener("input", function () { applyAllFilters(); });

// ===== 分类筛选下拉 =====
var catFilter = document.getElementById("memo-cat-filter");
if (catFilter) catFilter.addEventListener("change", function () { applyAllFilters(); });

// ===== 合并过滤逻辑：搜索关键词 + 分类筛选 =====
function applyAllFilters() {
    var kw = (memoQ ? memoQ.value : "").trim().toLowerCase();
    var cat = catFilter ? catFilter.value : "";
    document.querySelectorAll(".memo-card").forEach(function (card) {
        var visible = true;
        // 搜索过滤
        if (kw) {
            var title = card.querySelector(".memo-title");
            var content = card.querySelector(".memo-content");
            var hit = (title && title.textContent.toLowerCase().indexOf(kw) >= 0) ||
                      (content && content.textContent.toLowerCase().indexOf(kw) >= 0);
            if (!hit) visible = false;
        }
        // 分类过滤
        if (visible && cat) {
            var badge = card.querySelector(".memo-cat-badge");
            var cardCat = badge ? badge.textContent.trim() : "";
            if (cardCat !== cat) visible = false;
        }
        card.style.display = visible ? "" : "none";
    });
}
// 保留旧的 applySearch 引用，让 refreshList 回调兼容
function applySearch(kw) { applyAllFilters(); }
