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

/* ===== 通用 UI 组件（替代原生 alert / confirm / prompt，兼容沙箱 iframe）=====
   各页面共用；样式复用 common.css 的 .toast / .modal-mask / .modal-box。
   - toast(msg, isErr)：轻提示，2 秒后自动消失
   - confirmBox(msg, onOk, okText)：确认弹窗，点"确定"时回调 onOk()
   - promptBox(title, defaultValue, onOk)：输入弹窗，点"确定"时回调 onOk(value)
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

// 确认弹窗：替代原生 confirm()。okText 可自定义确定按钮文字（如"删除"）
function confirmBox(msg, onOk, okText) {
    var mask = document.createElement("div");
    mask.className = "modal-mask";
    var box = document.createElement("div");
    box.className = "modal-box";
    box.innerHTML =
        '<div class="modal-title">确认操作</div>' +
        '<div class="modal-msg"></div>' +
        '<div class="modal-ops">' +
        '<button type="button" class="modal-cancel">取消</button>' +
        '<button type="button" class="modal-ok">' + (okText || "确定") + '</button>' +
        '</div>';
    box.querySelector(".modal-msg").textContent = msg;
    box.querySelector(".modal-cancel").onclick = function () { mask.remove(); };
    box.querySelector(".modal-ok").onclick = function () {
        mask.remove();
        if (typeof onOk === "function") onOk();
    };
    // 点遮罩空白处 = 取消
    mask.addEventListener("click", function (ev) {
        if (ev.target === mask) mask.remove();
    });
    mask.appendChild(box);
    document.body.appendChild(mask);
    box.querySelector(".modal-ok").focus();
    return mask;
}

// 输入弹窗：替代原生 prompt()。点"确定"或按回车时回调 onOk(输入值)
function promptBox(title, defaultValue, onOk) {
    var mask = document.createElement("div");
    mask.className = "modal-mask";
    var box = document.createElement("div");
    box.className = "modal-box";
    box.innerHTML =
        '<div class="modal-title"></div>' +
        '<input type="text" class="modal-input">' +
        '<div class="modal-ops">' +
        '<button type="button" class="modal-cancel">取消</button>' +
        '<button type="button" class="modal-ok">确定</button>' +
        '</div>';
    box.querySelector(".modal-title").textContent = title;
    var input = box.querySelector(".modal-input");
    input.value = (defaultValue == null) ? "" : String(defaultValue);
    function submit() {
        mask.remove();
        if (typeof onOk === "function") onOk(input.value);
    }
    box.querySelector(".modal-cancel").onclick = function () { mask.remove(); };
    box.querySelector(".modal-ok").onclick = submit;
    mask.addEventListener("click", function (ev) {
        if (ev.target === mask) mask.remove();
    });
    input.addEventListener("keydown", function (ev) {
        if (ev.key === "Enter") { ev.preventDefault(); submit(); }
    });
    mask.appendChild(box);
    document.body.appendChild(mask);
    input.focus();
    input.select();  // 选中默认值，便于直接覆盖输入
    return mask;
}
