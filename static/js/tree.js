// ===== 目录树侧栏（static/js/tree.js）=====
// 为文件浏览页面提供目录树组件：懒加载子节点、展开/折叠、
// 记忆展开状态、自动展开到当前目录、切换面板显隐。
// 依赖：页面需定义 window.TREE_CONFIG 提供 urls.tree 和 currentPath。

(function () {
    "use strict";

    var config = window.TREE_CONFIG;
    if (!config) return; // 未注入配置则不初始化

    // ===== 常量 =====
    var TREE_API = config.urls.tree;          // /tree API 地址
    var CURRENT_PATH = config.currentPath;     // 当前浏览的目录路径
    var STORAGE_KEY = "tree_expanded_paths";   // localStorage 键名

    // ===== DOM 引用 =====
    var treeRoot = document.getElementById("tree-root");
    var treePanel = document.getElementById("tree-panel");
    var treeToggle = document.getElementById("tree-toggle");
    if (!treeRoot || !treePanel || !treeToggle) return;

    // ===== 状态 =====
    // 已展开的路径集合，用于记忆展开状态
    var expandedPaths = loadExpandedPaths();
    // 已加载子节点的路径集合，避免重复请求
    var loadedPaths = {};
    // 当前活跃节点（当前目录对应的 DOM 节点行）
    var activeNodeRow = null;

    // ===== 工具函数 =====
    function encPath(p) {
        // 路径分段编码，避免特殊字符破坏 URL
        return p.split("/").map(encodeURIComponent).join("/");
    }

    function loadExpandedPaths() {
        try {
            var raw = localStorage.getItem(STORAGE_KEY);
            return raw ? JSON.parse(raw) : {};
        } catch (e) {
            return {};
        }
    }

    function saveExpandedPaths() {
        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(expandedPaths));
        } catch (e) {
            // localStorage 满或不可用，静默忽略
        }
    }

    // ===== 创建树节点 DOM =====
    function createNodeRow(node) {
        // 创建一行节点：箭头 + 图标 + 名称
        var li = document.createElement("li");
        li.className = "tree-node";

        var row = document.createElement("div");
        row.className = "tree-node-row";
        row.setAttribute("data-path", node.path);

        // 展开箭头
        var arrow = document.createElement("span");
        arrow.className = "tree-arrow";
        arrow.textContent = "▶";
        row.appendChild(arrow);

        // 文件夹图标
        var iconClosed = document.createElement("span");
        iconClosed.className = "tree-icon closed";
        iconClosed.textContent = "📁";
        row.appendChild(iconClosed);
        var iconOpen = document.createElement("span");
        iconOpen.className = "tree-icon open";
        iconOpen.textContent = "📂";
        row.appendChild(iconOpen);

        // 名称
        var nameEl = document.createElement("span");
        nameEl.className = "tree-name";
        nameEl.textContent = node.name || "云书库";
        row.appendChild(nameEl);

        li.appendChild(row);
        return li;
    }

    function createChildrenContainer() {
        var ul = document.createElement("ul");
        ul.className = "tree-children";
        return ul;
    }

    // ===== 渲染子节点列表 =====
    function renderChildren(childrenUl, children) {
        childrenUl.innerHTML = "";
        children.forEach(function (child) {
            var nodeLi = createNodeRow(child);
            // 为每个节点预置空的子节点容器
            var subUl = createChildrenContainer();
            nodeLi.appendChild(subUl);
            childrenUl.appendChild(nodeLi);
        });
    }

    // ===== 展开/折叠节点 =====
    function toggleNode(nodeLi) {
        var row = nodeLi.querySelector(".tree-node-row");
        var arrow = row.querySelector(".tree-arrow");
        var childrenUl = nodeLi.querySelector(".tree-children");
        var path = row.getAttribute("data-path");

        if (!childrenUl) return;

        var isExpanded = childrenUl.classList.contains("expanded");

        if (isExpanded) {
            // 折叠
            childrenUl.classList.remove("expanded");
            arrow.classList.remove("expanded");
            row.classList.remove("expanded");
            delete expandedPaths[path];
            saveExpandedPaths();
        } else {
            // 展开
            childrenUl.classList.add("expanded");
            arrow.classList.add("expanded");
            row.classList.add("expanded");
            expandedPaths[path] = true;
            saveExpandedPaths();

            // 如果子节点还没加载过，则异步加载
            if (!loadedPaths[path]) {
                loadChildren(nodeLi, path);
            }
        }
    }

    // ===== 懒加载子节点 =====
    function loadChildren(nodeLi, path) {
        var childrenUl = nodeLi.querySelector(".tree-children");
        if (!childrenUl) return;

        // 显示加载中
        var loadingEl = document.createElement("div");
        loadingEl.className = "tree-loading";
        loadingEl.textContent = "加载中…";
        childrenUl.appendChild(loadingEl);

        fetch(TREE_API + "?path=" + encPath(path))
            .then(function (r) {
                if (!r.ok) throw new Error("HTTP " + r.status);
                return r.json();
            })
            .then(function (data) {
                // 移除加载中提示
                if (loadingEl.parentNode) loadingEl.parentNode.removeChild(loadingEl);

                loadedPaths[path] = true;

                if (data.children && data.children.length > 0) {
                    renderChildren(childrenUl, data.children);

                    // 检查是否需要自动展开到当前路径
                    autoExpandToCurrent(childrenUl);

                    // 恢复之前记忆的展开状态
                    restoreExpanded(childrenUl, path);
                } else {
                    // 没有子目录，移除空容器，标记为无子节点
                    childrenUl.innerHTML = "";
                }
            })
            .catch(function (err) {
                if (loadingEl.parentNode) loadingEl.parentNode.removeChild(loadingEl);
                console.error("加载目录树失败:", err);
            });
    }

    // ===== 自动展开到当前目录 =====
    function autoExpandToCurrent(container) {
        if (!CURRENT_PATH) return;

        var rows = container.querySelectorAll(".tree-node-row");
        rows.forEach(function (row) {
            var nodePath = row.getAttribute("data-path");
            if (!nodePath) return;

            // 如果当前路径以该节点路径开头，说明当前目录在该节点下
            if (CURRENT_PATH === nodePath || CURRENT_PATH.indexOf(nodePath + "/") === 0) {
                var nodeLi = row.parentNode;
                var childrenUl = nodeLi.querySelector(".tree-children");
                if (childrenUl && !childrenUl.classList.contains("expanded")) {
                    childrenUl.classList.add("expanded");
                    row.querySelector(".tree-arrow").classList.add("expanded");
                    row.classList.add("expanded");
                    expandedPaths[nodePath] = true;
                    saveExpandedPaths();

                    // 继续加载子节点
                    if (!loadedPaths[nodePath]) {
                        loadChildren(nodeLi, nodePath);
                    }
                }
            }

            // 高亮当前目录
            if (nodePath === CURRENT_PATH) {
                highlightNode(row);
            }
        });
    }

    // ===== 恢复之前展开的节点 =====
    function restoreExpanded(container, parentPath) {
        var rows = container.querySelectorAll(".tree-node-row");
        rows.forEach(function (row) {
            var nodePath = row.getAttribute("data-path");
            if (nodePath && expandedPaths[nodePath]) {
                var nodeLi = row.parentNode;
                var childrenUl = nodeLi.querySelector(".tree-children");
                if (childrenUl && !childrenUl.classList.contains("expanded")) {
                    childrenUl.classList.add("expanded");
                    row.querySelector(".tree-arrow").classList.add("expanded");
                    row.classList.add("expanded");
                    if (!loadedPaths[nodePath]) {
                        loadChildren(nodeLi, nodePath);
                    }
                }
            }
        });
    }

    // ===== 高亮当前节点 =====
    function highlightNode(row) {
        if (activeNodeRow) {
            activeNodeRow.classList.remove("active");
        }
        row.classList.add("active");
        activeNodeRow = row;

        // 滚动到可见区域
        row.scrollIntoView({ block: "nearest", behavior: "smooth" });
    }

    // ===== 事件委托：点击处理 =====
    treeRoot.addEventListener("click", function (e) {
        var row = e.target.closest(".tree-node-row");
        if (!row) return;

        var path = row.getAttribute("data-path");
        if (!path && path !== "") return; // path 可能为空字符串（根目录）

        // 点击的是箭头区域 → 展开/折叠
        if (e.target.closest(".tree-arrow")) {
            var nodeLi = row.parentNode;
            toggleNode(nodeLi);
            return;
        }

        // 点击的是名称/图标 → 导航到该目录
        // 根目录路径为空字符串，导航到主页
        if (path === "") {
            window.location.href = config.urls.browseRoot || "/";
        } else {
            window.location.href = config.urls.browseBase + encPath(path);
        }
    });

    // ===== 面板切换 =====
    function showTree() {
        treePanel.removeAttribute("hidden");
        treeToggle.setAttribute("aria-expanded", "true");
        document.body.classList.add("tree-visible");
        try { localStorage.setItem("tree_visible", "1"); } catch (e) {}
    }

    function hideTree() {
        treePanel.setAttribute("hidden", "");
        treeToggle.setAttribute("aria-expanded", "false");
        document.body.classList.remove("tree-visible");
        try { localStorage.setItem("tree_visible", "0"); } catch (e) {}
    }

    function isTreeVisible() {
        return !treePanel.hasAttribute("hidden");
    }

    window.toggleTree = function () {
        if (isTreeVisible()) {
            hideTree();
        } else {
            showTree();
        }
    };

    // 切换按钮点击
    treeToggle.addEventListener("click", function () {
        window.toggleTree();
    });

    // ===== 初始化 =====
    function init() {
        // 加载根节点
        fetch(TREE_API)
            .then(function (r) {
                if (!r.ok) throw new Error("HTTP " + r.status);
                return r.json();
            })
            .then(function (data) {
                loadedPaths[""] = true;

                // 创建根节点条目
                var rootLi = createNodeRow(data);
                var rootChildrenUl = createChildrenContainer();
                rootLi.appendChild(rootChildrenUl);
                treeRoot.appendChild(rootLi);

                if (data.children && data.children.length > 0) {
                    renderChildren(rootChildrenUl, data.children);
                    // 自动展开到当前目录
                    autoExpandToCurrent(rootChildrenUl);
                    // 恢复之前展开的节点
                    restoreExpanded(rootChildrenUl, "");
                }

                // 默认展开根节点
                var rootChildren = treeRoot.querySelector(".tree-children");
                if (rootChildren) {
                    rootChildren.classList.add("expanded");
                    var rootArrow = treeRoot.querySelector(".tree-arrow");
                    if (rootArrow) rootArrow.classList.add("expanded");
                    var rootRow = treeRoot.querySelector(".tree-node-row");
                    if (rootRow) rootRow.classList.add("expanded");
                }

                // 高亮当前目录
                if (CURRENT_PATH !== undefined && CURRENT_PATH !== null) {
                    highlightCurrentPath(CURRENT_PATH);
                }
            })
            .catch(function (err) {
                console.error("初始化目录树失败:", err);
            });

        // 恢复面板可见性
        var savedVisible = null;
        try { savedVisible = localStorage.getItem("tree_visible"); } catch (e) {}
        if (savedVisible === "1") {
            showTree();
        } else if (savedVisible === "0") {
            hideTree();
        } else {
            // 默认显示（桌面端）
            showTree();
        }
    }

    // 高亮指定路径的节点
    function highlightCurrentPath(targetPath) {
        if (!targetPath && targetPath !== "") return;

        var allRows = treeRoot.querySelectorAll(".tree-node-row");
        allRows.forEach(function (row) {
            var nodePath = row.getAttribute("data-path");
            if (nodePath === targetPath) {
                highlightNode(row);
            }
        });
    }

    // ===== 启动 =====
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();