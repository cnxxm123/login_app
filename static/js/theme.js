/* ===== 公共主题切换脚本（static/js/theme.js）=====
   深色/浅色主题：本地记住选择（localStorage.theme），未设置时跟随系统。
   所有页面共用同一套逻辑，避免在每个模板里重复粘贴。

   用法：
   1. <head> 里引入：<script src="{{ url_for('static', filename='js/theme.js') }}"></script>
      （放在 </body> 前也行，保证 .theme-toggle 按钮已存在于 DOM）
   2. 页面里放一个按钮：<button class="theme-toggle" type="button" onclick="toggleTheme()">切换主题</button>
   3. 暗色样式通过 body.dark 覆盖实现（见 common.css / 各模板私有样式）。
*/
(function () {
    // 读取偏好；未设置过则跟随系统（prefers-color-scheme）
    var saved = localStorage.getItem("theme");
    var dark = saved ? saved === "dark"
                     : window.matchMedia("(prefers-color-scheme: dark)").matches;
    document.body.classList.toggle("dark", dark);
})();

// 供 onclick="toggleTheme()" 调用：切换 body.dark 并记住选择
function toggleTheme() {
    var dark = document.body.classList.toggle("dark");
    localStorage.setItem("theme", dark ? "dark" : "light");
}

/* ===== 通用 UI 组件 =====
   各页面共用；样式复用 common.css 的 .toast / .modal-mask / .modal-box。
   - toast(msg, isErr)：轻提示，2 秒后自动消失
   - confirmBox(message, options)：自定义确认框，返回 Promise<boolean>
     用来替代原生 window.confirm（见 require.md 规范：弹窗统一用自定义实现）
   文字一律用 textContent 写入，避免标签名等内容造成 XSS。
*/

// 轻提示：保存成功 / 失败等即时反馈
function toast(msg, isErr) {
    var t = document.createElement("div");
    t.className = "toast" + (isErr ? " err" : "");
    t.textContent = msg;
    document.body.appendChild(t);
    setTimeout(function () { t.classList.add("hide"); }, 2000);
    setTimeout(function () { t.remove(); }, 2600);
}

// 自定义确认框：替代原生 window.confirm，返回 Promise<boolean>。
// 单例懒创建弹窗 DOM，样式复用 common.css 的 .modal-* 类。
//   confirmBox("要删除吗？")                            // 仅消息
//   confirmBox("删除无法撤销", {title: "确认删除", danger: true, okText: "删除"})
//   .then(function (ok) { if (ok) doDelete(); });
(function () {
    var mask = null;
    var titleEl = null, msgEl = null, okBtn = null, cancelBtn = null;
    var currentResolve = null;

    function ensureDom() {
        if (mask) return;
        mask = document.createElement("div");
        mask.className = "modal-mask";
        mask.hidden = true;
        mask.innerHTML = '<div class="modal-box">'
            + '<div class="modal-title"></div>'
            + '<div class="modal-msg"></div>'
            + '<div class="modal-ops">'
            + '<button type="button" class="modal-cancel"></button>'
            + '<button type="button" class="modal-ok"></button>'
            + '</div></div>';
        document.body.appendChild(mask);
        titleEl = mask.querySelector(".modal-title");
        msgEl = mask.querySelector(".modal-msg");
        okBtn = mask.querySelector(".modal-ok");
        cancelBtn = mask.querySelector(".modal-cancel");
        okBtn.addEventListener("click", function () { close(true); });
        cancelBtn.addEventListener("click", function () { close(false); });
        // 点遮罩空白区域视为取消；Esc 键也取消
        mask.addEventListener("click", function (e) { if (e.target === mask) close(false); });
        document.addEventListener("keydown", function (e) {
            if (!mask.hidden && e.key === "Escape") close(false);
        });
    }

    function close(result) {
        if (!mask) return;
        mask.hidden = true;
        var resolve = currentResolve;
        currentResolve = null;
        if (resolve) resolve(result);
    }

    window.confirmBox = function (message, options) {
        ensureDom();
        options = options || {};
        // 新弹窗把前一个未响应的 Promise 当作"取消"关掉，避免悬挂
        if (currentResolve) close(false);
        titleEl.textContent = options.title || "请确认";
        msgEl.textContent = String(message == null ? "" : message);
        okBtn.textContent = options.okText || "确定";
        cancelBtn.textContent = options.cancelText || "取消";
        okBtn.classList.toggle("danger", !!options.danger);
        mask.hidden = false;
        okBtn.focus();
        return new Promise(function (resolve) { currentResolve = resolve; });
    };
})();
