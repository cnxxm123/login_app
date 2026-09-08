        // ===== 通用弹窗 =====
        // 沙箱预览 iframe 禁用了 prompt/confirm/alert，用自绘弹窗代替。
        // 输入模式：确认 resolve 输入值（去首尾空格），取消/点遮罩 resolve null；
        // 纯提示/确认模式：确认 resolve true，取消 resolve false。
        function openModal(opts) {
            return new Promise(function (resolve) {
                var mask = document.getElementById("modal-mask");
                var input = document.getElementById("modal-input");
                var isInput = !!opts.input;
                document.getElementById("modal-title").textContent = opts.title || "提示";
                var msgEl = document.getElementById("modal-msg");
                if (opts.html) { msgEl.innerHTML = opts.message || ""; }  // html 模式：支持 <br>/<b> 排版
                else { msgEl.textContent = opts.message || ""; }
                input.hidden = !isInput;
                if (isInput) {
                    input.value = opts.value || "";
                    input.placeholder = opts.placeholder || "";
                }
                document.getElementById("modal-ok").textContent = opts.okText || "确定";
                document.getElementById("modal-cancel").textContent = opts.cancelText || "取消";
                function close() { mask.hidden = true; }
                document.getElementById("modal-ok").onclick = function () {
                    close(); resolve(isInput ? input.value.trim() : true);
                };
                document.getElementById("modal-cancel").onclick = function () {
                    close(); resolve(isInput ? null : false);
                };
                mask.onclick = function (e) { if (e.target === mask) { close(); resolve(isInput ? null : false); } };
                mask.hidden = false;
                if (isInput) { input.focus(); input.select(); }
            });
        }
        // 轻提示：复用弹窗做纯提示（沙箱禁用 alert）
        function notify(msg) {
            openModal({ title: "提示", message: msg, okText: "知道了" });
        }

        // ===== 上传提醒：点击"上传"时弹窗确认本次文件数与大小 =====
        // 限制值由后端 config.py 传入（不写死在页面），改了 config 两侧自动一致。
        var UPLOAD_MAX_PARTS = window.MAIN_CONFIG.maxParts;
        var UPLOAD_MAX_BYTES = window.MAIN_CONFIG.maxBytes;
        function formatSize(bytes) {
            if (bytes >= 1073741824) return (bytes / 1073741824).toFixed(2) + " GB";
            if (bytes >= 1048576) return (bytes / 1048576).toFixed(1) + " MB";
            if (bytes >= 1024) return (bytes / 1024).toFixed(1) + " KB";
            return bytes + " B";
        }
        // 弹"上传确认"：显示本次文件数/总大小与上限；超限时禁止继续（服务端同样会 413）。
        // files 是 FileList/数组，用 length 与 size。resolve(true)=继续，resolve(false)=放弃。
        function confirmUpload(files) {
            var n = files.length, total = 0;
            for (var i = 0; i < n; i++) total += files[i].size || 0;
            var overParts = n > UPLOAD_MAX_PARTS, overBytes = total > UPLOAD_MAX_BYTES;
            var msg = "本次将上传 <b>" + n + "</b> 个文件，共 <b>" + formatSize(total) + "</b>。<br>"
                + "当前上限：单次最多 " + UPLOAD_MAX_PARTS + " 个文件、总大小 "
                + formatSize(UPLOAD_MAX_BYTES) + "（单个文件无大小上限）。";
            if (overParts || overBytes) {
                var why = overParts ? "文件数超过上限" : "总大小超过上限";
                return openModal({ title: "超出上传上限", html: true, okText: "知道了",
                    message: msg + "<br><b style=\"color:#ef4444\">本次已超过上限（" + why + "），无法上传。</b>" })
                    .then(function () { return false; });
            }
            return openModal({ title: "上传确认", html: true, okText: "继续上传",
                message: msg + "<br>确定开始上传？" });
        }
        // ===== 上传进度条：用 XMLHttpRequest 提交 FormData，监听 upload.onprogress 显示进度。
        // fetch 无法获取上传进度，故改用 XHR；进度条弹窗可中途取消（abort）。
        // 上传完成：服务端返回 302 重定向到上级目录，XHR 会自动跟随，
        // 最终用 responseURL（跟随后的最终地址）跳转刷新页面。 =====
        function uploadWithProgress(fd) {
            return new Promise(function (resolve) {
                var mask = document.getElementById("progress-mask");
                var fill = document.getElementById("progress-fill");
                var info = document.getElementById("progress-info");
                var fileEl = document.getElementById("progress-file");
                var cancelBtn = document.getElementById("progress-cancel");
                var xhr = new XMLHttpRequest();
                var n = fd.getAll("files").length;  // 本次上传的文件数
                fileEl.textContent = "共 " + n + " 个文件";
                fill.style.width = "0%";
                info.textContent = "正在连接…";
                mask.hidden = false;
                var settled = false;  // 防止完成后再触发其它回调重复关闭弹窗
                function finish() { if (!settled) { settled = true; mask.hidden = true; resolve(); } }
                cancelBtn.onclick = function () { xhr.abort(); };  // abort 会触发下方 onabort
                xhr.upload.onprogress = function (e) {
                    if (!e.lengthComputable) { info.textContent = "已上传 " + formatSize(e.loaded); return; }
                    var pct = Math.round(e.loaded / e.total * 100);
                    fill.style.width = pct + "%";
                    info.textContent = formatSize(e.loaded) + " / " + formatSize(e.total) + "（" + pct + "%）";
                };
                xhr.onload = function () {
                    finish();
                    if (xhr.status >= 200 && xhr.status < 300) {
                        location.href = xhr.responseURL || location.href;  // 跟随重定向到刷新后的目录页
                    } else if (xhr.status === 413) {
                        notify("上传失败：请求超出服务端大小上限");
                    } else {
                        notify("上传失败（状态码 " + xhr.status + "）");
                    }
                };
                xhr.onerror = function () { finish(); notify("上传失败：网络错误"); };
                // 取消后刷新目录：正常情况下服务端已回滚到原状，刷新只是恢复一致；
                // 也覆盖"请求体恰好已收完、文件实际已落盘"的边界竞态，避免列表过期。
                xhr.onabort = function () { finish(); location.reload(); };
                xhr.open("POST", window.MAIN_CONFIG.urls.upload);
                xhr.send(fd);
            });
        }
        // 普通文件上传：选择文件后弹"上传确认"，确认后改用 XHR 上传以显示进度条
        (function () {
            var fileInput = document.getElementById("file-input");
            if (!fileInput) return;
            fileInput.addEventListener("change", function () {
                var files = this.files;
                if (!files.length) return;
                confirmUpload(files).then(function (ok) {
                    if (!ok) { fileInput.value = ""; return; }  // 取消：清空选择，允许重选相同文件
                    var fd = new FormData();
                    for (var i = 0; i < files.length; i++) fd.append("files", files[i]);
                    uploadWithProgress(fd);  // XHR 上传，显示进度条
                });
            });
        })();

        // ===== 上传菜单：单个"上传"按钮弹出 上传文件/上传文件夹/新建文件夹 =====
        // 页面头部（桌面端）与顶部应用栏（移动端，nav.html 注入）各有一个菜单，
        // 共用同一套函数：由点击的按钮就近定位所属菜单的弹出层。
        (function () {
            var menus = document.querySelectorAll(".up-menu");
            if (!menus.length) return;
            window.toggleUpMenu = function (btn, e) {
                if (e) e.stopPropagation();
                var pop = btn.parentNode.querySelector(".up-pop");
                pop.hidden = !pop.hidden;
            };
            window.closeUpMenu = function (btn) {
                btn.closest(".up-menu").querySelector(".up-pop").hidden = true;
            };
            // 点击菜单外任意位置关闭
            document.addEventListener("click", function (e) {
                menus.forEach(function (m) {
                    var pop = m.querySelector(".up-pop");
                    if (!pop.hidden && !m.contains(e.target)) pop.hidden = true;
                });
            });
            window.pickFiles = function (btn) {
                closeUpMenu(btn);
                document.getElementById("file-input").click();
            };
            window.pickFolder = function (btn) {
                closeUpMenu(btn);
                document.getElementById("dir-input").click();
            };
        })();

        // 新建文件夹：弹窗输入名称 → POST /mkdir/<当前目录>
        function mkdirItem() {
            openModal({ title: "新建文件夹", message: "输入新文件夹名称：", input: true, placeholder: "文件夹名称", okText: "创建" })
                .then(function (name) {
                    if (!name) return;
                    var fd = new FormData();
                    fd.append("new_folder", name);
                    fetch(window.MAIN_CONFIG.urls.mkdir, { method: "POST", body: fd })
                        .then(function (r) {
                            if (r.redirected) { location.href = r.url; return; }
                            if (r.ok) { location.reload(); }
                            else if (r.status === 409) { notify("已存在同名文件/文件夹"); }
                            else { notify("新建文件夹失败"); }
                        });
                });
        }

        // ===== 上传文件夹：整棵目录树的所有文件都在 input.files 里，
        // 每个文件带 webkitRelativePath（如 "漫画/第1话/001.jpg"）。
        // 用 FormData 把相对路径作为上传文件名提交，后端据此逐级建目录还原结构。 =====
        (function () {
            var dirInput = document.getElementById("dir-input");
            var dirItems = document.querySelectorAll(".up-dir-item");
            if (!dirInput || !dirItems.length) return;

            // 特性检测：webkitdirectory 并非所有浏览器真正支持。
            // 1) 属性不存在（部分老浏览器/安卓内置浏览器）→ 不支持；
            // 2) iOS Safari/Chrome：属性"存在"但苹果文件选择器没有
            //    "文件夹"选项，点了还是只能选文件；
            // 3) 小米自带浏览器（MiuiBrowser）：基于 Chromium，属性存在、
            //    点击也有反应，但文件选择器同样不提供"选择文件夹"，
            //    只能选文件 → 一并按不支持处理。
            var iOS = /iPad|iPhone|iPod/.test(navigator.userAgent)
                || (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);  // iPadOS 13+ 伪装成 Mac
            var isMiuiBrowser = /MiuiBrowser/i.test(navigator.userAgent);  // 小米自带浏览器
            var supported = "webkitdirectory" in HTMLInputElement.prototype && !iOS && !isMiuiBrowser;
            if (!supported) {
                // 不支持时隐藏所有"上传文件夹"入口（其余上传功能不受影响）
                dirItems.forEach(function (el) { el.remove(); });
                dirInput.remove();
                return;
            }

            dirInput.addEventListener("change", function () {
                var files = this.files;
                if (!files.length) return;
                // 先弹"上传确认"（显示文件数/总大小与上限），确认后才打包提交
                confirmUpload(files).then(function (ok) {
                    if (!ok) { dirInput.value = ""; return; }  // 取消：清空选择，允许重选相同文件夹
                    var fd = new FormData();
                    for (var i = 0; i < files.length; i++) {
                        // webkitRelativePath 为空（个别浏览器）时退回普通文件名
                        var rel = files[i].webkitRelativePath || files[i].name;
                        fd.append("files", files[i], rel);
                    }
                    uploadWithProgress(fd);  // XHR 上传，显示进度条
                });
            });
        })();

        // ===== 视频时长：逐个拉取 /duration 接口，把时长渲染成缩略图右下角角标 =====
        (function () {
            var badges = document.querySelectorAll(".fc-dur");
            if (!badges.length) return;

            // 相对路径逐段 encode，避免文件名里的特殊字符破坏 URL
            function encPath(p) { return p.split("/").map(encodeURIComponent).join("/"); }
            // 秒 → "H:MM:SS" 或 "MM:SS"
            function fmtDur(s) {
                s = Math.round(s);
                var h = Math.floor(s / 3600),
                    m = Math.floor((s % 3600) / 60),
                    sec = s % 60,
                    pad = function (n) { return n < 10 ? "0" + n : "" + n; };
                return h ? h + ":" + pad(m) + ":" + pad(sec) : m + ":" + pad(sec);
            }

            var base = window.MAIN_CONFIG.urls.duration;
            // 并发上限 4：冷缓存时避免一次起太多 ffmpeg 拖慢页面。
            // 注意：不能用 var 声明循环里的 b —— var 是函数作用域，所有异步回调
            // 会共享同一个 b，等 fetch 返回时 b 已指向最后启动的那个角标，
            // 导致前几个视频的时长永远写不进去。这里用 IIFE 把 b 锁进各自闭包。
            var idx = 0, running = 0;
            function next() {
                while (running < 4 && idx < badges.length) {
                    (function (b) {
                        var p = b.getAttribute("data-path");
                        if (!p) { return; }  // 无路径直接跳过，不占用并发槽位
                        running++;
                        fetch(base + encPath(p))
                            .then(function (r) { return r.json(); })
                            .then(function (d) {
                                if (d && typeof d.duration === "number" && d.duration > 0) {
                                    b.textContent = fmtDur(d.duration);
                                    b.classList.add("show");
                                }
                            })
                            .catch(function () {})
                            .then(function () { running--; next(); });
                    })(badges[idx++]);
                }
            }
            next();
        })();