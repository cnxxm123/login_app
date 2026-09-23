/* ===== 图集/漫画阅读器逻辑（static/js/gallery.js）=====
   全部阅读交互收敛在这里，模板 gallery.html 只负责结构（数据通过
   window.GALLERY_DATA 注入，与模板解耦，便于复用与维护）。

   功能一览（参照主流漫画阅读器交互）：
   - 两种阅读模式：单页 / 长条（Webtoon 纵向滚动）
   - 四种适配方式：适合屏幕 / 适合宽度 / 适合高度 / 原始大小
   - 缩放与平移：滚轮缩放（以光标为中心）、双指捏合、双击放大/还原、
     放大后拖拽平移（鼠标/触摸）
   - 缩略图导航栏：底部横向小图（走压缩缩略图），点击任意页跳转，
     当前页高亮并自动滚到可见
   - 跳转页码弹层：输入页码直达
   - 阅读方向：左→右 / 右→左（RTL 时箭头位置、点击区域同步反转）
   - 点击翻页（可开关）：点舞台左右区域翻页，点中间唤出/收起控制条
   - 键盘快捷键：←→ PageUp/PageDown/Space 翻页，Home/End 首末页，
     + / - 缩放、0 复位、F 全屏、T 缩略图栏、Esc 关弹层；手机端用音量键翻页
   - 进度记忆：按"图集目录"记住页码（长条模式记滚动比例）与全部阅读偏好
   - 控制条闲置自动隐藏（桌面），移动/翻页唤出
*/
(function () {
    "use strict";

    /* ================= 数据与 DOM ================= */
    var D = window.GALLERY_DATA || {};
    var imgs = D.imageUrls || [];      // 全部原图地址
    var imagePaths = D.imagePaths || [];
    var thumbs = D.thumbUrls || [];    // 全部压缩缩略图地址
    var itemPath = D.itemPath || "";   // 图集自身路径（收藏和进度的稳定标识）
    var total = imgs.length;

    var stage = document.getElementById("gl-stage");
    var zoom = document.getElementById("gl-zoom");
    var imgCur = document.getElementById("gl-img-cur");
    var strip = document.getElementById("gl-strip");
    var posEl = document.getElementById("gl-pos");
    var loadingEl = document.getElementById("gl-loading");
    var thumbsTrack = document.getElementById("gl-thumbs-track");
    var thumbsBar = document.getElementById("gl-thumbs");
    var settingsMask = document.getElementById("gl-settings");
    var jumpMask = document.getElementById("gl-jump");
    var jumpInput = document.getElementById("gl-jump-input");
    var setClick = document.getElementById("set-click");
    var setThumbs = document.getElementById("set-thumbs");
    var setAuto = document.getElementById("set-auto");
    var autoIntervalEl = document.getElementById("auto-interval");
    var progressBar = document.getElementById("gl-progress");
    var progressFill = document.getElementById("gl-progress-fill");
    var navPrev = document.getElementById("nav-prev");
    var navNext = document.getElementById("nav-next");

    /* ================= 偏好记忆（localStorage） ================= */
    function loadPref(key, def) {
        try {
            var v = localStorage.getItem(key);
            return v === null ? def : JSON.parse(v);
        } catch (e) { return def; }
    }
    function savePref(key, val) {
        try { localStorage.setItem(key, JSON.stringify(val)); } catch (e) {}
    }

    // 触屏设备（无悬停）默认收起缩略图栏，避免遮挡画面
    var isCoarse = window.matchMedia && window.matchMedia("(pointer: coarse)").matches;

    // 兼容旧版本：localStorage 里可能存过已删除的双页模式 "double"，一律回退到单页
    var savedMode = loadPref("gallery_mode", "single");
    if (savedMode !== "strip") savedMode = "single";

    var S = {
        mode: savedMode,   // 阅读模式 single/strip
        fit: loadPref("gallery_fit", "screen"),     // 适配 screen/width/height/original
        dir: loadPref("gallery_dir", "ltr"),        // 阅读方向 ltr/rtl
        clickNav: loadPref("gallery_click", true),  // 点击区域翻页开关
        thumbsOn: loadPref("gallery_thumbs", !isCoarse),
        autoplay: loadPref("gallery_auto", false),        // 自动翻页开关
        autoInterval: loadPref("gallery_auto_interval", 4),  // 自动翻页间隔（秒）
        cur: 0,        // 当前页（单页=当前图；长条=参考图）
        zoom: 1,       // 用户缩放倍率（1 = 适配基准）
        base: 1,       // 适配基准比例（由 fit 模式计算）
        tx: 0, ty: 0,  // 平移偏移（相对舞台左上角）
        nw: 0, nh: 0,  // 当前单张图的自然尺寸
        contentW: 0, contentH: 0,  // 内容自然尺寸
        loading: false,
        failed: false,   // 当前图请求失败（显示重试提示）
        _stripRatio: null   // 长条模式恢复用的滚动比例
    };

    // 最近一次 error 事件对应的图片 URL，用于区分"加载失败"与"还在加载中的自然尺寸为 0"
    var failUrl = null;

    /* ================= 页码与进度记忆 ================= */
    function pageLabel() {
        return (S.cur + 1) + " / " + total;
    }

    var posKey = "gallery_pos_" + itemPath;
    var syncTimer = null;
    function progressPayload() {
        return {
            path: itemPath,
            kind: "page",
            position: S.cur + 1,
            total: total,
            locator: imagePaths[S.cur] || null,
            completed: S.cur >= total - 1
        };
    }
    function syncGlobalProgress() {
        if (!window.Personal || !itemPath || !total) return;
        window.clearTimeout(syncTimer);
        syncTimer = window.setTimeout(function () {
            window.Personal.reportProgress(progressPayload());
        }, 600);
    }
    window.addEventListener("pagehide", function () {
        window.clearTimeout(syncTimer);
        if (window.Personal && itemPath && total) {
            window.Personal.reportProgress(progressPayload(), true);
        }
    });
    function savePos() {
        if (!total) return;
        var val = { mode: S.mode };
        if (S.mode === "strip") {
            var range = strip.scrollHeight - strip.clientHeight;
            val.ratio = range > 0 ? strip.scrollTop / range : 0;
        } else {
            val.index = S.cur;
        }
        savePref(posKey, val);
        syncGlobalProgress();
    }
    function restorePos() {
        var server = D.initialProgress;
        if (server && server.kind === "page") {
            var serverIndex = server.locator ? imagePaths.indexOf(server.locator) : Math.round(Number(server.position || 1)) - 1;
            if (serverIndex >= 0 && serverIndex < total) {
                S.cur = serverIndex;
                return;
            }
        }
        var saved = loadPref(posKey, null);
        if (!saved) return;
        if (saved.mode === S.mode && S.mode === "strip" && typeof saved.ratio === "number") {
            S._stripRatio = saved.ratio;
        } else if (typeof saved.index === "number" && saved.index >= 0 && saved.index < total) {
            S.cur = saved.index;
        }
    }

    /* ================= 缩略图栏 ================= */
    function markThumb() {
        var act = thumbsTrack.querySelector(".gl-thumb.active");
        if (act) act.classList.remove("active");
        var curEl = thumbsTrack.querySelector('.gl-thumb[data-i="' + S.cur + '"]');
        if (curEl) {
            curEl.classList.add("active");
            curEl.scrollIntoView({ block: "nearest", inline: "nearest" });
        }
    }

    /* ================= 更新页码/边界/缩略图/进度条 ================= */
    function updateProgress() {
        if (!total) { progressFill.style.width = "0%"; return; }
        var done = S.cur + 1;  // 进度 = 已读到的当前页
        progressFill.style.width = ((done / total) * 100).toFixed(2) + "%";
    }
    function updatePos() {
        if (!total) { posEl.textContent = "0 / 0"; return; }
        posEl.textContent = pageLabel();
        navPrev.disabled = S.cur <= 0;
        navNext.disabled = S.cur >= total - 1;
        markThumb();
        updateProgress();
        savePos();
    }

    /* ================= 舞台布局 =================
       图片以"自然尺寸"放进 .gl-zoom，缩放/平移全走 zoom 的 transform：
       translate(tx,ty) scale(base*zoom)，原点 0 0。 */
    function layoutStage() {
        var nw = S.nw || 1, nh = S.nh || 1;
        var W = stage.clientWidth, H = stage.clientHeight;
        var cw = nw, ch = nh;  // 单页：内容宽高 = 图片自然尺寸
        S.contentW = cw; S.contentH = ch;

        zoom.style.width = cw + "px";
        zoom.style.height = ch + "px";
        imgCur.style.width = nw + "px";
        imgCur.style.height = nh + "px";

        // 按适配方式计算基准比例（留 16px 边距）
        var pad = 16, b;
        switch (S.fit) {
            case "width":   b = (W - pad) / cw; break;
            case "height":  b = (H - pad) / ch; break;
            case "original": b = 1; break;
            default:        b = Math.min((W - pad) / cw, (H - pad) / ch); break; // screen
        }
        S.base = Math.max(0.05, Math.min(4, b));
        S.zoom = 1; S.tx = 0; S.ty = 0;
        applyTransform();
    }

    function applyTransform() {
        if (S.mode === "strip" || !S.contentW) return;
        var s = S.base * S.zoom;
        var W = stage.clientWidth, H = stage.clientHeight;
        var cw = S.contentW * s, ch = S.contentH * s;
        var tx, ty;
        // 内容比舞台大 → 允许在该轴平移（限制边界）；否则居中
        if (cw >= W) { tx = Math.max(W - cw, Math.min(0, S.tx)); }
        else { tx = (W - cw) / 2; }
        if (ch >= H) { ty = Math.max(H - ch, Math.min(0, S.ty)); }
        else { ty = (H - ch) / 2; }
        S.tx = tx; S.ty = ty;
        zoom.style.transform = "translate(" + tx + "px, " + ty + "px) scale(" + s + ")";
    }

    /* ================= 缩放 ================= */
    // factor>1 放大；以舞台内 (px,py) 为缩放中心，保持该点下内容不动
    function zoomAt(factor, px, py) {
        if (S.mode === "strip") return;
        var oldS = S.base * S.zoom;
        var next = Math.max(0.2, Math.min(8, S.zoom * factor));
        if (next === S.zoom) return;
        S.zoom = next;
        var newS = S.base * S.zoom;
        S.tx = px - (px - S.tx) * (newS / oldS);
        S.ty = py - (py - S.ty) * (newS / oldS);
        applyTransform();
    }
    function resetView() {
        if (S.mode === "strip") return;
        S.zoom = 1; S.tx = 0; S.ty = 0;
        applyTransform();
    }

    /* ================= 换页与加载 ================= */
    function preloadNext() {
        if (S.mode === "strip") return;
        var n = S.cur + 1;
        if (n < total) { var im = new Image(); im.src = imgs[n]; }
    }

    function show(i) {
        if (!total) return;
        S.cur = Math.max(0, Math.min(total - 1, i));
        if (S.mode === "strip") { updatePos(); return; }
        imgCur.src = imgs[S.cur];
        loadingEl.hidden = false;
        loadingEl.textContent = "加载中…";
        S.loading = true;
        S.failed = false;
        updatePos();
        // 翻页过渡动画：移除 class 强制重排后再加，确保每次换图都重新淡入
        imgCur.classList.remove("gl-flip");
        void imgCur.offsetWidth;
        imgCur.classList.add("gl-flip");
        preloadNext();
        // 同 URL 已加载完成时不会再触发 load/error 事件（如点当前页缩略图、
        // 从长条切回原页），此时手动走一遍"加载完成"收尾，避免提示永远卡住
        if (imgCur.complete) {
            onStageLoaded();
        }
    }

    function imgOk(im) { return !im.src || im.complete; }

    function onStageLoaded() {
        if (!S.loading) return;
        if (!imgOk(imgCur)) return;  // 等当前图加载完
        S.loading = false;
        // 当前图确实加载失败（发生过 error 且拿不到尺寸）：
        // 保留原布局并提示可重试，避免渲染成"黑块"式空白
        if (imgCur.getAttribute("src") === failUrl && imgCur.naturalWidth === 0) {
            S.failed = true;
            loadingEl.textContent = "图片加载失败 · 点此重试";
            loadingEl.hidden = false;
            return;
        }
        S.failed = false;
        loadingEl.hidden = true;
        loadingEl.textContent = "加载中…";
        S.nw = imgCur.naturalWidth || stage.clientWidth;
        S.nh = imgCur.naturalHeight || stage.clientHeight;
        layoutStage();
    }
    imgCur.addEventListener("error", function () {
        // 记录本次失败对应的 URL（旧请求被替换时也可能报 error，用 URL 对账避免误判）
        failUrl = imgCur.getAttribute("src");
    });
    imgCur.addEventListener("load", onStageLoaded);
    imgCur.addEventListener("error", onStageLoaded);

    // 加载失败时点击提示可重试：清空 src 强制重新请求当前图
    loadingEl.addEventListener("click", function () {
        if (!total || S.mode === "strip") return;
        imgCur.removeAttribute("src");
        failUrl = null;
        show(S.cur);
    });

    /* ================= 翻页 ================= */
    var autoTimer = null;  // 自动翻页定时器

    // 启动自动翻页：按间隔逐页翻；到达末页自动停止。
    // 长条模式不适用（滚动阅读），切到长条时暂停。
    function startAuto() {
        stopAuto();
        if (!S.autoplay || S.mode === "strip") return;
        autoTimer = setInterval(function () {
            if (S.mode === "strip") return;
            var last = total - 1;
            if (S.cur >= last) {
                S.autoplay = false;
                savePref("gallery_auto", false);
                renderPrefs();
                stopAuto();
                return;
            }
            go(1);
        }, Math.max(1, S.autoInterval) * 1000);
    }
    function stopAuto() {
        if (autoTimer) { clearInterval(autoTimer); autoTimer = null; }
    }
    // 手动翻页/跳页后重置计时，避免刚翻完又立刻翻下一页
    function resetAuto() { if (S.autoplay) startAuto(); }

    function toggleAuto() {
        S.autoplay = !S.autoplay;
        savePref("gallery_auto", S.autoplay);
        if (S.autoplay) startAuto(); else stopAuto();
        renderPrefs();
        showUI();
    }
    // 调整自动翻页间隔（秒），±1，范围 1~30
    function autoStep(d) {
        S.autoInterval = Math.max(1, Math.min(30, S.autoInterval + d));
        savePref("gallery_auto_interval", S.autoInterval);
        if (autoIntervalEl) autoIntervalEl.textContent = S.autoInterval + "s";
        resetAuto();
        showUI();
    }

    function go(d) {
        if (!total) return;
        if (S.mode === "strip") {
            S.cur = Math.max(0, Math.min(total - 1, S.cur + d));
            scrollToCurrent();
            updatePos();
        } else {
            show(S.cur + d);  // 单页一次翻一张
        }
        resetAuto();
        // 注意：不调用 showUI() —— 翻页（滑动/点击边缘）不应弹出控制条，
        // 控制条只由"点击屏幕中间区域"切换显隐
    }
    function goTo(i) {
        if (!total) return;
        if (S.mode === "strip") {
            S.cur = Math.max(0, Math.min(total - 1, i));
            scrollToCurrent();
            updatePos();
        } else {
            show(i);
        }
        resetAuto();
        // 同上：跳页不弹出控制条（跳页弹窗/进度条点击处会主动 showUI）
    }

    /* ================= 长条模式 ================= */
    function scrollToCurrent() {
        var items = strip.querySelectorAll(".gl-strip-img");
        if (items[S.cur]) items[S.cur].scrollIntoView({ block: "start" });
    }
    // 滚动时同步记忆滚动比例（供下次进入长条模式续读）+ 顶部进度条
    strip.addEventListener("scroll", function () {
        if (!total) return;
        // 长条模式进度 = 滚动位置 / 可滚动范围
        var range = strip.scrollHeight - strip.clientHeight;
        var ratio = range > 0 ? strip.scrollTop / range : 0;
        progressFill.style.width = (ratio * 100).toFixed(2) + "%";
        savePos();
    }, { passive: true });
    // 长条模式：滚动是原生纵向滚动，横滑/点击翻页都不可用；
    // 仅点击屏幕中间区域（横向 40%~60%）切换控制条显隐，与单页模式一致
    strip.addEventListener("click", function (e) {
        if (e.target.closest(".gl-bar, .gl-thumbs, .gl-modal-mask")) return;
        var rect = strip.getBoundingClientRect();
        var x = rect.width > 0 ? (e.clientX - rect.left) / rect.width : 0.5;
        if (x < 0.4 || x > 0.6) return;
        toggleUI();
    });
    // 长条模式：单张原图加载失败时退回压缩缩略图，避免整块空白
    //（error 事件不冒泡，需用捕获阶段做事件委托）
    strip.addEventListener("error", function (e) {
        var im = e.target;
        if (!(im instanceof HTMLImageElement) || im.getAttribute("data-i") === null) return;
        var ti = parseInt(im.getAttribute("data-i"), 10);
        if (isNaN(ti) || !thumbs[ti]) return;
        if (im.getAttribute("src") !== thumbs[ti]) im.src = thumbs[ti];
    }, true);
    // 参考带监听：哪张图进入视野中央就把页码跟到哪张
    if (total > 1) {
        var stripImgs = Array.prototype.slice.call(strip.querySelectorAll(".gl-strip-img"));
        var obs = new IntersectionObserver(function (entries) {
            entries.forEach(function (en) {
                if (en.isIntersecting) {
                    var idx = stripImgs.indexOf(en.target);
                    if (idx >= 0 && idx !== S.cur) { S.cur = idx; updatePos(); }
                }
            });
        }, { root: null, rootMargin: "-15% 0px -55% 0px", threshold: 0 });
        stripImgs.forEach(function (im) { obs.observe(im); });
    }

    /* ================= 模式 / 适配 / 方向切换 ================= */
    function setMode(m) {
        if (m === S.mode) return;
        S.mode = m;
        savePref("gallery_mode", m);
        if (m === "strip") {
            stage.hidden = true;
            strip.hidden = false;
            S.loading = false;
            S.failed = false;
            loadingEl.hidden = true;
            scrollToCurrent();
            updatePos();
        } else {
            strip.hidden = true;
            stage.hidden = false;
            show(S.cur);   // 用当前页码进入单页
        }
        // 长条模式暂停自动翻页，回到单页自动恢复
        if (m === "strip") stopAuto();
        else if (S.autoplay) startAuto();
        renderPrefs();
        showUI();
    }
    function setFit(f) {
        S.fit = f;
        savePref("gallery_fit", f);
        if (S.mode !== "strip") layoutStage();  // 重新计算基准并复位视图
        renderPrefs();
    }
    function setDir(d) {
        S.dir = d;
        savePref("gallery_dir", d);
        renderPrefs();   // 更新箭头位置 / 点击区域
        if (S.mode !== "strip") applyTransform();
    }

    /* ================= 点击区域翻页 + 双击缩放 =================
       单击延迟 280ms 执行，以区分双击（双击第二击不翻页）。 */
    var clickTimer = null, lastClickT = 0, lastX = 0, lastY = 0;

    function doClickAction(e) {
        if (S.mode === "strip") return;
        if (Date.now() - swipedT < 500) return;   // 刚滑动/捏合过：忽略残留 click，避免误翻页
        if (e.target.closest(".gl-nav, .gl-bar, .gl-thumbs, .gl-modal-mask")) return;
        var rect = stage.getBoundingClientRect();
        var x = e.clientX - rect.left;
        var W = stage.clientWidth;
        var action = null;
        if (x < W * 0.4) action = S.dir === "ltr" ? -1 : 1;        // 左区：LTR=上一页
        else if (x > W * 0.6) action = S.dir === "ltr" ? 1 : -1;   // 右区：LTR=下一页
        if (S.clickNav && action) go(action);
        else toggleUI();  // 中间区域或点击翻页关闭时：切换控制条显隐
    }

    stage.addEventListener("click", function (e) {
        if (S.mode === "strip") return;
        if (e.target.closest(".gl-nav, .gl-bar, .gl-thumbs, .gl-modal-mask")) return;
        var now = Date.now();
        var isDbl = (now - lastClickT < 300) &&
            Math.abs(e.clientX - lastX) < 30 && Math.abs(e.clientY - lastY) < 30;
        lastClickT = now; lastX = e.clientX; lastY = e.clientY;
        if (clickTimer) { clearTimeout(clickTimer); clickTimer = null; }
        if (isDbl) {
            // 双击：放大到 2 倍（以点击点为中心），已放大则还原
            if (S.zoom > 1.01) resetView();
            else zoomAt(2, e.clientX, e.clientY);
            showUI();
            return;
        }
        clickTimer = setTimeout(function () { clickTimer = null; doClickAction(e); }, 280);
    });

    /* ================= 触摸 / 拖拽手势（pointer events 统一处理） =================
       - 单指：未缩放时水平滑动翻页；缩放后拖动平移
       - 双指：捏合缩放（以两指中点为中心） */
    var pointers = {};
    var panState = null;
    var swipedT = 0;   // 最近一次滑动/捏合的时刻，用于抑制手势结束后残留的 click

    stage.addEventListener("pointerdown", function (e) {
        if (S.mode === "strip") return;
        if (e.target.closest(".gl-nav, .gl-bar, .gl-thumbs")) return;
        pointers[e.pointerId] = { x: e.clientX, y: e.clientY };
        if (Object.keys(pointers).length === 1) {
            panState = { x: e.clientX, y: e.clientY, tx: S.tx, ty: S.ty, moved: false, flipped: false };
        }
    });

    stage.addEventListener("pointermove", function (e) {
        if (S.mode === "strip") return;
        if (!(e.pointerId in pointers)) return;
        var p = pointers[e.pointerId];
        var dx = e.clientX - p.x, dy = e.clientY - p.y;
        p.x = e.clientX; p.y = e.clientY;
        var ids = Object.keys(pointers);

        if (ids.length === 1 && panState) {
            var totalDx = e.clientX - panState.x;
            var totalDy = e.clientY - panState.y;
            if (Math.hypot(totalDx, totalDy) > 8) panState.moved = true;
            if (!panState.moved) return;
            if (S.zoom > 1.001) {
                // 已缩放：拖拽平移（以按下时的起点为基准）
                S.tx = panState.tx + totalDx;
                S.ty = panState.ty + totalDy;
                applyTransform();
            } else if (Math.abs(totalDx) > 60 && Math.abs(totalDx) > Math.abs(totalDy) * 1.5 && !panState.flipped) {
                // 未缩放：水平滑动翻页（左滑=下一页，RTL 反转）
                swipedT = Date.now();   // 抑制松手后残留的 click（否则会把刚翻的页翻回去）
                var d = totalDx < 0 ? 1 : -1;
                if (S.dir === "rtl") d = -d;
                go(d);
                panState.flipped = true;   // 一次手势只翻一页：totalDx 基于按下起点算，不重置的话每次 move 都会再翻
            }
        } else if (ids.length === 2) {
            // 双指捏合缩放
            swipedT = Date.now();   // 捏合手势产生的残留 click 一并抑制
            var p0 = pointers[ids[0]], p1 = pointers[ids[1]];
            var dist = Math.hypot(p0.x - p1.x, p0.y - p1.y);
            if (panState && panState.pinch && panState.pinch > 0) {
                var midX = (p0.x + p1.x) / 2, midY = (p0.y + p1.y) / 2;
                zoomAt(dist / panState.pinch, midX, midY);
            }
            panState.pinch = dist;
            panState.moved = true;
        }
    });

    function endPointer(e) {
        delete pointers[e.pointerId];
        var ids = Object.keys(pointers);
        if (ids.length === 1) {
            // 从双指变单指：重置平移基准为当前状态
            var p = pointers[ids[0]];
            panState = { x: p.x, y: p.y, tx: S.tx, ty: S.ty, moved: true, flipped: false };
        } else if (ids.length === 0) {
            panState = null;
        }
    }
    stage.addEventListener("pointerup", endPointer);
    stage.addEventListener("pointercancel", endPointer);
    stage.addEventListener("pointerleave", endPointer);

    // 滚轮缩放（长条模式由容器原生滚动，不拦截）
    stage.addEventListener("wheel", function (e) {
        if (S.mode === "strip") return;
        e.preventDefault();   // 阻止浏览器"Ctrl+滚轮缩放页面"
        var factor = e.deltaY < 0 ? 1.12 : 1 / 1.12;
        zoomAt(factor, e.clientX, e.clientY);
    }, { passive: false });

    /* ================= 控制条显隐 =================
       控制条只由"点击屏幕中间区域"切换（doClickAction / strip 点击监听）；
       不再监听全局 pointermove，否则滑动翻页/长条滚动时控制条会被弹出来。 */
    var uiTimer = null;
    function showUI() {
        document.body.classList.remove("gl-ui-hidden");
        clearTimeout(uiTimer);
        if (window.matchMedia("(hover: hover)").matches) {
            uiTimer = setTimeout(function () { document.body.classList.add("gl-ui-hidden"); }, 2800);
        }
    }

    function toggleUI() {
        if (document.body.classList.contains("gl-ui-hidden")) { showUI(); }
        else {
            document.body.classList.add("gl-ui-hidden");
            clearTimeout(uiTimer);
        }
    }

    /* ================= 偏好开关与渲染 ================= */
    function toggleClick() {
        S.clickNav = !S.clickNav;
        savePref("gallery_click", S.clickNav);
        renderPrefs();
    }
    function toggleThumbs() {
        S.thumbsOn = !S.thumbsOn;
        savePref("gallery_thumbs", S.thumbsOn);
        renderPrefs();
        showUI();
    }

    // 把所有 [data-set] 分段按钮、开关按钮同步为当前状态
    function renderPrefs() {
        document.querySelectorAll("[data-set]").forEach(function (btn) {
            var key = btn.getAttribute("data-set");
            btn.classList.toggle("active", btn.getAttribute("data-val") === String(S[key]));
        });
        setClick.classList.toggle("on", S.clickNav);
        setClick.textContent = S.clickNav ? "开" : "关";
        setThumbs.classList.toggle("on", S.thumbsOn);
        setThumbs.textContent = S.thumbsOn ? "开" : "关";
        if (setAuto) {
            setAuto.classList.toggle("on", S.autoplay);
            setAuto.textContent = S.autoplay ? "开" : "关";
        }
        if (autoIntervalEl) autoIntervalEl.textContent = S.autoInterval + "s";
        document.body.classList.toggle("gl-rtl", S.dir === "rtl");
        thumbsBar.style.display = S.thumbsOn ? "" : "none";
    }

    /* ================= 弹层：设置 / 跳页 ================= */
    function openJump() {
        jumpInput.value = S.cur + 1;
        jumpMask.hidden = false;
        jumpInput.focus();
        jumpInput.select();
    }
    function doJump() {
        var v = parseInt(jumpInput.value, 10);
        if (!isNaN(v)) goTo(Math.max(1, Math.min(total, v)) - 1);
        jumpMask.hidden = true;
        showUI();
    }
    function closeModals() {
        settingsMask.hidden = true;
        jumpMask.hidden = true;
        showUI();
    }
    jumpInput.addEventListener("keydown", function (e) {
        if (e.key === "Enter") doJump();
    });

    /* ================= 顶部进度条：点击按比例跳页（长条模式不适用） ================= */
    progressBar.addEventListener("click", function (e) {
        if (!total || S.mode === "strip") return;
        var rect = progressBar.getBoundingClientRect();
        if (rect.width <= 0) return;
        var ratio = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
        goTo(Math.round(ratio * (total - 1)));
        showUI();
    });

    /* ================= 事件委托（document 级，动态元素也可靠） =================
       模板里的按钮统一用 data-act / data-set / data-i 声明，不用内联 onclick
       （历史经验：内联 onclick + 引号嵌套易出 JS 语法错误）。 */
    document.addEventListener("click", function (e) {
        var actEl = e.target.closest("[data-act]");
        if (actEl) {
            switch (actEl.getAttribute("data-act")) {
                case "prev": go(-1); break;
                case "next": go(1); break;
                case "jump": openJump(); break;
                case "settings": settingsMask.hidden = false; showUI(); break;
                case "fullscreen": toggleFullscreen(); break;
                case "close-settings": settingsMask.hidden = true; break;
                case "close-jump": jumpMask.hidden = true; break;
                case "go-jump": doJump(); break;
                case "toggle-click": toggleClick(); break;
                case "toggle-thumbs": toggleThumbs(); break;
                case "toggle-auto": toggleAuto(); break;
                case "auto-slower": autoStep(1); break;
                case "auto-faster": autoStep(-1); break;
            }
            return;
        }
        var setEl = e.target.closest("[data-set]");
        if (setEl) {
            var key = setEl.getAttribute("data-set");
            var val = setEl.getAttribute("data-val");
            if (key === "mode") setMode(val);
            else if (key === "fit") setFit(val);
            else if (key === "dir") setDir(val);
            return;
        }
        var thumbEl = e.target.closest(".gl-thumb");
        if (thumbEl) {
            var i = parseInt(thumbEl.getAttribute("data-i"), 10);
            if (!isNaN(i)) goTo(i);
            return;
        }
        if (e.target.classList.contains("gl-modal-mask")) closeModals();  // 点遮罩空白关闭
    });

    /* ================= 键盘快捷键 =================
       手机端实体音量键在部分浏览器（如 Android）会转成 keydown 事件，
       利用它翻页；仅触屏设备生效，避免影响桌面端媒体音量键。 */
    document.addEventListener("keydown", function (e) {
        var tag = (e.target.tagName || "").toLowerCase();
        if (tag === "input" || tag === "textarea") return;
        switch (e.key) {
            case "ArrowLeft": go(-1); e.preventDefault(); break;
            case "ArrowRight": go(1); e.preventDefault(); break;
            case "PageUp": go(-1); e.preventDefault(); break;
            case "PageDown": case " ": go(1); e.preventDefault(); break;
            case "Home": goTo(0); e.preventDefault(); break;
            case "End": goTo(total - 1); e.preventDefault(); break;
            case "+": case "=": zoomAt(1.25, stage.clientWidth / 2, stage.clientHeight / 2); e.preventDefault(); break;
            case "-": case "_": zoomAt(0.8, stage.clientWidth / 2, stage.clientHeight / 2); e.preventDefault(); break;
            case "0": resetView(); e.preventDefault(); break;
            case "f": case "F": toggleFullscreen(); e.preventDefault(); break;
            case "t": case "T": toggleThumbs(); e.preventDefault(); break;
            // 手机端音量键翻页（AudioVolumeUp/Down 是部分旧版浏览器的事件键名）
            case "VolumeUp": case "AudioVolumeUp": if (isCoarse) { go(-1); e.preventDefault(); } break;
            case "VolumeDown": case "AudioVolumeDown": if (isCoarse) { go(1); e.preventDefault(); } break;
            case "Escape": closeModals(); break;
        }
    });

    /* ================= 浏览器原生全屏 ================= */
    function toggleFullscreen() {
        if (!document.fullscreenElement && !document.webkitFullscreenElement) {
            var req = document.documentElement.requestFullscreen || document.documentElement.webkitRequestFullscreen;
            if (req) req.call(document.documentElement);
        } else {
            var exit = document.exitFullscreen || document.webkitExitFullscreen;
            if (exit) exit.call(document);
        }
    }

    /* ================= 窗口尺寸变化：重新适配 ================= */
    window.addEventListener("resize", function () {
        if (S.mode === "strip" || !S.contentW) return;
        layoutStage();
    });

    /* ================= 初始化 ================= */
    if (!total) {
        posEl.textContent = "0 / 0";   // 空图集防御（正常不会进入此页）
        return;
    }
    renderPrefs();
    restorePos();
    if (S.mode === "strip") {
        stage.hidden = true;
        strip.hidden = false;
        // 等图片布局后应用滚动比例（长条续读）或定位到当前页
        requestAnimationFrame(function () {
            if (S._stripRatio != null && strip.scrollHeight > strip.clientHeight) {
                strip.scrollTop = S._stripRatio * (strip.scrollHeight - strip.clientHeight);
                S._stripRatio = null;
            } else {
                scrollToCurrent();
            }
            updatePos();
        });
    } else {
        show(S.cur);
    }
    // 用户上次开着自动翻页：进入时恢复（长条模式由 startAuto 内部拦截）
    if (S.autoplay) startAuto();
})();
