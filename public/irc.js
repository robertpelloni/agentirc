/* ================================================================
   AgentIRC — Nick List Panel + Status Bar
   Injects a persistent right-side IRC nick list with checkboxes
   ================================================================ */

(function () {
    "use strict";

    // ── State ──
    let agents = []; // [{name, display, enabled, benched}]

    // ── Create DOM ──
    function createPanel() {
        if (document.getElementById("irc-nick-panel")) return;

        const panel = document.createElement("div");
        panel.id = "irc-nick-panel";
        panel.innerHTML = `
            <div class="nick-header">
                #agentirc
            </div>
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
            <span id="irc-sb-topic">The Omni-Workspace and Future AI Architectures</span>
        `;
        document.body.appendChild(bar);
    }

    // ── Render agents ──
    function renderNickList() {
        const list = document.getElementById("irc-nick-list");
        const footer = document.getElementById("irc-nick-footer");
        if (!list) return;

        // Sort: enabled first (with @), then disabled (with .)
        const sorted = [...agents].sort((a, b) => {
            if (a.enabled && !b.enabled) return -1;
            if (!a.enabled && b.enabled) return 1;
            return a.display.localeCompare(b.display);
        });

        list.innerHTML = sorted
            .map((a) => {
                const cls = a.enabled ? "enabled" : "disabled";
                const prefix = a.enabled ? "@" : " ";
                const prefixCls = a.enabled ? "op" : "off";
                const checked = a.enabled ? "checked" : "";
                return `
                    <div class="nick-entry ${cls}" data-name="${a.name}">
                        <span class="nick-prefix ${prefixCls}">${prefix}</span>
                        <input type="checkbox" class="nick-check" data-name="${a.name}" ${checked} />
                        <span class="nick-name" title="${a.display}">${a.display}</span>
                    </div>
                `;
            })
            .join("");

        // Wire up checkbox clicks
        list.querySelectorAll(".nick-check").forEach((cb) => {
            cb.addEventListener("change", (e) => {
                e.stopPropagation();
                const name = cb.dataset.name;
                const enable = cb.checked;
                toggleAgent(name, enable);
            });
        });

        // Wire up nick name clicks (DM shortcut)
        list.querySelectorAll(".nick-name").forEach((span) => {
            span.addEventListener("click", () => {
                const entry = span.closest(".nick-entry");
                const name = entry.dataset.name;
                insertDM(name);
            });
        });

        const enabledCount = agents.filter((a) => a.enabled).length;
        if (footer) {
            footer.textContent = `${enabledCount}/${agents.length} active`;
        }
    }

    // ── Toggle agent on/off via chat command ──
    function toggleAgent(name, enable) {
        const cmd = enable ? `/enable ${name}` : `/disable ${name}`;
        sendChatMessage(cmd);
    }

    // ── Insert @name into chat input ──
    function insertDM(name) {
        const input = document.querySelector("textarea, [class*='chat-input'], input[type='text']");
        if (input) {
            const display = name.replace(/_/g, "-");
            input.value = `@${display} `;
            input.focus();
            input.dispatchEvent(new Event("input", { bubbles: true }));
        }
    }

    // ── Submit a chat message programmatically ──
    function sendChatMessage(text) {
        const input = document.querySelector("textarea, [class*='chat-input'], input[type='text']");
        if (!input) return;

        // React-compatible way to set value
        const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
            window.HTMLTextAreaElement.prototype, "value"
        )?.set || Object.getOwnPropertyDescriptor(
            window.HTMLInputElement.prototype, "value"
        )?.set;

        if (nativeInputValueSetter) {
            nativeInputValueSetter.call(input, text);
        } else {
            input.value = text;
        }

        input.dispatchEvent(new Event("input", { bubbles: true }));

        // Find and click the send button
        setTimeout(() => {
            const sendBtn = document.querySelector(
                'button[aria-label="Send"], button[class*="send"], button[type="submit"]'
            );
            if (sendBtn) {
                sendBtn.click();
            } else {
                // Fallback: dispatch Enter key
                input.dispatchEvent(
                    new KeyboardEvent("keydown", { key: "Enter", code: "Enter", bubbles: true })
                );
            }
        }, 100);
    }

    // ── Public API: called from Python via hidden HTML messages ──
    window.__ircUpdateAgents = function (data) {
        agents = data.agents || [];
        renderNickList();
    };

    window.__ircUpdateStatus = function (data) {
        const sbRoom = document.getElementById("irc-sb-room");
        const sbMode = document.getElementById("irc-sb-mode");
        const sbTopic = document.getElementById("irc-sb-topic");
        const nickHeader = document.querySelector("#irc-nick-panel .nick-header");

        if (sbRoom) sbRoom.textContent = data.room || "lobby";
        if (sbMode) sbMode.textContent = data.mode || "BROADCAST";
        if (sbTopic) sbTopic.textContent = data.topic || "";
        if (nickHeader) nickHeader.textContent = "#" + (data.room || "agentirc");
    };

    // ── Init ──
    function init() {
        createPanel();
        createStatusBar();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }

    // Also re-inject if Chainlit re-renders
    const observer = new MutationObserver(() => {
        if (!document.getElementById("irc-nick-panel")) {
            init();
        }
    });
    observer.observe(document.body, { childList: true, subtree: true });
})();
