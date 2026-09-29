/*
 * Video.js 适配层：只负责初始化开源播放器和视频进度记忆。
 * 播放列表切换由 view.js 负责，播放器控件由 Video.js 官方 skin 负责。
 */
(function () {
    "use strict";

    var cfg = window.VIEW_CONFIG || {};
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
            inactivityTimeout: 2500,
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
        if (value > 10 && total > 30 && value < total - 10) {
            savedPos = value;
            // Video.js 没有强制弹窗，使用原生 confirm 让用户决定是否续播，
            // 避免旧自制覆盖层遮挡移动端视频画面。
            if (window.confirm("上次看到 " + formatTime(value) + " / " + formatTime(total) + "，继续播放吗？")) {
                player.currentTime(value);
                player.play().catch(function () {});
            }
        }
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
        var initial = cfg.initialProgress;
        if (path === cfg.path && initial && initial.kind === "seconds") {
            offerResume(path, token, initial.position);
        } else {
            offerResume(path, token, localSaved());
        }
    });

    player.on("ended", function () {
        clearProgress();
    });
}());
