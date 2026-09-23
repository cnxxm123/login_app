/* 全站个人中心客户端：收藏、历史和阅读/播放进度统一上报。 */
(function () {
    "use strict";

    var config = window.PERSONAL_CONFIG || {};

    function requestJson(url, method, body, keepalive) {
        if (!url) return Promise.reject(new Error("个人中心接口未配置"));
        return fetch(url, {
            method: method,
            headers: {"Content-Type": "application/json", "Accept": "application/json"},
            body: JSON.stringify(body || {}),
            credentials: "same-origin",
            keepalive: !!keepalive
        }).then(function (response) {
            return response.json().catch(function () {
                throw new Error("服务器返回了无效响应");
            }).then(function (data) {
                if (!response.ok || !data.ok) throw new Error(data.error || ("HTTP " + response.status));
                return data;
            });
        });
    }

    function toast(message, error) {
        var old = document.querySelector(".personal-toast");
        if (old) old.remove();
        var node = document.createElement("div");
        node.className = "personal-toast" + (error ? " error" : "");
        node.setAttribute("role", "status");
        node.textContent = message;
        document.body.appendChild(node);
        window.setTimeout(function () { node.remove(); }, 1800);
    }

    function syncFavoriteButtons(path, favorite) {
        document.querySelectorAll("[data-personal-favorite]").forEach(function (button) {
            if (button.getAttribute("data-path") !== path) return;
            button.setAttribute("aria-pressed", favorite ? "true" : "false");
            button.title = favorite ? "取消收藏" : "收藏";
            button.textContent = favorite ? "★" : "☆";
        });
    }

    document.addEventListener("click", function (event) {
        var button = event.target.closest("[data-personal-favorite]");
        if (!button) return;
        event.preventDefault();
        event.stopPropagation();
        if (button.disabled) return;
        var path = button.getAttribute("data-path");
        var favorite = button.getAttribute("aria-pressed") !== "true";
        button.disabled = true;
        requestJson(config.favoriteUrl, "PUT", {path: path, favorite: favorite})
            .then(function (data) {
                syncFavoriteButtons(data.path, data.favorite);
                if (!data.favorite && button.hasAttribute("data-remove-on-unfavorite")) {
                    var card = button.closest(".personal-card");
                    if (card) card.remove();
                    var count = document.getElementById("favorite-count");
                    if (count) count.textContent = String(Math.max(0, parseInt(count.textContent || "0", 10) - 1));
                }
                toast(data.favorite ? "已加入收藏" : "已取消收藏");
            })
            .catch(function (error) { toast(error.message, true); })
            .finally(function () { button.disabled = false; });
    });

    document.addEventListener("click", function (event) {
        var button = event.target.closest("[data-personal-clear-progress]");
        if (!button) return;
        event.preventDefault();
        var path = button.getAttribute("data-path");
        button.disabled = true;
        requestJson(config.progressUrl, "DELETE", {path: path})
            .then(function () {
                var card = button.closest(".personal-card");
                if (card) card.remove();
                toast("进度已清除");
            })
            .catch(function (error) { toast(error.message, true); })
            .finally(function () { button.disabled = false; });
    });

    window.Personal = {
        setFavorite: function (path, favorite) {
            return requestJson(config.favoriteUrl, "PUT", {path: path, favorite: !!favorite});
        },
        recordHistory: function (path) {
            return requestJson(config.historyUrl, "POST", {path: path});
        },
        getState: function (path) {
            if (!config.stateUrl) return Promise.resolve({favorite: false, progress: null});
            return fetch(config.stateUrl + "?path=" + encodeURIComponent(path), {
                headers: {"Accept": "application/json"},
                credentials: "same-origin"
            }).then(function (response) {
                return response.json().then(function (data) {
                    if (!response.ok || !data.ok) throw new Error(data.error || ("HTTP " + response.status));
                    return data;
                });
            });
        },
        reportProgress: function (payload, keepalive) {
            return requestJson(config.progressUrl, "PUT", payload, keepalive).catch(function () {
                // 进度同步失败不打断阅读和播放；现有 localStorage 仍作为本机回退。
                return null;
            });
        },
        clearProgress: function (path) {
            return requestJson(config.progressUrl, "DELETE", {path: path});
        }
    };
}());
