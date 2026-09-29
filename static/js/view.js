/* 通用查看页：阅读进度、图片阅读、目录和音视频连播。 */
(function () {
    "use strict";

    var cfg = window.VIEW_CONFIG || {};

    // ===== 文档阅读进度：恢复并按滚动比例节流同步 =====
    (function () {
        var bar = document.getElementById("reading-bar");
        if (!bar) return;
        var restored = false;

        function ratio() {
            var root = document.documentElement;
            var max = root.scrollHeight - root.clientHeight;
            return max > 0 ? Math.min(Math.max(window.scrollY / max, 0), 1) : 0;
        }
        function update(sync) {
            var value = ratio();
            bar.style.width = (value * 100) + "%";
            if (!cfg.trackScroll || !sync) return;
        }
        window.addEventListener("scroll", function () { update(true); }, {passive: true});
        window.addEventListener("resize", function () { update(false); });
        
        window.requestAnimationFrame(function () {
            var progress = cfg.initialProgress;
            if (!restored && cfg.trackScroll && progress && progress.kind === "scroll" && progress.position > 0 && progress.position < 0.98) {
                restored = true;
                var root = document.documentElement;
                window.scrollTo(0, (root.scrollHeight - root.clientHeight) * progress.position);
            }
            update(false);
        });
    }());

    // ===== 图片阅读器：单页/长条、翻页、缩放、全屏、进度 =====
    var imgs = cfg.imageUrls || [];
    var imagePaths = cfg.imagePaths || [];
    var reader = document.getElementById("reader-single");
    var strip = document.getElementById("img-strip");
    if (reader) {
        var currentUrl = cfg.currentUrl;
        var posKey = "img_pos_" + cfg.parent;
        var saved = null;
        try { saved = JSON.parse(localStorage.getItem(posKey) || "null"); } catch (e) {}
        var cur = 0;
        var serverProgress = cfg.initialProgress;
        if (serverProgress && serverProgress.kind === "page" && serverProgress.locator) {
            cur = imagePaths.indexOf(serverProgress.locator);
        }
        if (cur < 0 || cur >= imgs.length) cur = 0;
        if ((!serverProgress || serverProgress.kind !== "page") && saved && saved.path === currentUrl && saved.index >= 0 && saved.index < imgs.length) {
            cur = saved.index;
        } else if ((!serverProgress || serverProgress.kind !== "page") && imgs.indexOf(currentUrl) >= 0) {
            cur = imgs.indexOf(currentUrl);
        }
        var scale = 1;
        var mode = "single";

        function saveImageProgress() {
            try { localStorage.setItem(posKey, JSON.stringify({index: cur, path: imgs[cur]})); } catch (e) {}
        }
        function show(i) {
            if (!imgs.length) return;
            cur = Math.max(0, Math.min(imgs.length - 1, i));
            var img = document.getElementById("reader-img");
            img.src = imgs[cur];
            img.style.transform = "";
            scale = 1;
            document.getElementById("reader-pos").textContent = (cur + 1) + " / " + imgs.length;
            saveImageProgress();
        }
        function go(d) { show(cur + d); }
        function currentContainer() { return strip.hidden ? reader : strip; }
        function applyZoom() {
            var element = mode === "single" ? document.getElementById("reader-img") : strip;
            element.style.transform = scale === 1 ? "" : "scale(" + scale + ")";
        }
        function zoom(d) { scale = Math.min(3, Math.max(0.5, +(scale + d).toFixed(2))); applyZoom(); }
        function zoomReset() { scale = 1; applyZoom(); }
        function toggleFullscreen() {
            var element = currentContainer();
            if (!document.fullscreenElement && !document.webkitFullscreenElement) {
                var request = element.requestFullscreen || element.webkitRequestFullscreen;
                if (request) request.call(element);
            } else if (document.exitFullscreen) {
                document.exitFullscreen();
            } else if (document.webkitExitFullscreen) {
                document.webkitExitFullscreen();
            }
        }
        function scrollToCurrent() {
            var items = strip.querySelectorAll(".img-item");
            if (items[cur]) items[cur].scrollIntoView({block: "start"});
        }
        function setMode(value) {
            mode = value;
            document.getElementById("mode-single").classList.toggle("active", value === "single");
            document.getElementById("mode-strip").classList.toggle("active", value === "strip");
            reader.hidden = value !== "single";
            strip.hidden = value !== "strip";
            applyZoom();
            if (value === "single") show(cur);
            else if (value === "strip") scrollToCurrent();
        }
        document.addEventListener("keydown", function (event) {
            var tag = (event.target.tagName || "").toLowerCase();
            if (tag === "input" || tag === "textarea") return;
            if (event.key === "+" || event.key === "=") { zoom(0.2); event.preventDefault(); return; }
            if (event.key === "-" || event.key === "_") { zoom(-0.2); event.preventDefault(); return; }
            if (event.key === "0") { zoomReset(); event.preventDefault(); return; }
            if (event.key.toLowerCase() === "f") { toggleFullscreen(); event.preventDefault(); return; }
            if (!reader.hidden) {
                if (["ArrowLeft", "ArrowUp", "PageUp"].indexOf(event.key) >= 0) { go(-1); event.preventDefault(); }
                else if (["ArrowRight", "ArrowDown", "PageDown", " "].indexOf(event.key) >= 0) { go(1); event.preventDefault(); }
            }
        });
        window.go = go;
        window.zoom = zoom;
        window.zoomReset = zoomReset;
        window.toggleFullscreen = toggleFullscreen;
        window.setMode = setMode;
        // 长条模式根据进入视口中心的图片更新当前页，避免进度停在切换前位置。
        if ("IntersectionObserver" in window) {
            var stripItems = Array.prototype.slice.call(strip.querySelectorAll(".img-item"));
            var observer = new IntersectionObserver(function (entries) {
                entries.forEach(function (entry) {
                    if (!entry.isIntersecting || mode !== "strip") return;
                    var index = stripItems.indexOf(entry.target);
                    if (index >= 0 && index !== cur) {
                        cur = index;
                        document.getElementById("reader-pos").textContent = (cur + 1) + " / " + imgs.length;
                        saveImageProgress();
                    }
                });
            }, {root: null, rootMargin: "-20% 0px -55% 0px", threshold: 0});
            stripItems.forEach(function (item) { observer.observe(item); });
        }
        setMode(mode);
    }

    // ===== 文档目录 =====
    (function () {
        var body = document.querySelector(".md-body");
        var toggle = document.getElementById("toc-toggle");
        var panel = document.getElementById("toc-panel");
        if (!body || !toggle || !panel) return;
        var headings = body.querySelectorAll("h1, h2, h3");
        if (!headings.length) return;
        headings.forEach(function (heading, index) { if (!heading.id) heading.id = "toc-h" + index; });
        var list = document.createElement("ul");
        headings.forEach(function (heading) {
            var item = document.createElement("li");
            item.className = "toc-" + heading.tagName.toLowerCase();
            var link = document.createElement("a");
            link.textContent = heading.textContent;
            link.href = "#" + heading.id;
            link.addEventListener("click", function (event) {
                event.preventDefault();
                heading.scrollIntoView({behavior: "smooth", block: "start"});
            });
            item.appendChild(link);
            list.appendChild(item);
        });
        document.getElementById("toc-list").appendChild(list);
        toggle.hidden = false;
        toggle.addEventListener("click", function () { panel.hidden = !panel.hidden; });
    }());

    // ===== 编辑保存提示 =====
    (function () {
        if (new URLSearchParams(location.search).get("saved") !== "1") return;
        var node = document.createElement("div");
        node.className = "save-toast";
        node.textContent = "已保存";
        document.body.appendChild(node);
        setTimeout(function () { node.classList.add("hide"); }, 1800);
        setTimeout(function () { node.remove(); }, 2400);
    }());

    // ===== 音视频连播与音频进度 =====
    (function () {
        var playlist = cfg.playlist || [];
        var player = document.getElementById("media-player");
        var videoApi = cfg.mediaType === "video" ? (window.videoPlayer || null) : null;
        if (!player || !playlist.length) return;
        var pIndex = cfg.playlistIndex || 0;
        var list = document.getElementById("pl-list");
        var count = document.getElementById("pl-count");
        var lastSaveAt = 0;
        var restoredPath = null;
        var restoreToken = 0;

        function currentItem() { return playlist[pIndex]; }
        function mediaEnded() { return videoApi ? videoApi.ended() : player.ended; }
        function mediaSetSource(item) {
            if (videoApi) {
                videoApi.src({src: item.url});
                videoApi.poster(item.thumb || "");
            } else {
                player.src = item.url;
                if (cfg.mediaType === "video") player.poster = item.thumb || "";
            }
        }
        function mediaPlay() {
            var result = videoApi ? videoApi.play() : player.play();
            if (result && typeof result.catch === "function") result.catch(function () {});
        }
        function localKey() { return "media_pos_" + currentItem().path; }
        function rememberAudio(completed) {
            if (cfg.mediaType !== "audio" || !isFinite(player.duration) || player.duration <= 0) return;
            var position = completed ? player.duration : player.currentTime;
            try {
                if (completed) localStorage.removeItem(localKey());
                else if (position > 5 && position < player.duration - 5) localStorage.setItem(localKey(), String(Math.floor(position)));
            } catch (e) {}
        }
        if (cfg.mediaType === "audio") {
            player.addEventListener("timeupdate", function () {
                var now = Date.now();
                if (now - lastSaveAt < 5000) return;
                lastSaveAt = now;
                rememberAudio(false);
            });
            player.addEventListener("pause", function () { if (!player.ended) rememberAudio(false); });
            window.addEventListener("pagehide", function () { rememberAudio(false); });
            player.addEventListener("loadedmetadata", function () {
                var item = currentItem();
                if (restoredPath === item.path) return;
                restoredPath = item.path;
                var token = ++restoreToken;
                function localSaved() {
                    try { return Number(localStorage.getItem(localKey()) || 0); } catch (e) { return 0; }
                }
                function applySaved(saved) {
                    if (token !== restoreToken || currentItem().path !== item.path) return;
                    saved = Number(saved || 0);
                    if (saved > 5 && saved < player.duration - 5) player.currentTime = saved;
                }
                if (item.path === cfg.path && cfg.initialProgress && cfg.initialProgress.kind === "seconds") {
                    applySaved(cfg.initialProgress.position);
                } else {
                    applySaved(localSaved());
                }
            });
            player.addEventListener("ended", function () { rememberAudio(true); });
        }

        if (count) count.textContent = "共 " + playlist.length + " 项";
        var headTitle = document.querySelector("#pl-head span");
        if (headTitle) headTitle.textContent = headTitle.textContent.split("（")[0] + "（" + playlist.length + " 项）";
        playlist.forEach(function (item, index) {
            var button = document.createElement("button");
            button.type = "button";
            button.className = "pl-item" + (index === pIndex ? " active" : "");
            if (item.thumb) {
                var thumb = document.createElement("span");
                thumb.className = "pl-thumb";
                var image = document.createElement("img");
                image.src = item.thumb; image.alt = ""; image.loading = "lazy";
                image.addEventListener("error", function () {
                    // 缩略图抽帧失败时保留列表项，不让破图图标破坏布局。
                    thumb.classList.add("thumb-fallback");
                    image.remove();
                });
                thumb.appendChild(image); button.appendChild(thumb);
            } else {
                var number = document.createElement("span");
                number.className = "pl-idx"; number.textContent = (index + 1) + ".";
                button.appendChild(number);
            }
            var name = document.createElement("span");
            name.className = "pl-name"; name.textContent = item.name;
            button.appendChild(name);
            button.addEventListener("click", function () { playAt(index); });
            list.appendChild(button);
        });

        function updateActive() {
            list.querySelectorAll(".pl-item").forEach(function (element, index) {
                var active = index === pIndex;
                element.classList.toggle("active", active);
                if (active) element.setAttribute("aria-current", "true");
                else element.removeAttribute("aria-current");
            });
            var current = list.querySelector(".pl-item.active");
            if (current) current.scrollIntoView({block: "nearest"});
        }
        function playAt(index) {
            if (index < 0) index = playlist.length - 1;
            if (index >= playlist.length) index = 0;
            if (cfg.mediaType === "audio" && !mediaEnded()) rememberAudio(false);
            pIndex = index;
            var item = currentItem();
            mediaSetSource(item);
            var videoBox = document.getElementById("vp-player");
            if (videoBox) {
                videoBox.setAttribute("data-key", item.path);
                videoBox.setAttribute("data-download-url", item.download || "");
            }
            mediaPlay();
            document.title = item.name;
            var title = document.getElementById("vp-title");
            if (title) title.textContent = item.name;
            var meta = document.querySelector(".meta span:last-child");
            if (meta) meta.textContent = item.name;
            updateActive();
        }
        // 视频结束后由自定义结束层让用户决定是否播放下一集；音频仍保持自动连播。
        if (cfg.mediaType === "audio") {
            player.addEventListener("ended", function () { playAt(pIndex + 1); });
        }
        window.plGo = function (delta) { playAt(pIndex + delta); };
        window.togglePlaylist = function () {
            var panel = document.getElementById("pl-panel");
            var head = document.getElementById("pl-head");
            if (!panel) return;
            panel.hidden = !panel.hidden;
            if (head) head.classList.toggle("open", !panel.hidden);
        };

        // 视频页移动端播放列表：使用页面抽屉，不侵入 Video.js 官方控制栏。
        var videoPage = document.getElementById("vp-page");
        var videoSide = videoPage && videoPage.querySelector(".vp-side");
        var videoToggle = document.getElementById("vp-playlist-toggle");
        var videoClose = document.getElementById("vp-playlist-close");
        var videoBackdrop = null;
        function setVideoPlaylistOpen(open) {
            if (!videoPage || !videoSide) return;
            videoPage.classList.toggle("playlist-open", !!open);
            if (videoToggle) videoToggle.setAttribute("aria-expanded", open ? "true" : "false");
            if (videoBackdrop) videoBackdrop.setAttribute("aria-hidden", open ? "false" : "true");
        }
        if (videoPage && videoSide) {
            videoBackdrop = document.createElement("button");
            videoBackdrop.type = "button";
            videoBackdrop.className = "vp-playlist-backdrop";
            videoBackdrop.setAttribute("aria-label", "关闭播放列表");
            videoBackdrop.setAttribute("aria-hidden", "true");
            videoPage.appendChild(videoBackdrop);
            videoBackdrop.addEventListener("click", function () { setVideoPlaylistOpen(false); });
            if (videoToggle) videoToggle.addEventListener("click", function () {
                setVideoPlaylistOpen(!videoPage.classList.contains("playlist-open"));
            });
            if (videoClose) videoClose.addEventListener("click", function () { setVideoPlaylistOpen(false); });
            list.addEventListener("click", function () { setVideoPlaylistOpen(false); });
            document.addEventListener("keydown", function (event) {
                if (event.key === "Escape") setVideoPlaylistOpen(false);
            });
        }
        window.toggleVideoPlaylist = function () {
            setVideoPlaylistOpen(!videoPage.classList.contains("playlist-open"));
        };
    }());
}());
