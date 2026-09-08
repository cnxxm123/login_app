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
