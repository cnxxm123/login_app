// ===== 通用下载确认：所有页面共用 =====
        // main.html（.fc-dl）、search.html（.file-dl）、view.html（[data-download-confirm]）
        // 点击下载链接先弹自绘确认框（沙箱 iframe 禁用了原生 confirm），确认后才跳转下载。
        // 本脚本自包含弹窗 DOM，不依赖各页面是否引入 main.js（style 复用 common.css 的弹窗类）。
        (function () {
            var mask = null;  // 懒创建弹窗遮罩（只建一次）

            function ensureMask() {
                if (mask) return mask;
                mask = document.createElement("div");
                mask.className = "modal-mask";
                mask.id = "dl-confirm-mask";
                mask.hidden = true;
                mask.innerHTML = '<div class="modal-box">'
                    + '<div class="modal-title" id="dl-title"></div>'
                    + '<div class="modal-msg" id="dl-msg"></div>'
                    + '<div class="modal-ops">'
                    + '<button class="modal-cancel" id="dl-cancel" type="button">取消</button>'
                    + '<button class="modal-ok" id="dl-ok" type="button">开始下载</button>'
                    + '</div></div>';
                document.body.appendChild(mask);
                return mask;
            }

            // 弹出确认框，resolve(true)=确认，resolve(false)=取消/点遮罩
            function ask(label) {
                return new Promise(function (resolve) {
                    var m = ensureMask();
                    document.getElementById("dl-title").textContent = "下载确认";
                    document.getElementById("dl-msg").textContent = "确定要" + label + "吗？";
                    function close(v) { m.hidden = true; resolve(v); }
                    document.getElementById("dl-ok").onclick = function () { close(true); };
                    document.getElementById("dl-cancel").onclick = function () { close(false); };
                    m.onclick = function (e) { if (e.target === m) close(false); };
                    m.hidden = false;
                });
            }

            // 拦截下载链接：提示文案取 data-download-confirm > aria-label > 默认"下载"
            var links = document.querySelectorAll(".fc-dl, .file-dl, [data-download-confirm]");
            links.forEach(function (el) {
                el.addEventListener("click", function (e) {
                    e.preventDefault();
                    var url = this.getAttribute("href");
                    var label = this.getAttribute("data-download-confirm")
                        || this.getAttribute("aria-label") || "下载";
                    ask(label).then(function (ok) { if (ok) location.href = url; });
                });
            });
        })();