/* ================================================================
   AgentIRC — Nick List Panel (MutationObserver-based sync)
   Watches for <div class="irc-agent-data" data-agents="..."> in DOM
   ================================================================ */

(function () {
    "use strict";

    let agents = [];

    // ── Create the panel and status bar ──
    function createPanel() {
        if (document.getElementById("irc-nick-panel")) return;

        const panel = document.createElement("div");
        panel.id = "irc-nick-panel";
        panel.innerHTML = `
            <div class="nick-header" id="irc-channel-title">#agentirc</div>
            <div class="nick-list" id="irc-nick-list"></div>
            <div class="nick-footer" id="irc-nick-footer">0 users</div>
        `;
        document.body.appendChild(panel);
    }

    function createStatusBar() {
        if (document.getElementById("irc-status-bar")) return;

        const bar = document.createElement("div");
        bar.id = "irc-status-bar";
        bar.innerHTML = `
            <span id="irc-sb-room">lobby</span>
            <span id="irc-sb-mode">BROADCAST</span>
            <span id="irc-sb-topic">Topic</span>
        `;
        document.body.appendChild(bar);
    }

    // ── Render the nick list from current state ──
    function renderNickList() {
        const list = document.getElementById("irc-nick-list");
        const footer = document.getElementById("irc-nick-footer");
        if (!list) return;

        // Sort: enabled first, then alpha
        const sorted = [...agents].sort((a, b) => {
            if (a.enabled && !b.enabled) return -1;
            if (!a.enabled && b.enabled) return 1;
            return a.display.localeCompare(b.display);
        });

        list.innerHTML = sorted.map(a => {
            const cls = a.enabled ? "enabled" : "disabled";
            const prefix = a.enabled ? "@" : " ";
            const prefixCls = a.enabled ? "op" : "off";
            const checked = a.enabled ? "checked" : "";
            return `<div class="nick-entry ${cls}" data-name="${a.name}">
                <span class="nick-prefix ${prefixCls}">${prefix}</span>
                <input type="checkbox" class="nick-check" data-name="${a.name}" ${checked} />
                <span class="nick-name" title="${a.display}">${a.display}</span>
            </div>`;
        }).join("");

        // Wire checkbox toggles
        list.querySelectorAll(".nick-check").forEach(cb => {
            cb.addEventListener("change", e => {
                e.stopPropagation();
                toggleAgent(cb.dataset.name, cb.checked);
            });
        });

        // Wire nick name clicks → insert @name in input
        list.querySelectorAll(".nick-name").forEach(span => {
            span.addEventListener("click", () => {
                const name = span.closest(".nick-entry").dataset.name;
                insertDM(name);
            });
        });

        const on = agents.filter(a => a.enabled).length;
        if (footer) footer.textContent = `${on}/${agents.length} active`;
    }

    // ── Send /enable or /disable command via chat input ──
    function toggleAgent(name, enable) {
        const cmd = enable ? `/enable ${name}` : `/disable ${name}`;
        sendChatMessage(cmd);
    }

    function insertDM(name) {
        const input = findInput();
        if (!input) return;
        input.value = `@${name.replace(/_/g, "-")} `;
        input.focus();
        input.dispatchEvent(new Event("input", { bubbles: true }));
    }

    function findInput() {
        return document.querySelector("textarea") ||
               document.querySelector("[class*='chat-input']") ||
               document.querySelector("input[type='text']");
    }

    function sendChatMessage(text) {
        const input = findInput();
        if (!input) return;

        const setter = Object.getOwnPropertyDescriptor(
            window.HTMLTextAreaElement.prototype, "value"
        )?.set;
        if (setter) setter.call(input, text);
        else input.value = text;

        input.dispatchEvent(new Event("input", { bubbles: true }));

        setTimeout(() => {
            const btn = document.querySelector(
                'button[aria-label="Send"], button[class*="send"], button[type="submit"]'
            );
            if (btn) btn.click();
            else input.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", code: "Enter", bubbles: true }));
        }, 100);
    }

    // ── Parse data from hidden divs ──
    function processDataElement(el) {
        try {
            // Try data attributes first
            let raw = el.getAttribute("data-agents");
            let statusRaw = el.getAttribute("data-status");

            // Fallback: read from <span> text content
            if (!raw) {
                const span = el.querySelector(".irc-agents-raw");
                if (span) raw = span.textContent;
            }
            if (!statusRaw) {
                const span = el.querySelector(".irc-status-raw");
                if (span) statusRaw = span.textContent;
            }

            if (raw) {
                agents = JSON.parse(raw);
                renderNickList();
            }
            if (statusRaw) {
                const s = JSON.parse(statusRaw);
                const sbRoom = document.getElementById("irc-sb-room");
                const sbMode = document.getElementById("irc-sb-mode");
                const sbTopic = document.getElementById("irc-sb-topic");
                const chTitle = document.getElementById("irc-channel-title");
                if (sbRoom) sbRoom.textContent = s.room || "lobby";
                if (sbMode) sbMode.textContent = (s.mode || "BROADCAST").toUpperCase();
                if (sbTopic) sbTopic.textContent = s.topic || "";
                if (chTitle) chTitle.textContent = "#" + (s.room || "agentirc");
            }
        } catch (e) {
            console.warn("[AgentIRC] Failed to parse data element:", e);
        }
    }

    // ── MutationObserver: watch for hidden data divs ──
    function startObserver() {
        const observer = new MutationObserver(mutations => {
            for (const m of mutations) {
                for (const node of m.addedNodes) {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        // Check if it's a data element itself
                        if (node.classList && node.classList.contains("irc-agent-data")) {
                            processDataElement(node);
                        }
                        // Also check children
                        const children = node.querySelectorAll ? node.querySelectorAll(".irc-agent-data") : [];
                        children.forEach(processDataElement);
                    }
                }
            }
        });
        observer.observe(document.body, { childList: true, subtree: true });
    }

    // ── Init ──
    function init() {
        createPanel();
        createStatusBar();
        startObserver();

        // Process any data elements already in the DOM
        document.querySelectorAll(".irc-agent-data").forEach(processDataElement);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }

    // Re-inject panel if Chainlit nukes it
    const recheck = new MutationObserver(() => {
        if (!document.getElementById("irc-nick-panel")) {
            createPanel();
            createStatusBar();
            renderNickList();
        }
    });
    recheck.observe(document.body, { childList: true, subtree: true });
})();
