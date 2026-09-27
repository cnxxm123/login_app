/*
 * PhotoSwipe 图集适配层。
 * PhotoSwipe 负责单页模式的缩放、滑动、键盘和全屏；项目只保留长条模式、
 * 目录进度、缩略图和阅读偏好等业务逻辑。
 */
(function () {
    "use strict";

    var D = window.GALLERY_DATA || {};
    var imgs = D.imageUrls || [];
    var paths = D.imagePaths || [];
    var thumbs = D.thumbUrls || [];
    var sizes = D.imageSizes || [];
    var total = imgs.length;
    var itemPath = D.itemPath || "";

    var stage = document.getElementById("gl-stage");
    var strip = document.getElementById("gl-strip");
    var posEl = document.getElementById("gl-pos");
    var progress = document.getElementById("gl-progress-fill");
    var thumbsBar = document.getElementById("gl-thumbs");
    var thumbsTrack = document.getElementById("gl-thumbs-track");
    var settingsMask = document.getElementById("gl-settings");
    var jumpMask = document.getElementById("gl-jump");
    var jumpInput = document.getElementById("gl-jump-input");
    var isCoarse = window.matchMedia && window.matchMedia("(pointer: coarse)").matches;
    var posKey = "gallery_pos_" + itemPath;
    var autoTimer = null;
    var lightbox = null;

    if (!total || !stage || !strip) return;

    var S = {
        mode: loadPref("gallery_mode", "single") === "strip" ? "strip" : "single",
        cur: 0,
        thumbsOn: loadPref("gallery_thumbs", !isCoarse),
        autoplay: loadPref("gallery_auto", false),
        autoInterval: Math.max(1, Math.min(30, Number(loadPref("gallery_auto_interval", 4)) || 4))
    };

    function loadPref(key, fallback) {
        try {
            var value = localStorage.getItem(key);
            return value === null ? fallback : JSON.parse(value);
        } catch (e) { return fallback; }
    }
    function savePref(key, value) {
        try { localStorage.setItem(key, JSON.stringify(value)); } catch (e) {}
    }
    function clampIndex(index) { return Math.max(0, Math.min(total - 1, Number(index) || 0)); }
    function pageLabel() { return (S.cur + 1) + " / " + total; }
    function itemSize(index) {
        var size = sizes[index] || [];
        return {width: Math.max(1, Number(size[0]) || 1600), height: Math.max(1, Number(size[1]) || 1200)};
    }

    function restorePosition() {
        var saved = loadPref(posKey, null);
        if (!saved) return;
        if (saved.mode === "strip" && typeof saved.ratio === "number") {
            S._stripRatio = Math.max(0, Math.min(1, saved.ratio));
        } else if (typeof saved.index === "number") {
            S.cur = clampIndex(saved.index);
        }
    }

    function progressPayload() {
        return {
            path: itemPath,
            kind: "page",
            position: S.cur + 1,
            total: total,
            locator: paths[S.cur] || null,
            completed: S.cur >= total - 1
        };
    }
    function syncGlobalProgress() {
        if (!window.Personal || typeof window.Personal.reportProgress !== "function" || !itemPath) return;
        clearTimeout(syncTimer);
        syncTimer = setTimeout(function () { window.Personal.reportProgress(progressPayload()); }, 600);
    }
    var syncTimer = null;
    window.addEventListener("pagehide", function () {
        clearTimeout(syncTimer);
        if (window.Personal && typeof window.Personal.reportProgress === "function" && itemPath) {
            window.Personal.reportProgress(progressPayload(), true);
        }
    });

    function savePosition() {
        var value = {mode: S.mode, index: S.cur};
        if (S.mode === "strip") {
            var range = strip.scrollHeight - strip.clientHeight;
            value.ratio = range > 0 ? strip.scrollTop / range : 0;
        }
        savePref(posKey, value);
        syncGlobalProgress();
    }

    function markThumb() {
        if (!thumbsTrack) return;
        var active = thumbsTrack.querySelector(".gl-thumb.active");
        if (active) active.classList.remove("active");
        var current = thumbsTrack.querySelector('.gl-thumb[data-i="' + S.cur + '"]');
        if (current) {
            current.classList.add("active");
            current.scrollIntoView({block: "nearest", inline: "nearest"});
        }
    }
    function updatePosition(shouldSave) {
        if (posEl) posEl.textContent = pageLabel();
        if (progress) {
            var ratio = S.mode === "strip"
                ? (strip.scrollHeight > strip.clientHeight ? strip.scrollTop / (strip.scrollHeight - strip.clientHeight) : 0)
                : (S.cur + 1) / total;
            progress.style.width = Math.max(0, Math.min(1, ratio)) * 100 + "%";
        }
        markThumb();
        if (shouldSave !== false) savePosition();
    }

    function scrollToCurrent() {
        var target = strip.querySelector('.gl-strip-img[data-i="' + S.cur + '"]');
        if (target) target.scrollIntoView({block: "start"});
    }
    function updateCurrentFromStrip() {
        var center = window.innerHeight * .5;
        var best = 0, distance = Infinity;
        strip.querySelectorAll(".gl-strip-img").forEach(function (image) {
            var rect = image.getBoundingClientRect();
            var distanceToCenter = Math.abs((rect.top + rect.height / 2) - center);
            if (distanceToCenter < distance) {
                distance = distanceToCenter;
                best = Number(image.getAttribute("data-i")) || 0;
            }
        });
        if (best !== S.cur) {
            S.cur = clampIndex(best);
            updatePosition();
        } else {
            updatePosition(false);
        }
    }

    function setStripMode() {
        S.mode = "strip";
        savePref("gallery_mode", S.mode);
        stopAuto();
        if (lightbox && lightbox.pswp) lightbox.pswp.close();
        document.body.classList.remove("pswp-open");
        stage.hidden = true;
        strip.hidden = false;
        if (S._stripRatio != null) {
            requestAnimationFrame(function () {
                var range = strip.scrollHeight - strip.clientHeight;
                if (range > 0) strip.scrollTop = S._stripRatio * range;
                S._stripRatio = null;
                updateCurrentFromStrip();
            });
        } else {
            scrollToCurrent();
            updatePosition();
        }
        renderPrefs();
    }

    function openSingle(index) {
        if (!lightbox) return;
        var open = function () {
            document.body.classList.add("pswp-open");
            lightbox.loadAndOpen(clampIndex(index));
        };
        if (lightbox.pswp) {
            lightbox.pswp.close();
            setTimeout(open, 650);
        } else {
            open();
        }
    }

    function setSingleMode(index) {
        S.mode = "single";
        savePref("gallery_mode", S.mode);
        stage.hidden = true;
        strip.hidden = true;
        stopAuto();
        if (lightbox) {
            openSingle(index);
        } else {
            stage.hidden = true;
            strip.hidden = false;
            scrollToCurrent();
        }
        renderPrefs();
    }

    function next(delta) {
        var nextIndex = S.cur + delta;
        if (nextIndex < 0 || nextIndex >= total) return;
        if (S.mode === "strip") {
            S.cur = nextIndex;
            scrollToCurrent();
            updatePosition();
        } else if (lightbox && lightbox.pswp) {
            lightbox.pswp.goTo(delta);
        } else {
            setSingleMode(nextIndex);
        }
    }

    function startAuto() {
        stopAuto();
        if (!S.autoplay || S.mode !== "single") return;
        autoTimer = setInterval(function () {
            if (S.cur >= total - 1) {
                S.autoplay = false;
                savePref("gallery_auto", false);
                renderPrefs();
                stopAuto();
                return;
            }
            next(1);
        }, S.autoInterval * 1000);
    }
    function stopAuto() {
        if (autoTimer) { clearInterval(autoTimer); autoTimer = null; }
    }

    function renderPrefs() {
        document.querySelectorAll("[data-set]").forEach(function (button) {
            var key = button.getAttribute("data-set");
            var value = button.getAttribute("data-val");
            if (key === "mode") button.classList.toggle("active", value === S.mode);
        });
        var setThumbs = document.getElementById("set-thumbs");
        if (setThumbs) {
            setThumbs.classList.toggle("on", !!S.thumbsOn);
            setThumbs.textContent = S.thumbsOn ? "开" : "关";
        }
        var setAuto = document.getElementById("set-auto");
        if (setAuto) {
            setAuto.classList.toggle("on", !!S.autoplay);
            setAuto.textContent = S.autoplay ? "开" : "关";
        }
        var interval = document.getElementById("auto-interval");
        if (interval) interval.textContent = S.autoInterval + "s";
        if (thumbsBar) thumbsBar.style.display = S.thumbsOn ? "" : "none";
    }

    function toggleFullscreen() {
        if (!document.fullscreenElement && !document.webkitFullscreenElement) {
            var request = document.documentElement.requestFullscreen || document.documentElement.webkitRequestFullscreen;
            if (request) request.call(document.documentElement);
        } else {
            var exit = document.exitFullscreen || document.webkitExitFullscreen;
            if (exit) exit.call(document);
        }
    }

    if (typeof window.PhotoSwipeLightbox === "function" && typeof window.PhotoSwipe === "function") {
        lightbox = new window.PhotoSwipeLightbox({
            gallery: "#pswp-gallery",
            children: "a",
            pswpModule: window.PhotoSwipe,
            loop: false,
            bgOpacity: 1,
            showHideAnimationType: "fade",
            closeOnVerticalDrag: false,
            pinchToClose: false,
            wheelToZoom: true,
            initialZoomLevel: "fit",
            secondaryZoomLevel: "fill",
            maxZoomLevel: "max",
            preload: [0, 1],
            paddingFn: function () { return {top: 116, bottom: S.thumbsOn ? 110 : 22, left: 8, right: 8}; }
        });
        lightbox.on("change", function () {
            if (!lightbox.pswp) return;
            S.cur = clampIndex(lightbox.pswp.currIndex);
            document.body.classList.add("pswp-open");
            updatePosition();
        });
        lightbox.on("close", function () {
            document.body.classList.remove("pswp-open");
            updatePosition(false);
        });
        lightbox.init();
    }

    if (thumbsTrack) {
        thumbsTrack.addEventListener("click", function (event) {
            var thumb = event.target.closest(".gl-thumb");
            if (!thumb) return;
            var index = clampIndex(thumb.getAttribute("data-i"));
            if (S.mode === "strip") {
                S.cur = index;
                scrollToCurrent();
                updatePosition();
            } else {
                setSingleMode(index);
            }
        });
        thumbsTrack.querySelectorAll("img").forEach(function (image, index) {
            image.addEventListener("error", function () {
                if (thumbs[index] && image.src !== new URL(imgs[index], location.href).href) image.src = imgs[index];
            });
        });
    }

    strip.addEventListener("scroll", function () { if (S.mode === "strip") updateCurrentFromStrip(); }, {passive: true});
    strip.addEventListener("click", function (event) {
        if (event.target.closest(".gl-strip-img")) return;
    });

    document.addEventListener("click", function (event) {
        var set = event.target.closest("[data-set]");
        if (set) {
            var key = set.getAttribute("data-set");
            if (key === "mode") {
                if (set.getAttribute("data-val") === "strip") setStripMode();
                else setSingleMode(S.cur);
            }
            return;
        }
        var action = event.target.closest("[data-act]");
        if (action) {
            switch (action.getAttribute("data-act")) {
                case "prev": next(-1); break;
                case "next": next(1); break;
                case "jump":
                    jumpInput.value = S.cur + 1;
                    jumpMask.hidden = false;
                    jumpInput.focus();
                    jumpInput.select();
                    break;
                case "settings": settingsMask.hidden = false; break;
                case "fullscreen": toggleFullscreen(); break;
                case "close-settings": settingsMask.hidden = true; break;
                case "close-jump": jumpMask.hidden = true; break;
                case "go-jump":
                    var target = parseInt(jumpInput.value, 10);
                    if (!isNaN(target)) {
                        S.cur = clampIndex(target - 1);
                        if (S.mode === "strip") { scrollToCurrent(); updatePosition(); }
                        else setSingleMode(S.cur);
                    }
                    jumpMask.hidden = true;
                    break;
                case "toggle-thumbs":
                    S.thumbsOn = !S.thumbsOn;
                    savePref("gallery_thumbs", S.thumbsOn);
                    renderPrefs();
                    break;
                case "toggle-auto":
                    S.autoplay = !S.autoplay;
                    savePref("gallery_auto", S.autoplay);
                    if (S.autoplay) startAuto(); else stopAuto();
                    renderPrefs();
                    break;
                case "auto-slower":
                    S.autoInterval = Math.min(30, S.autoInterval + 1);
                    savePref("gallery_auto_interval", S.autoInterval);
                    startAuto(); renderPrefs();
                    break;
                case "auto-faster":
                    S.autoInterval = Math.max(1, S.autoInterval - 1);
                    savePref("gallery_auto_interval", S.autoInterval);
                    startAuto(); renderPrefs();
                    break;
            }
            return;
        }
        if (event.target.classList.contains("gl-modal-mask")) {
            settingsMask.hidden = true;
            jumpMask.hidden = true;
        }
    });

    document.addEventListener("keydown", function (event) {
        if (event.target === jumpInput) {
            if (event.key === "Enter") document.querySelector('[data-act="go-jump"]').click();
            return;
        }
        if (event.key === "t" || event.key === "T") {
            S.thumbsOn = !S.thumbsOn;
            savePref("gallery_thumbs", S.thumbsOn);
            renderPrefs();
        } else if (event.key === "f" || event.key === "F") {
            toggleFullscreen();
        } else if (event.key === "Escape") {
            settingsMask.hidden = true;
            jumpMask.hidden = true;
        } else if (S.mode === "strip" && event.key === "PageDown") {
            next(1); event.preventDefault();
        } else if (S.mode === "strip" && event.key === "PageUp") {
            next(-1); event.preventDefault();
        }
    });

    restorePosition();
    renderPrefs();
    updatePosition(false);
    if (S.mode === "strip") {
        setStripMode();
    } else {
        setSingleMode(S.cur);
    }
})();
