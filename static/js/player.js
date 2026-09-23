/* ===== 自定义网页视频播放器（static/js/player.js）=====
   仿主流网页播放器（DPlayer / ArtPlayer / B 站）的自定义播放器逻辑。

   功能清单：
   - 底部控制栏：播放/暂停、音量（悬停展开滑块 + 静音）、时间、进度条
     （已播 + 缓冲 + 点击/拖拽跳转 + 悬停时间气泡）、倍速菜单、画中画、
     宽屏 / 网页全屏 / 全屏（B 站式三种尺寸模式）
   - 中央大播放键、加载转圈、错误"重试"
   - 与 view.html 连播逻辑联动：控制栏里的 上一集/下一集 按钮
   - 交互：点击视频播放/暂停、双击全屏、空闲 3 秒自动隐藏控制栏
   - 快捷键：空格/K 播放暂停、←→ 快退/快进 5 秒、↑↓ 音量、
     M 静音、F 全屏、P 画中画、ESC 退出网页全屏、数字 0-9 跳转到 10%-90%、
     >/. 与 </, 加速/减速
   - 记忆：音量、静音、倍速、宽屏偏好存 localStorage

   用法：在 view.html 的 </body> 前引入本文件即可（仅存在 #vp-player 时生效）：
   <script src="{{ url_for('static', filename='js/player.js') }}"></script>
   播放器骨架（模板只写这个）：
   <div class="vp" id="vp-player">
       <video id="media-player" class="vp-video" playsinline preload="metadata" src="..."></video>
   </div>
*/
(function () {
    var playerEl = document.getElementById("vp-player");
    var video = playerEl && playerEl.querySelector(".vp-video");
    if (!playerEl || !video) return;   // 非视频页（没有该结构）直接跳过
    video.controls = false;            // 双保险：关掉浏览器原生控制栏，用自定义的

    /* ---------- 1. 图标库：全部用内联 SVG（白色随按钮 color 变化）---------- */
    var ICONS = {
        play: '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M8 5.14v13.72a1 1 0 0 0 1.5.86l11-6.86a1 1 0 0 0 0-1.72l-11-6.86a1 1 0 0 0-1.5.86z"/></svg>',
        pause: '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><rect x="6" y="5" width="4" height="14" rx="1"/><rect x="14" y="5" width="4" height="14" rx="1"/></svg>',
        volume: '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M3 9v6h4l5 4V5L7 9H3z"/><path d="M16 8.5a5 5 0 0 1 0 7" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
        muted: '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M3 9v6h4l5 4V5L7 9H3z"/><path d="M17 9l4 6M21 9l-4 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
        prev: '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M6 5h2v14H6zM20 5v14l-10-7z"/></svg>',
        next: '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M16 5h2v14h-2zM4 5v14l10-7z"/></svg>',
        speed: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 4a9 9 0 1 0 9 9"/><path d="M12 8v5l3 2"/></svg>',
        wide: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="6" width="18" height="12" rx="2"/><path d="M8 3v2.5M16 3v2.5M8 18.5V21M16 18.5V21"/></svg>',
        webfull: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="M2 9h20"/><path d="M6.5 6.5v.5M9.5 6.5v.5"/></svg>',
        pip: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2"/><rect x="10" y="10" width="8" height="5" rx="1" fill="currentColor" stroke="none"/></svg>',
        full: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"/></svg>',
        compress: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M8 3v3a2 2 0 0 1-2 2H3m18 0h-3a2 2 0 0 1-2-2V3m0 18v-3a2 2 0 0 1 2-2h3M3 16h3a2 2 0 0 1 2 2v3"/></svg>',
        retry: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12a9 9 0 1 1-2.64-6.36M21 3v6h-6"/></svg>'
    };

    /* ---------- 2. DOM 辅助：建元素 / 建按钮 ---------- */
    function el(tag, cls, html) {
        var e = document.createElement(tag);
        if (cls) e.className = cls;
        if (html !== undefined) e.innerHTML = html;
        return e;
    }
    function iconBtn(id, cls, title, icon) {
        var b = el("button", "vp-btn" + (cls ? " " + cls : ""), ICONS[icon]);
        b.type = "button"; b.id = id; b.title = title; b.setAttribute("aria-label", title);
        return b;
    }

    /* ---------- 3. 构建控制栏 DOM（一次性注入到播放器容器）---------- */
    var controls = el("div", "vp-controls");

    // 进度条：轨道上叠 缓冲层 + 已播层 + 圆点，另有一个悬停时间气泡
    var progress = el("div", "vp-progress");
    progress.id = "vp-progress";
    progress.appendChild(el("div", "vp-progress-buffer"));
    progress.appendChild(el("div", "vp-progress-played"));
    progress.appendChild(el("div", "vp-progress-thumb"));
    var hoverTime = el("div", "vp-hover-time", "00:00");
    hoverTime.hidden = true;
    progress.appendChild(hoverTime);

    // 按钮行：左侧 播放/音量/时间；右侧 上一集/下一集/倍速/列表/画中画/全屏
    var bottom = el("div", "vp-bottom");
    var left = el("div", "vp-left");
    var right = el("div", "vp-right");

    var btnPlay = iconBtn("vp-play", null, "播放/暂停（空格）", "play");
    var volWrap = el("div", "vp-vol");
    var btnMute = iconBtn("vp-mute", null, "静音（M）", "volume");
    var volSlider = el("input", "vp-vol-slider");
    volSlider.type = "range"; volSlider.min = "0"; volSlider.max = "1"; volSlider.step = "0.05";
    volSlider.value = "1"; volSlider.setAttribute("aria-label", "音量");
    volWrap.appendChild(btnMute); volWrap.appendChild(volSlider);

    var timeLabel = el("span", "vp-time", "00:00 / 00:00");
    timeLabel.id = "vp-time";

    left.appendChild(btnPlay); left.appendChild(volWrap); left.appendChild(timeLabel);

    var btnPrev = iconBtn("vp-prev", null, "上一集", "prev");
    var btnNext = iconBtn("vp-next", null, "下一集", "next");
    var btnSpeed = iconBtn("vp-speed", null, "播放速度", "speed");
    var btnWide = iconBtn("vp-wide", null, "宽屏", "wide");
    var btnWebFull = iconBtn("vp-webfull", null, "网页全屏", "webfull");
    var btnPip = iconBtn("vp-pip", null, "画中画（P）", "pip");
    var btnFull = iconBtn("vp-full", null, "全屏（F）", "full");
    right.appendChild(btnPrev); right.appendChild(btnNext); right.appendChild(btnSpeed);
    right.appendChild(btnWide); right.appendChild(btnWebFull); right.appendChild(btnPip); right.appendChild(btnFull);

    bottom.appendChild(left);
    bottom.appendChild(el("div", "vp-spacer"));
    bottom.appendChild(right);

    controls.appendChild(progress);
    controls.appendChild(bottom);

    // 倍速设置菜单
    var settings = el("div", "vp-settings");
    settings.hidden = true;
    settings.appendChild(el("div", "vp-settings-title", "播放速度"));
    var RATES = [0.5, 0.75, 1, 1.25, 1.5, 2];
    var rateBtns = {};
    RATES.forEach(function (r) {
        var b = el("button", null, r + "x");
        b.type = "button"; b.dataset.rate = r;
        b.addEventListener("click", function () { setRate(r); hideSettings(); });
        rateBtns[r] = b;
        settings.appendChild(b);
    });

    // 中央大播放键 + 加载转圈 + 错误层
    var center = el("div", "vp-center");
    center.hidden = true;
    var centerPlay = el("button", "vp-center-play", ICONS.play);
    centerPlay.type = "button";
    centerPlay.addEventListener("click", function (e) { e.stopPropagation(); togglePlay(); });
    center.appendChild(centerPlay);

    var spinner = el("div", "vp-spinner");
    spinner.hidden = true;

    var errorLayer = el("div", "vp-error", '<span>视频加载失败</span>');
    errorLayer.hidden = true;
    var retryBtn = el("button", "vp-retry", ICONS.retry + "重试");
    retryBtn.type = "button";
    retryBtn.addEventListener("click", function () {
        errorLayer.hidden = true;
        video.load();            // 重新加载当前 src
        video.play().catch(function () {});
    });
    errorLayer.appendChild(retryBtn);

    // 续播提示层：再次进入时若上次看到一半，询问"继续播放 / 从头播放"
    var resumeLayer = el("div", "vp-resume");
    resumeLayer.hidden = true;
    var resumeBox = el("div", "vp-resume-box");
    resumeBox.appendChild(el("div", "vp-resume-title", "上次看到这里"));
    var resumeInfo = el("div", "vp-resume-info", "");
    var resumeOps = el("div", "vp-resume-ops");
    var resumeBtn = el("button", "vp-resume-btn primary", "继续播放");
    resumeBtn.type = "button";
    var restartBtn = el("button", "vp-resume-btn", "从头播放");
    restartBtn.type = "button";
    resumeOps.appendChild(resumeBtn);
    resumeOps.appendChild(restartBtn);
    resumeBox.appendChild(resumeInfo);
    resumeBox.appendChild(resumeOps);
    resumeLayer.appendChild(resumeBox);

    // 结束覆盖层：播放完成后显示"重播 / 下一集"（连播列表存在时才有下一集）
    var endLayer = el("div", "vp-end");
    endLayer.hidden = true;
    var endBox = el("div", "vp-end-box");
    var endReplay = el("button", "vp-end-btn", ICONS.retry + "重播");
    endReplay.type = "button";
    var endNext = el("button", "vp-end-btn next", "下一集");
    endNext.type = "button";
    endBox.appendChild(endReplay);
    endBox.appendChild(endNext);
    endLayer.appendChild(endBox);

    // 全部挂到播放器容器（顺序：视频 → 中央按钮 → 转圈 → 控制栏 → 菜单 → 错误层 → 续播/结束层）
    playerEl.appendChild(center);
    playerEl.appendChild(spinner);
    playerEl.appendChild(controls);
    playerEl.appendChild(settings);
    playerEl.appendChild(errorLayer);
    playerEl.appendChild(resumeLayer);
    playerEl.appendChild(endLayer);

    /* ---------- 4. 状态与偏好记忆（localStorage）---------- */
    var rate = parseFloat(localStorage.getItem("vp_rate") || "1") || 1;
    var vol = parseFloat(localStorage.getItem("vp_volume") || "1") || 1;
    var muted = localStorage.getItem("vp_muted") === "1";
    var dragging = false;        // 是否正在拖拽进度条
    var hideTimer = null;        // 控制栏自动隐藏定时器

    video.volume = Math.min(1, Math.max(0, vol));
    video.muted = muted;
    video.playbackRate = rate;
    volSlider.value = String(video.volume);
    syncRateUI();

    /* ---------- 5. 控制栏显隐（空闲 3 秒隐藏，移动/点击恢复）----------
       B站手机端风格：顶部悬浮栏（返回键+标题）与底部控制栏同步显隐，
       一起加 .hidden（淡出 + 不响应指针），互不干扰。 */
    var topBar = document.getElementById("vp-top");
    function hideControls() {
        if (!video.paused && !video.ended) {
            controls.classList.add("hidden");
            if (topBar) topBar.classList.add("hidden");
        }
    }
    function showControls() {
        controls.classList.remove("hidden");
        if (topBar) topBar.classList.remove("hidden");
        clearTimeout(hideTimer);
        hideTimer = setTimeout(hideControls, 3000);
    }
    // 只在"正在播放"时自动隐藏；暂停时保持可见方便操作
    playerEl.addEventListener("pointermove", showControls);
    playerEl.addEventListener("pointerdown", showControls);
    playerEl.addEventListener("touchstart", showControls);
    playerEl.addEventListener("pointerleave", function () {
        if (!video.paused) clearTimeout(hideTimer), hideTimer = setTimeout(hideControls, 1200);
    });

    /* ---------- 6. 时间格式化（hh:mm:ss / mm:ss）---------- */
    function fmt(sec) {
        if (!isFinite(sec) || sec < 0) sec = 0;
        var s = Math.floor(sec % 60), m = Math.floor(sec / 60) % 60, h = Math.floor(sec / 3600);
        var pad = function (n) { return (n < 10 ? "0" : "") + n; };
        return (h > 0 ? h + ":" + pad(m) : m) + ":" + pad(s);
    }
    function getDuration() { return isFinite(video.duration) ? video.duration : 0; }

    /* ---------- 7. 播放 / 暂停 ---------- */
    function togglePlay() {
        if (video.paused || video.ended) {
            video.play().catch(function () {});  // 自动播放被浏览器拦截时静默
        } else {
            video.pause();
        }
    }
    // 播放/暂停事件 → 切图标 + 中央大按钮显隐
    function syncPlayUI() {
        var playing = !video.paused && !video.ended;
        btnPlay.innerHTML = playing ? ICONS.pause : ICONS.play;
        btnPlay.title = playing ? "暂停（空格）" : "播放（空格）";
        center.hidden = playing;
        showControls();  // 播放中恢复控制栏（随后按空闲定时隐藏），暂停时保持可见
    }
    video.addEventListener("play", syncPlayUI);
    video.addEventListener("pause", syncPlayUI);
    video.addEventListener("ended", syncPlayUI);

    /* ---------- 7.5 播放进度记忆 + 服务端同步 ---------- */
    var lastSaveAt = 0;
    var savedPos = 0;
    var resumeForPath = "";
    var resumeToken = 0;

    function currentPath() { return playerEl.getAttribute("data-key") || ""; }
    function currentPosKey() { return currentPath() ? "vp_pos_" + currentPath() : ""; }
    function reportVideoProgress(completed, keepalive) {
        var d = getDuration(), path = currentPath();
        if (!path || d <= 30 || !window.Personal) return;
        window.Personal.reportProgress({
            path: path,
            kind: "seconds",
            position: completed ? d : video.currentTime,
            total: d,
            completed: !!completed
        }, keepalive);
    }
    function rememberProgress(keepalive) {
        var d = getDuration(), key = currentPosKey();
        if (!key || d <= 30) return;
        if (video.currentTime > 5 && video.currentTime < d - 10) {
            try { localStorage.setItem(key, String(Math.floor(video.currentTime))); } catch (e) {}
            reportVideoProgress(false, !!keepalive);
        }
    }
    function clearProgress() {
        var key = currentPosKey();
        if (key) {
            try { localStorage.removeItem(key); } catch (e) {}
        }
    }

    video.addEventListener("timeupdate", function () {
        var now = Date.now();
        if (now - lastSaveAt < 5000) return;
        lastSaveAt = now;
        rememberProgress();
    });
    video.addEventListener("pause", function () { if (!video.ended) rememberProgress(); });
    window.addEventListener("pagehide", function () {
        rememberProgress(true);
    });

    video.addEventListener("loadedmetadata", function () {
        var path = currentPath();
        if (!path || resumeForPath === path) return;
        resumeForPath = path;
        var token = ++resumeToken;
        var d = getDuration();
        function localSaved() {
            try { return parseInt(localStorage.getItem(currentPosKey()) || "0", 10); } catch (e) { return 0; }
        }
        function offerResume(saved) {
            if (token !== resumeToken || currentPath() !== path) return;
            saved = Number(saved || 0);
            if (saved > 10 && d > 30 && saved < d - 10) {
                savedPos = saved;
                resumeInfo.textContent = "上次看到 " + fmt(saved) + " / " + fmt(d);
                resumeLayer.hidden = false;
                showControls();
            }
        }
        var initial = window.VIEW_CONFIG && window.VIEW_CONFIG.initialProgress;
        if (window.VIEW_CONFIG && path === window.VIEW_CONFIG.path && initial && initial.kind === "seconds") {
            offerResume(initial.position);
        } else if (window.Personal) {
            window.Personal.getState(path).then(function (state) {
                var progress = state.progress;
                offerResume(progress && progress.kind === "seconds" ? progress.position : localSaved());
            }).catch(function () { offerResume(localSaved()); });
        } else {
            offerResume(localSaved());
        }
    });
    resumeBtn.addEventListener("click", function () {
        video.currentTime = savedPos;
        resumeLayer.hidden = true;
        video.play().catch(function () {});
    });
    restartBtn.addEventListener("click", function () {
        clearProgress();
        if (window.Personal && currentPath()) window.Personal.clearProgress(currentPath()).catch(function () {});
        resumeLayer.hidden = true;
        video.currentTime = 0;
        video.play().catch(function () {});
    });

    video.addEventListener("ended", function () {
        clearProgress();
        reportVideoProgress(true, false);
        var items = document.querySelectorAll("#pl-list .pl-item");
        endNext.style.display = (items.length > 1) ? "" : "none";
        endLayer.hidden = false;
        showControls();
    });
    endReplay.addEventListener("click", function () {
        endLayer.hidden = true;
        video.currentTime = 0;
        video.play().catch(function () {});
    });
    endNext.addEventListener("click", function () {
        endLayer.hidden = true;
        if (window.plGo) window.plGo(1);
    });

    video.addEventListener("emptied", function () {
        endLayer.hidden = true;
        resumeLayer.hidden = true;
        errorLayer.hidden = true;
        spinner.hidden = true;
    });

    /* ---------- 8. 进度条（已播 + 缓冲 + 点击/拖拽跳转 + 悬停气泡）---------- */
    var playedBar = controls.querySelector(".vp-progress-played");
    var bufferBar = controls.querySelector(".vp-progress-buffer");
    var thumb = controls.querySelector(".vp-progress-thumb");

    // 用比例刷新进度条（0~1），拖拽中不被打断
    function syncProgress() {
        if (dragging) return;
        var d = getDuration();
        var frac = d ? video.currentTime / d : 0;
        playedBar.style.width = (frac * 100) + "%";
        thumb.style.left = (frac * 100) + "%";
        timeLabel.textContent = fmt(video.currentTime) + " / " + fmt(d);
    }
    video.addEventListener("timeupdate", syncProgress);
    video.addEventListener("durationchange", syncProgress);
    video.addEventListener("loadedmetadata", syncProgress);

    // 缓冲进度：progress 事件给出已缓冲范围，取最后一段的终点
    function syncBuffer() {
        try {
            var b = video.buffered;
            if (b.length) {
                var end = b.end(b.length - 1);
                bufferBar.style.width = (getDuration() ? end / getDuration() * 100 : 0) + "%";
            }
        } catch (e) { /* 个别浏览器缓冲对象不可读时忽略 */ }
    }
    video.addEventListener("progress", syncBuffer);

    // 点击/拖拽跳转：统一用 Pointer 事件（桌面鼠标 + 触屏都支持）
    function seekByClientX(clientX) {
        var r = progress.getBoundingClientRect();
        var frac = Math.min(1, Math.max(0, (clientX - r.left) / r.width));
        if (getDuration()) video.currentTime = frac * getDuration();
        return frac;
    }
    function syncHoverTime(e) {
        var r = progress.getBoundingClientRect();
        var frac = Math.min(1, Math.max(0, (e.clientX - r.left) / r.width));
        hoverTime.textContent = fmt(frac * getDuration());
        hoverTime.style.left = (frac * 100) + "%";
    }
    progress.addEventListener("pointerdown", function (e) {
        if (e.button !== 0 && e.pointerType === "mouse") return;  // 只响应左键
        dragging = true;
        progress.classList.add("dragging");
        progress.setPointerCapture(e.pointerId);  // 拖出进度条也持续收到 move/up
        seekByClientX(e.clientX);
        syncHoverTime(e);
        showControls();
    });
    progress.addEventListener("pointermove", function (e) {
        syncHoverTime(e);
        hoverTime.hidden = false;
        if (dragging) seekByClientX(e.clientX);
    });
    // 结束拖拽：释放指针捕获，隐藏气泡
    function endDrag(e) {
        if (!dragging) return;
        dragging = false;
        progress.classList.remove("dragging");
        hoverTime.hidden = true;
        try { progress.releasePointerCapture(e.pointerId); } catch (err) {}
        showControls();
    }
    progress.addEventListener("pointerup", endDrag);
    progress.addEventListener("pointercancel", endDrag);
    progress.addEventListener("pointerleave", function () { hoverTime.hidden = true; });

    /* ---------- 9. 音量与静音（记忆在 localStorage）---------- */
    function syncVolUI() {
        var mutedNow = video.muted || video.volume === 0;
        btnMute.innerHTML = mutedNow ? ICONS.muted : ICONS.volume;
        btnMute.classList.toggle("active", mutedNow);
        if (!video.muted) volSlider.value = String(video.volume);
    }
    volSlider.addEventListener("input", function () {
        video.muted = false;
        video.volume = parseFloat(volSlider.value) || 0;
    });
    function toggleMute() { video.muted = !video.muted; }
    function setVol(v) {
        video.volume = Math.min(1, Math.max(0, v));
        if (v > 0) video.muted = false;
    }
    video.addEventListener("volumechange", function () {
        // 记忆：只在用户操作（非静音）时覆盖音量，静音只记静音标志
        if (!video.muted) localStorage.setItem("vp_volume", String(video.volume));
        localStorage.setItem("vp_muted", video.muted ? "1" : "0");
        syncVolUI();
    });
    btnMute.addEventListener("click", toggleMute);

    /* ---------- 10. 倍速（记忆在 localStorage）---------- */
    function setRate(r) {
        rate = r;
        video.playbackRate = r;
        localStorage.setItem("vp_rate", String(r));
        syncRateUI();
    }
    function syncRateUI() {
        btnSpeed.textContent = "";                    // 图标按钮 → 显示 "1.0x" 文案
        btnSpeed.style.fontSize = "13px";
        btnSpeed.style.fontWeight = "600";
        btnSpeed.style.width = "auto";
        btnSpeed.style.padding = "0 8px";
        btnSpeed.textContent = rate + "x";
        for (var r in rateBtns) rateBtns[r].classList.toggle("active", rateBtns[r].dataset.rate == rate);
    }
    btnSpeed.addEventListener("click", function (e) {
        e.stopPropagation();   // 阻止冒泡到文档（文档点击会关菜单）
        settings.hidden = !settings.hidden;
    });
    btnSpeed.addEventListener("dblclick", function (e) { e.stopPropagation(); });
    // 点击菜单外关闭
    document.addEventListener("click", function (e) {
        if (!settings.hidden && !settings.contains(e.target) && e.target !== btnSpeed) hideSettings();
    });
    function hideSettings() { settings.hidden = true; }

    /* ---------- 11. 全屏（对播放器容器整体全屏）----------
       移动端：CSS 模拟全屏——不调用浏览器全屏 API（不进入沉浸模式），
       因此不会出现系统"退出全屏"提示条。播放器固定定位铺满视口，
       横视频 + 竖屏视口时把整个播放器（含控制栏/标题）旋转 90°（B 站式全 UI 横屏）。
       桌面端：原生全屏 API + 进入全屏后锁定屏幕横屏。 */
    var isMobileUA = /Android|iPhone|iPad|iPod/i.test(navigator.userAgent);
    function isLandscapeVideo() {   // 横视频：宽 > 高（视频元数据就绪后才有值）
        return !!video.videoWidth && video.videoWidth > video.videoHeight;
    }
    function lockLandscape() {
        if (!isMobileUA || !isLandscapeVideo()) return;
        try {
            if (screen.orientation && screen.orientation.lock) {
                screen.orientation.lock("landscape").catch(function () {});
            }
        } catch (e) { /* iOS 等不支持方向锁定的环境静默忽略 */ }
    }
    function unlockOrientation() {
        if (!isMobileUA) return;
        try {
            if (screen.orientation && screen.orientation.unlock) screen.orientation.unlock();
        } catch (e) {}
    }
    function isMobileFull() {
        return document.body.classList.contains("vp-mobile-full");
    }
    function toggleFullscreen() {
        // 移动端：CSS 模拟全屏（固定定位铺满视口 + 必要时旋转视频），
        // 不调用浏览器全屏 API，因此不会出现系统"退出全屏"提示条。
        if (isMobileUA) {
            if (!isMobileFull()) {
                document.body.classList.add("vp-mobile-full");
                // 横视频 + 竖屏视口：旋转整个播放器（视频+控制栏+标题）铺满（B 站式全 UI 横屏）
                if (isLandscapeVideo() && window.innerWidth < window.innerHeight) {
                    playerEl.classList.add("rotated");
                } else {
                    playerEl.classList.remove("rotated");
                }
            } else {
                document.body.classList.remove("vp-mobile-full");
                playerEl.classList.remove("rotated");
            }
            syncFullUI();   // 刷新全屏图标
            return;
        }

        // 桌面端使用原生全屏 API
        if (document.fullscreenElement || document.webkitFullscreenElement) {
            (document.exitFullscreen || document.webkitExitFullscreen).call(document);
        } else {
            var req = playerEl.requestFullscreen || playerEl.webkitRequestFullscreen;
            if (req) {
                var p = req.call(playerEl);
                // 方向锁定必须在"已进入全屏"后才能生效：Promise 就绪后再锁
                if (p && p.then) p.then(lockLandscape).catch(function () {});
                else lockLandscape();   // 老 Safari 无 Promise 返回值：直接尝试
            }
        }
    }
    // 全屏状态变化 → 切全屏图标（进入/退出都刷新）
    function syncFullUI() {
        var fs = document.fullscreenElement || document.webkitFullscreenElement;
        var mobileFull = isMobileFull();
        btnFull.innerHTML = (fs || mobileFull) ? ICONS.compress : ICONS.full;
        btnFull.title = (fs || mobileFull) ? "退出全屏（F）" : "全屏（F）";
        if (!fs && !mobileFull) unlockOrientation();   // 退出全屏：解锁方向，恢复竖屏
        // 全屏时若正在播放且鼠标闲置，同样自动隐藏控制栏
        showControls();
    }
    document.addEventListener("fullscreenchange", syncFullUI);
    document.addEventListener("webkitfullscreenchange", syncFullUI);
    btnFull.addEventListener("click", toggleFullscreen);
    // 模拟全屏期间元数据才就绪：按真实宽高比补上/去掉旋转（进入全屏早于加载完成时）
    video.addEventListener("loadedmetadata", function () {
        if (!isMobileFull()) return;
        if (isLandscapeVideo() && window.innerWidth < window.innerHeight) {
            playerEl.classList.add("rotated");
        } else {
            playerEl.classList.remove("rotated");
        }
    });

    // 点击视频本体：播放/暂停；双击：全屏（控制栏按钮的点击不会冒泡到视频）
    video.addEventListener("click", function () {
        if (!dragging) togglePlay();
    });
    video.addEventListener("dblclick", function (e) {
        e.preventDefault();
        toggleFullscreen();
    });

    /* ---------- 12. 画中画（浏览器不支持则隐藏按钮）---------- */
    function togglePip() {
        if (document.pictureInPictureElement) {
            document.exitPictureInPicture().catch(function () {});
        } else if (video.requestPictureInPicture) {
            video.requestPictureInPicture().catch(function () {});
        }
    }
    if (!video.requestPictureInPicture) {
        btnPip.style.display = "none";
    } else {
        btnPip.addEventListener("click", togglePip);
        video.addEventListener("enterpictureinpicture", function () { btnPip.classList.add("active"); });
        video.addEventListener("leavepictureinpicture", function () { btnPip.classList.remove("active"); });
    }

    /* ---------- 13. 上一集/下一集（联动 view.html 的连播逻辑）---------- */
    // 注意：view.html 的连播脚本在本文件之后才执行，window.plGo 此时还没定义，
    // 因此这里只在"点击时"判断函数是否存在，避免初始化时误隐藏按钮。
    btnPrev.addEventListener("click", function () { if (window.plGo) window.plGo(-1); });
    btnNext.addEventListener("click", function () { if (window.plGo) window.plGo(1); });

    /* ---------- 13.5 宽屏 / 网页全屏（B 站式三种尺寸模式：常规、宽屏、网页全屏、全屏）---------- */
    var pageEl = document.getElementById("vp-page");
    // 宽屏：播放器撑满可用宽度（CSS .vp-page.wide 控制），偏好记忆在 localStorage
    function toggleWide() {
        if (!pageEl) return;
        var on = pageEl.classList.toggle("wide");
        localStorage.setItem("vp_wide", on ? "1" : "0");
        btnWide.classList.toggle("active", on);
        showControls();
    }
    // 网页全屏：隐藏页面其余元素，播放器铺满浏览器窗口（body.vp-web-full 控制）
    function toggleWebFull() {
        var on = document.body.classList.toggle("vp-web-full");
        btnWebFull.classList.toggle("active", on);
        showControls();
    }
    btnWide.addEventListener("click", toggleWide);
    btnWebFull.addEventListener("click", toggleWebFull);
    // 网页全屏 / 模拟全屏下按 ESC 退出（浏览器原生全屏的 ESC 由浏览器自身处理）
    document.addEventListener("keydown", function (e) {
        if (e.key !== "Escape") return;
        if (document.body.classList.contains("vp-web-full")) toggleWebFull();
        if (document.body.classList.contains("vp-mobile-full")) toggleFullscreen();
    });

    /* ---------- 14. 加载中 / 错误 ---------- */
    video.addEventListener("waiting", function () { spinner.hidden = false; });
    video.addEventListener("playing", function () { spinner.hidden = true; });
    video.addEventListener("canplay", function () { spinner.hidden = true; });
    video.addEventListener("stalled", function () { /* 网络慢不转圈，保持当前画面 */ });
    video.addEventListener("error", function () {
        // 切换集数瞬间旧 src 被清掉会触发一次无害错误，此时无有效媒体，忽略
        var t = video.currentSrc || "";
        if (!t) return;
        // 4=格式不支持；2/3=网络/解码失败（如服务端转码超时、流被截断）——
        // 两类都提示并给出重试，避免播放失败时只留一个无限转圈
        var code = video.error && video.error.code;
        var msg = code === 4 ? "视频格式不支持" : "视频加载失败";
        var label = errorLayer.querySelector("span");
        if (label) label.textContent = msg;
        spinner.hidden = true;
        errorLayer.hidden = false;
    });

    /* ---------- 15. 键盘快捷键 ---------- */
    document.addEventListener("keydown", function (e) {
        var tag = (e.target.tagName || "").toLowerCase();
        // 输入框/按钮等可交互元素里不拦截（空格/回车等让给它们自己处理）
        if (["input", "textarea", "select", "button", "a"].indexOf(tag) >= 0) return;
        var k = e.key;
        if (k === " " || k.toLowerCase() === "k") { togglePlay(); e.preventDefault(); return; }
        if (k === "ArrowLeft") { video.currentTime = Math.max(0, video.currentTime - 5); e.preventDefault(); return; }
        if (k === "ArrowRight") { video.currentTime = Math.min(getDuration(), video.currentTime + 5); e.preventDefault(); return; }
        if (k === "ArrowUp") { setVol(video.volume + 0.1); e.preventDefault(); return; }
        if (k === "ArrowDown") { setVol(video.volume - 0.1); e.preventDefault(); return; }
        if (k.toLowerCase() === "m") { toggleMute(); e.preventDefault(); return; }
        if (k.toLowerCase() === "f") { toggleFullscreen(); e.preventDefault(); return; }
        if (k.toLowerCase() === "p") { togglePip(); e.preventDefault(); return; }
        if (k === ">" || k === ".") { var i = RATES.indexOf(rate) + 1; if (i < RATES.length) setRate(RATES[i]); e.preventDefault(); return; }
        if (k === "<" || k === ",") { var j = RATES.indexOf(rate) - 1; if (j >= 0) setRate(RATES[j]); e.preventDefault(); return; }
        if (k >= "0" && k <= "9" && getDuration()) {
            video.currentTime = getDuration() * (+k) / 10;   // 0 跳到开头，9 跳到 90%
            e.preventDefault();
        }
    });

    /* ---------- 16. 初始化 ---------- */
    // 恢复宽屏偏好
    if (pageEl && localStorage.getItem("vp_wide") === "1") {
        pageEl.classList.add("wide");
        btnWide.classList.add("active");
    }
    syncVolUI();
    syncPlayUI();
    syncProgress();
    syncBuffer();
})();
