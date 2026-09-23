/* ===== EPUB 阅读器脚本（static/js/epub_reader.js）=====
   功能：
   - 加载书籍信息和章节目录
   - 章节导航（上一篇/下一篇、键盘快捷键）
   - 目录面板展开/折叠
   - 阅读进度保存到 localStorage
   - 内嵌资源 URL 重写（图片/CSS 等）
*/

(function () {
    // ── DOM 引用 ──
    var tocList = document.getElementById("toc-list");
    var chapterContent = document.getElementById("chapter-content");
    var loadingEl = document.getElementById("epub-loading");
    var emptyEl = document.getElementById("epub-empty");
    var chapterTitle = document.getElementById("chapter-title");
    var progressEl = document.getElementById("progress");
    var prevBtn = document.getElementById("prev-chapter");
    var nextBtn = document.getElementById("next-chapter");
    var tocToggleBtn = document.getElementById("toc-toggle-btn");
    var tocPanel = document.getElementById("epub-toc");
    var tocOverlay = document.getElementById("epub-toc-overlay");
    var tocCloseBtn = document.getElementById("toc-close-btn");
    var topbarTitle = document.getElementById("topbar-book-title");
    var readingArea = document.getElementById("epub-reading-area");

    // ── 状态 ──
    var bookInfo = null;          // 书籍元数据
    var chapters = [];            // 章节列表
    var currentIndex = -1;        // 当前章节索引
    var currentChapterId = null;  // 当前章节 ID
    var filePath = "";            // 文件路径（用于 localStorage 键）
    var apiBase = "";             // API 基础路径

    // ── 初始化 ──
    function init() {
        filePath = window.EPUB_CONFIG.filePath;
        apiBase = "/epub/api";

        // 绑定点事件
        prevBtn.addEventListener("click", function () { goChapter(-1); });
        nextBtn.addEventListener("click", function () { goChapter(1); });
        tocToggleBtn.addEventListener("click", toggleToc);
        if (tocCloseBtn) tocCloseBtn.addEventListener("click", closeToc);
        if (tocOverlay) tocOverlay.addEventListener("click", closeToc);

        // 键盘快捷键
        document.addEventListener("keydown", handleKey);

        // 加载书籍信息
        loadBookInfo();
    }

    // ── 加载书籍信息 ──
    function loadBookInfo() {
        showLoading();
        fetch(apiBase + "/info/" + encodeURIComponent(filePath))
            .then(function (r) {
                if (!r.ok) throw new Error("HTTP " + r.status);
                return r.json();
            })
            .then(function (data) {
                if (data.error) throw new Error(data.error);
                bookInfo = data;
                chapters = data.chapters || [];
                topbarTitle.textContent = data.title || "EPUB 阅读器";
                document.title = data.title || "EPUB 阅读器";

                if (chapters.length === 0) {
                    showEmpty("该书没有目录信息", "请尝试使用其他阅读器打开");
                    return;
                }

                buildToc();
                // 恢复阅读进度或从第一章开始
                var savedId = loadProgress();
                var startIndex = 0;
                if (savedId) {
                    for (var i = 0; i < chapters.length; i++) {
                        if (chapters[i].id === savedId) {
                            startIndex = i;
                            break;
                        }
                    }
                }
                loadChapter(startIndex);
            })
            .catch(function (err) {
                showEmpty("无法加载书籍信息", err.message);
            });
    }

    // ── 构建目录 ──
    function buildToc() {
        tocList.innerHTML = "";
        chapters.forEach(function (ch, index) {
            var btn = document.createElement("button");
            btn.className = "toc-item";
            btn.textContent = ch.title || "第 " + (index + 1) + " 章";
            btn.title = ch.title;
            btn.addEventListener("click", function () {
                loadChapter(index);
                closeToc();
            });
            // 保存章节索引到 dataset
            btn.dataset.index = index;
            tocList.appendChild(btn);
        });
    }

    // ── 加载章节 ──
    function loadChapter(index) {
        if (index < 0 || index >= chapters.length) return;
        if (index === currentIndex && chapterContent.innerHTML) return;

        showLoading();
        currentIndex = index;
        currentChapterId = chapters[index].id;

        fetch(apiBase + "/chapter/" + encodeURIComponent(filePath) + "/" + encodeURIComponent(currentChapterId))
            .then(function (r) {
                if (!r.ok) throw new Error("HTTP " + r.status);
                return r.json();
            })
            .then(function (data) {
                if (data.error) throw new Error(data.error);
                renderChapter(data.content, data.href);
                updateNav();
                highlightTocItem();
                saveProgress();
                // 滚动到顶部
                readingArea.scrollTop = 0;
            })
            .catch(function (err) {
                chapterContent.textContent = "加载章节失败：" + err.message;
                chapterContent.classList.add("chapter-error");
                hideLoading();
                updateNav();
            });
    }

    // ── 渲染章节内容 ──
    function renderChapter(html, chapterHref) {
        chapterContent.classList.remove("chapter-error");
        // 重写内嵌资源 URL（图片、CSS 等），指向 /epub/api/resource/...
        var baseDir = chapterHref ? chapterHref.substring(0, chapterHref.lastIndexOf("/") + 1) : "";

        // 创建临时 DOM 来安全处理 HTML
        var temp = document.createElement("div");
        temp.innerHTML = html;

        // 重写图片 src
        var imgs = temp.querySelectorAll("img");
        for (var i = 0; i < imgs.length; i++) {
            var src = imgs[i].getAttribute("src");
            if (src && !src.match(/^(https?:|data:|#)/i)) {
                var resolved = resolveRelativePath(baseDir, src);
                imgs[i].setAttribute("src", apiBase + "/resource/" + encodeURIComponent(filePath) + "/" + encodeURIComponent(resolved));
            }
        }

        // 重写 image 元素的 xlink:href（SVG）
        var images = temp.querySelectorAll("image");
        for (var j = 0; j < images.length; j++) {
            var href = images[j].getAttribute("xlink:href") || images[j].getAttribute("href");
            if (href && !href.match(/^(https?:|data:|#)/i)) {
                var resolvedHref = resolveRelativePath(baseDir, href);
                images[j].setAttribute("href", apiBase + "/resource/" + encodeURIComponent(filePath) + "/" + encodeURIComponent(resolvedHref));
            }
        }

        // 移除 EPUB 内联的 CSS link（避免污染页面），但保留 style 标签
        var links = temp.querySelectorAll("link[rel='stylesheet']");
        for (var k = 0; k < links.length; k++) {
            links[k].remove();
        }

        chapterContent.innerHTML = temp.innerHTML;
        hideLoading();
    }

    // ── 解析相对路径 ──
    function resolveRelativePath(base, rel) {
        if (!base) return rel;
        // 处理 ../ 返回上级目录
        var parts = base.split("/").filter(Boolean);
        var relParts = rel.split("/");
        for (var i = 0; i < relParts.length; i++) {
            if (relParts[i] === "..") {
                if (parts.length > 0) parts.pop();
            } else if (relParts[i] !== ".") {
                parts.push(relParts[i]);
            }
        }
        return parts.join("/");
    }

    // ── 更新导航按钮状态 ──
    function updateNav() {
        prevBtn.disabled = currentIndex <= 0;
        nextBtn.disabled = currentIndex >= chapters.length - 1;

        var ch = chapters[currentIndex];
        chapterTitle.textContent = ch ? (ch.title || "第 " + (currentIndex + 1) + " 章") : "";
        progressEl.textContent = (currentIndex + 1) + " / " + chapters.length;
    }

    // ── 高亮当前目录项 ──
    function highlightTocItem() {
        var items = tocList.querySelectorAll(".toc-item");
        for (var i = 0; i < items.length; i++) {
            items[i].classList.toggle("active", parseInt(items[i].dataset.index) === currentIndex);
        }
    }

    // ── 章节导航 ──
    function goChapter(delta) {
        var newIndex = currentIndex + delta;
        if (newIndex >= 0 && newIndex < chapters.length) {
            loadChapter(newIndex);
        }
    }

    // ── 键盘快捷键 ──
    function handleKey(e) {
        // 如果焦点在输入框内，不处理快捷键
        if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA" || e.target.isContentEditable) {
            return;
        }
        switch (e.key) {
            case "ArrowLeft":
                e.preventDefault();
                goChapter(-1);
                break;
            case "ArrowRight":
                e.preventDefault();
                goChapter(1);
                break;
            case "m":
                // 切换目录面板
                if (!e.ctrlKey && !e.metaKey && !e.altKey) {
                    toggleToc();
                }
                break;
        }
    }

    // ── 目录面板切换 ──
    function toggleToc() {
        var isMobile = window.innerWidth <= 1024;
        if (isMobile) {
            // 移动端：全屏覆盖
            var isOpen = tocPanel.classList.contains("open");
            if (isOpen) {
                closeToc();
            } else {
                tocPanel.classList.add("open");
                if (tocOverlay) tocOverlay.classList.add("show");
            }
        } else {
            // 桌面端：侧边栏折叠
            tocPanel.classList.toggle("collapsed");
        }
    }

    function closeToc() {
        tocPanel.classList.remove("open");
        if (tocOverlay) tocOverlay.classList.remove("show");
    }

    // ── 加载 / 保存阅读进度 ──
    function loadProgress() {
        var serverProgress = window.EPUB_CONFIG.initialProgress;
        if (serverProgress && serverProgress.kind === "chapter" && serverProgress.locator) {
            return serverProgress.locator;
        }
        try {
            var key = "epub_progress_" + filePath;
            return localStorage.getItem(key);
        } catch (e) {
            return null;
        }
    }

    function saveProgress() {
        try {
            var key = "epub_progress_" + filePath;
            localStorage.setItem(key, currentChapterId);
        } catch (e) {
            // 存储不可用时仍继续使用服务端同步。
        }
        if (window.Personal && currentIndex >= 0) {
            window.Personal.reportProgress({
                path: filePath,
                kind: "chapter",
                position: currentIndex + 1,
                total: chapters.length,
                locator: currentChapterId,
                completed: currentIndex >= chapters.length - 1
            });
        }
    }

    // ── UI 状态 ──
    function showLoading() {
        loadingEl.hidden = false;
        emptyEl.hidden = true;
        chapterContent.innerHTML = "";
    }

    function hideLoading() {
        loadingEl.hidden = true;
        emptyEl.hidden = true;
    }

    function showEmpty(title, desc) {
        loadingEl.hidden = true;
        emptyEl.hidden = false;
        emptyEl.querySelector(".empty-title").textContent = title || "无法加载";
        emptyEl.querySelector(".empty-desc").textContent = desc || "";
    }

    // ── 启动 ──
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();