        // ===== 阅读进度条：随滚动填充顶部细线 =====
        (function () {
            var bar = document.getElementById("reading-bar");
            if (!bar) return;
            function update() {
                var h = document.documentElement;
                var max = h.scrollHeight - h.clientHeight;
                bar.style.width = (max > 0 ? Math.min(window.scrollY / max, 1) * 100 : 0) + "%";
            }
            window.addEventListener("scroll", update, { passive: true });
            window.addEventListener("resize", update);
            update();
        })();
        // ===== 图片阅读器：单页/长条切换、翻页、缩放、全屏、记忆位置 =====
        // imgs：本目录所有图片的访问地址（后端传入 image_urls），翻页即在其中切换
        var imgs = window.VIEW_CONFIG.imageUrls;
        var reader = document.getElementById("reader-single");
        var strip = document.getElementById("img-strip");  // 长条模式容器（setMode 切换显隐用）
        if (reader) {
            var currentUrl = window.VIEW_CONFIG.currentUrl;
            // 按"所在目录"记忆阅读位置：下次重开同一文件时继续上次那一张
            var posKey = "img_pos_" + window.VIEW_CONFIG.parent;
            var saved = JSON.parse(localStorage.getItem(posKey) || "null");
            var cur = 0;
            if (saved && saved.path === currentUrl && saved.index >= 0 && saved.index < imgs.length) {
                cur = saved.index;              // 重开同一个文件 → 继续上次位置
            } else {
                cur = imgs.indexOf(currentUrl); // 新点开 → 从当前文件开始
                if (cur < 0) cur = 0;
            }
            var scale = 1;
            // 阅读模式：每次打开图片一律默认单页模式
            var mode = "single";

            function show(i) {
                if (!imgs.length) return;
                cur = Math.max(0, Math.min(imgs.length - 1, i));
                var img = document.getElementById("reader-img");
                img.src = imgs[cur];
                img.style.transform = ""; scale = 1;      // 换页时重置缩放
                document.getElementById("reader-pos").textContent = (cur + 1) + " / " + imgs.length;
                // 记忆：保存"位置 + 当前图片地址"，重开该文件时据此续读
                localStorage.setItem(posKey, JSON.stringify({ index: cur, path: imgs[cur] }));
            }
            function go(d) { show(cur + d); }  // d=-1 上一张，d=1 下一张
            // 判断当前处于哪种模式：直接用"哪个容器当前可见"来判断。
            // 不用 mode 变量，避免 localStorage/状态不同步时缩放、全屏作用到错误的容器。
            function currentContainer() {
                return strip.hidden ? reader : strip;  // 长条隐藏 → 单页；否则 → 长条
            }
            // 把当前缩放值应用到"当前模式"的容器：
            //   单页模式 → 作用于当前那张图；长条模式 → 作用于整条（全部图片一起缩放）
            function applyZoom() {
                var el = (mode === "single") ? document.getElementById("reader-img") : strip;
                el.style.transform = (scale === 1) ? "" : "scale(" + scale + ")";
            }
            function zoom(d) {
                scale = Math.min(3, Math.max(0.5, +(scale + d).toFixed(2)));  // 限制 0.5x~3x
                applyZoom();
            }
            function zoomReset() { scale = 1; applyZoom(); }
            // 全屏：单页模式全屏单页容器；长条模式全屏整条容器。
            // 用 currentContainer() 判断（不依赖 mode 变量），并兼容老浏览器 webkit 前缀。
            function toggleFullscreen() {
                var el = currentContainer();
                if (!document.fullscreenElement && !document.webkitFullscreenElement) {
                    var req = el.requestFullscreen || el.webkitRequestFullscreen;  // 老 Chrome/Safari 用 webkit 前缀
                    if (req) req.call(el);
                } else if (document.exitFullscreen) {
                    document.exitFullscreen();
                } else if (document.webkitExitFullscreen) {
                    document.webkitExitFullscreen();
                }
            }
            // 长条模式：滚动定位到当前图片（.img-item 顺序与 imgs 一致，索引即 cur）
            function scrollToCurrent() {
                var items = strip.querySelectorAll(".img-item");
                if (items[cur]) items[cur].scrollIntoView({ block: "start" });
            }
            function setMode(m) {
                mode = m;
                document.getElementById("mode-single").classList.toggle("active", m === "single");
                document.getElementById("mode-strip").classList.toggle("active", m === "strip");
                reader.hidden = m !== "single";   // 单页模式显示单页容器
                strip.hidden = m !== "strip";     // 长条模式显示长条容器
                applyZoom();                      // 先把缩放应用到切换后的容器，再定位滚动（transform 不影响布局坐标）
                if (m === "single") { show(cur); }      // 切回单页时刷新当前页
                else if (m === "strip") { scrollToCurrent(); }  // 切到长条时定位到当前图片
            }
            // 键盘快捷键：+/- 缩放、0 重置、F 全屏在两种模式都生效；
            // 翻页（←/→ 等）仅在单页模式生效，长条模式下方向键留给页面滚动
            document.addEventListener("keydown", function (e) {
                var tag = (e.target.tagName || "").toLowerCase();
                if (tag === "input" || tag === "textarea") return;  // 输入框里不拦截
                if (e.key === "+" || e.key === "=") { zoom(0.2); e.preventDefault(); return; }
                if (e.key === "-" || e.key === "_") { zoom(-0.2); e.preventDefault(); return; }
                if (e.key === "0") { zoomReset(); e.preventDefault(); return; }
                if (e.key.toLowerCase() === "f") { toggleFullscreen(); e.preventDefault(); return; }
                if (!reader.hidden) {
                    if (e.key === "ArrowLeft" || e.key === "ArrowUp" || e.key === "PageUp") { go(-1); e.preventDefault(); }
                    else if (e.key === "ArrowRight" || e.key === "ArrowDown" || e.key === "PageDown" || e.key === " ") { go(1); e.preventDefault(); }
                }
            });
            show(cur);
            setMode(mode);
        }

        // ===== 文档目录（TOC）：解析 .md-body 的标题生成侧边导航 =====
        (function () {
            var body = document.querySelector(".md-body");
            var toggle = document.getElementById("toc-toggle");
            var panel = document.getElementById("toc-panel");
            if (!body || !toggle || !panel) return;
            var headings = body.querySelectorAll("h1, h2, h3");  // 只收前三级标题
            if (!headings.length) return;
            headings.forEach(function (h, i) {
                if (!h.id) h.id = "toc-h" + i;  // 给标题补 id，供锚点跳转
            });
            var ul = document.createElement("ul");
            headings.forEach(function (h, i) {
                var li = document.createElement("li");
                li.className = "toc-" + h.tagName.toLowerCase();  // toc-h1 / toc-h2 / toc-h3（缩进）
                var a = document.createElement("a");
                a.textContent = h.textContent;
                a.href = "#" + h.id;
                a.addEventListener("click", function (e) {
                    e.preventDefault();
                    h.scrollIntoView({ behavior: "smooth", block: "start" });  // 平滑滚动到标题
                });
                li.appendChild(a);
                ul.appendChild(li);
            });
            document.getElementById("toc-list").appendChild(ul);
            toggle.hidden = false;  // 有标题才显示"目录"按钮
            toggle.addEventListener("click", function () {
                panel.hidden = !panel.hidden;  // 点击切换面板显隐
            });
        })();

        // ===== "已保存"提示：保存编辑后跳转回来时（URL 带 saved=1）短暂显示 =====
        (function () {
            if (new URLSearchParams(location.search).get("saved") !== "1") return;
            var t = document.createElement("div");
            t.className = "save-toast";
            t.textContent = "已保存";
            document.body.appendChild(t);
            setTimeout(function () { t.classList.add("hide"); }, 1800);  // 1.8s 后淡出
            setTimeout(function () { t.remove(); }, 2400);               // 2.4s 后移除
        })();

        // ===== 音视频连播：整目录同类媒体自动连播（播放结束切下一首/集）=====
        (function () {
            var playlist = window.VIEW_CONFIG.playlist;   // 后端传入的目录媒体列表（含签名令牌 URL）
            var player = document.getElementById("media-player");
            if (!player || !playlist.length) return;  // 非音视频页面 / 目录没有同类媒体 → 跳过
            var pIndex = window.VIEW_CONFIG.playlistIndex;        // 当前文件在列表中的下标

            // 渲染播放列表（视频页为右侧"接下来播放"，带缩略图；音频页为原生列表）
            var list = document.getElementById("pl-list");
            var count = document.getElementById("pl-count");  // 列表标题里的"共 N 项"
            if (count) count.textContent = "共 " + playlist.length + " 项";
            // 面板标题里追加总数（音频/视频共用同一个 <span>，去掉旧括号内容避免重复）
            var headTitle = document.querySelector("#pl-head span");
            if (headTitle) headTitle.textContent = headTitle.textContent.split("（")[0] + "（" + playlist.length + " 项）";
            playlist.forEach(function (item, i) {
                var btn = document.createElement("button");
                btn.type = "button";
                btn.className = "pl-item" + (i === pIndex ? " active" : "");
                // 视频：左侧缩略图（media.thumb 抽帧）；音频无封面
                if (item.thumb) {
                    var thumb = document.createElement("span");
                    thumb.className = "pl-thumb";
                    var img = document.createElement("img");
                    img.src = item.thumb;
                    img.alt = "";
                    img.loading = "lazy";
                    thumb.appendChild(img);
                    btn.appendChild(thumb);
                } else {
                    var idx = document.createElement("span");
                    idx.className = "pl-idx"; idx.textContent = (i + 1) + ".";
                    btn.appendChild(idx);
                }
                var name = document.createElement("span");
                name.className = "pl-name"; name.textContent = item.name;
                btn.appendChild(name);
                btn.addEventListener("click", function () { playAt(i); });
                list.appendChild(btn);
            });

            // 高亮当前项，并滚动到可见位置（列表长时保证当前项不跑出视口）
            function updateActive() {
                list.querySelectorAll(".pl-item").forEach(function (el, i) {
                    el.classList.toggle("active", i === pIndex);
                });
                var cur = list.querySelector(".pl-item.active");
                if (cur) cur.scrollIntoView({ block: "nearest" });
            }

            // 切到第 i 项：更新 src 并播放；越界时循环（最后一首结束回到第一首）
            function playAt(i) {
                if (i < 0) i = playlist.length - 1;
                if (i >= playlist.length) i = 0;
                pIndex = i;
                player.src = playlist[i].url;   // 每项 URL 已带独立签名令牌
                player.play().catch(function () {});  // 自动播放被浏览器拦截时静默（用户可手动点播放）
                document.title = playlist[i].name;    // 标题跟随当前播放项
                var titleEl = document.getElementById("vp-title");  // 视频页标题（B 站式）
                if (titleEl) titleEl.textContent = playlist[i].name;
                var meta = document.querySelector(".meta span:last-child");  // 音频页兜底
                if (meta) meta.textContent = playlist[i].name;
                updateActive();
            }

            // 播放结束（ended 事件）自动切下一项 → 实现"整目录连播"
            player.addEventListener("ended", function () { playAt(pIndex + 1); });

            // 工具条按钮：上一首/下一首、展开/收起播放列表（音频页）
            window.plGo = function (d) { playAt(pIndex + d); };
            window.togglePlaylist = function () {
                var panel = document.getElementById("pl-panel");
                var head = document.getElementById("pl-head");
                if (!panel) return;
                panel.hidden = !panel.hidden;
                if (head) head.classList.toggle("open", !panel.hidden);
            };
        })();
