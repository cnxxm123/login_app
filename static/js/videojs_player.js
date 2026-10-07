/*
 * Video.js 适配层：只负责初始化开源播放器和视频进度记忆。
 * 播放列表切换由 view.js 负责，播放器控件由 Video.js 官方 skin 负责。
 */
(function () {
    "use strict";

    var cfg = window.VIEW_CONFIG || {};
    // 视频页用 <video id="media-player">，音频页用 <audio id="media-player">，
    // 二者在 view.html 的 {% elif %} 分支里互斥渲染（同一页面只会存在一个），
    // 所以共用 id 不冲突；本脚本只在视频类型下初始化 Video.js。
    var element = document.getElementById("media-player");
    if (cfg.mediaType !== "video" || !element || typeof window.videojs !== "function") return;

    var player;
    try {
        player = window.videojs(element, {
            controls: true,
            autoplay: false,
            preload: "metadata",
            fluid: true,
            responsive: true,
            aspectRatio: "16:9",
            nativeControlsForTouch: false,
            playbackRates: [0.5, 0.75, 1, 1.25, 1.5, 2],
            // 控制栏自动隐藏时间：2500ms 在手机上偏短（刚看到还没来得及点就隐了），
            // 延到 3500ms 给移动端更从容的操作窗口。
            inactivityTimeout: 3500,
            userActions: {hotkeys: true},
            controlBar: {
                volumePanel: {inline: false}
            }
        });
    } catch (error) {
        // CDN 加载失败时保留原生 video 控件，至少不让页面完全失去播放能力。
        element.controls = true;
        return;
    }

    // 供 view.js 使用 Video.js API 切换视频源。
    window.videoPlayer = player;

    // ===== 偏好记忆：音量 / 倍速 / 静音 =====
    // 存 localStorage，页面刷新或切换视频都能复用上次设置。
    // 应用偏好不加屏蔽标志：即使触发 volumechange 把同样的值再写一次 localStorage
    // 也是无害的，省得多维护一个状态位。
    var PREF_VOL = "vp_volume";
    var PREF_RATE = "vp_rate";
    var PREF_MUTED = "vp_muted";

    function applyPrefs() {
        try {
            var v = parseFloat(localStorage.getItem(PREF_VOL));
            if (isFinite(v) && v >= 0 && v <= 1) player.volume(v);
            if (localStorage.getItem(PREF_MUTED) === "1") player.muted(true);
            var r = parseFloat(localStorage.getItem(PREF_RATE));
            // 兼容老配置里的异常值；Video.js 当前允许的倍速范围是 0.5~2
            if (isFinite(r) && r >= 0.25 && r <= 4) player.playbackRate(r);
        } catch (e) {}
    }
    // ready 回调触发时 Video.js 已就绪，volume/rate/muted API 可用
    player.ready(applyPrefs);
    player.on("volumechange", function () {
        try {
            localStorage.setItem(PREF_VOL, String(player.volume()));
            localStorage.setItem(PREF_MUTED, player.muted() ? "1" : "0");
        } catch (e) {}
    });
    player.on("ratechange", function () {
        try {
            localStorage.setItem(PREF_RATE, String(player.playbackRate()));
        } catch (e) {}
    });

    var lastSaveAt = 0;
    var savedPos = 0;
    var resumeForPath = "";
    var resumeToken = 0;

    function currentPath() {
        var box = document.getElementById("vp-player");
        return box ? box.getAttribute("data-key") || "" : "";
    }
    function duration() {
        var value = Number(player.duration());
        return isFinite(value) ? value : 0;
    }
    function currentTime() {
        var value = Number(player.currentTime());
        return isFinite(value) ? value : 0;
    }
    function localKey() {
        var path = currentPath();
        return path ? "vp_pos_" + path : "";
    }
    function rememberProgress() {
        var total = duration();
        var position = currentTime();
        var key = localKey();
        if (!key || total <= 30) return;
        if (position > 5 && position < total - 10) {
            try { localStorage.setItem(key, String(Math.floor(position))); } catch (e) {}
        }
    }
    function clearProgress() {
        var key = localKey();
        if (key) {
            try { localStorage.removeItem(key); } catch (e) {}
        }
    }
    function localSaved() {
        try { return Number(localStorage.getItem(localKey()) || 0); } catch (e) { return 0; }
    }
    function offerResume(path, token, value) {
        if (token !== resumeToken || currentPath() !== path) return;
        var total = duration();
        value = Number(value || 0);
        if (value <= 10 || total <= 30 || value >= total - 10) return;
        savedPos = value;
        // 用项目统一的自定义弹窗（theme.js 的 confirmBox）替代 window.confirm——
        // require.md 规范要求弹窗一律自定义；原生 confirm 在移动端会阻塞媒体解码，
        // 用户点"取消"前视频也无法继续加载。
        var message = "上次看到 " + formatTime(value) + " / " + formatTime(total) + "，是否继续播放？";
        var fn = typeof window.confirmBox === "function" ? window.confirmBox : null;
        var ask = fn
            ? fn(message, {title: "续播提示", okText: "继续播放", cancelText: "从头开始"})
            : Promise.resolve(window.confirm(message));
        ask.then(function (ok) {
            // 用户按下按钮之前，若已切到下一集/关闭页面，不要再跳位置
            if (token !== resumeToken || currentPath() !== path) return;
            if (ok) {
                player.currentTime(value);
            } else {
                // 从头开始播：清掉旧进度，避免下一次打开又弹"上次看到"
                clearProgress();
                player.currentTime(0);
            }
            player.play().catch(function () {});
        });
    }
    function formatTime(value) {
        value = Math.max(0, Math.floor(Number(value) || 0));
        var minutes = Math.floor(value / 60);
        var seconds = String(value % 60).padStart(2, "0");
        if (minutes >= 60) {
            var hours = Math.floor(minutes / 60);
            minutes = String(minutes % 60).padStart(2, "0");
            return hours + ":" + minutes + ":" + seconds;
        }
        return minutes + ":" + seconds;
    }

    player.on("timeupdate", function () {
        var now = Date.now();
        if (now - lastSaveAt < 5000) return;
        lastSaveAt = now;
        rememberProgress();
    });
    player.on("pause", function () {
        if (!player.ended()) rememberProgress();
    });
    window.addEventListener("pagehide", function () { rememberProgress(); });

    player.on("loadedmetadata", function () {
        var path = currentPath();
        if (!path || resumeForPath === path) return;
        resumeForPath = path;
        var token = ++resumeToken;
        offerResume(path, token, localSaved());
    });

    // ===== 结束覆盖层：倒计时自动连播 + 重播 + 取消 =====
    // DOM 由模板渲染（见 view.html 的 .vp-ended），本脚本只控制显隐 + 倒计时。
    // 没有下一集时隐藏倒计时文案和"立即下一集"按钮，只保留"重播""取消"。
    var endedOverlay = document.getElementById("vp-ended");
    var countdownEl = document.getElementById("vp-ended-count");
    var countdownSub = document.getElementById("vp-ended-sub");
    var nextBtn = document.getElementById("vp-ended-next");
    var replayBtn = document.getElementById("vp-ended-replay");
    var cancelBtn = document.getElementById("vp-ended-cancel");
    var countdownTimer = null;
    var COUNTDOWN_SECONDS = 5;

    function hasNextEpisode() {
        var list = cfg.playlist || [];
        return list.length > 1;  // 目录连播是循环的，只要不止一个视频就能切下一集
    }
    function stopCountdown() {
        if (countdownTimer) {
            clearInterval(countdownTimer);
            countdownTimer = null;
        }
    }
    function hideEndedOverlay() {
        if (!endedOverlay) return;
        stopCountdown();
        endedOverlay.hidden = true;
    }
    function goNextEpisode() {
        hideEndedOverlay();
        if (typeof window.plGo === "function") window.plGo(1);
    }
    function replayCurrent() {
        hideEndedOverlay();
        player.currentTime(0);
        player.play().catch(function () {});
    }
    function startCountdown(seconds) {
        stopCountdown();
        var remaining = seconds;
        if (countdownEl) countdownEl.textContent = String(remaining);
        countdownTimer = setInterval(function () {
            remaining -= 1;
            if (remaining <= 0) {
                stopCountdown();
                goNextEpisode();
                return;
            }
            if (countdownEl) countdownEl.textContent = String(remaining);
        }, 1000);
    }
    function showEndedOverlay() {
        if (!endedOverlay) return;
        var withNext = hasNextEpisode();
        if (countdownSub) countdownSub.hidden = !withNext;
        if (nextBtn) nextBtn.hidden = !withNext;
        endedOverlay.hidden = false;
        if (withNext) startCountdown(COUNTDOWN_SECONDS);
    }

    if (nextBtn) nextBtn.addEventListener("click", goNextEpisode);
    if (replayBtn) replayBtn.addEventListener("click", replayCurrent);
    if (cancelBtn) cancelBtn.addEventListener("click", hideEndedOverlay);

    player.on("ended", function () {
        clearProgress();
        showEndedOverlay();
    });
    // 切换视频源（手动选集、点"立即下一集"后 view.js 调 src()）会触发 loadstart，
    // 此时把覆盖层清掉，避免倒计时越界把下一集也顺手切了。
    player.on("loadstart", hideEndedOverlay);
    // 覆盖层出现时用户点大播放按钮也当作"取消"（继续看最后一帧没意义，但保持交互一致）
    player.on("play", hideEndedOverlay);
}());
