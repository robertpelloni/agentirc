/* ================================================================
   AgentIRC — Nick List Panel (agents.json polling + MutationObserver)
   Python writes public/agents.json, this JS fetches it.
   Also watches for .irc-sync-ping elements to trigger immediate refresh.
   ================================================================ */

(function () {
    "use strict";

    let agents = [];
    let pollInterval = null;

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

    // ── Fetch agents.json ──
    async function fetchAgents() {
        try {
            const resp = await fetch("/public/agents.json?t=" + Date.now());
            if (!resp.ok) return;
            const data = await resp.json();
            if (data.agents) {
                agents = data.agents;
                renderNickList();
            }
            if (data.status) {
                updateStatus(data.status);
            }
        } catch (e) {
            console.warn("[AgentIRC] fetch agents.json failed:", e);
        }
    }

    // ── Update status bar ──
    function updateStatus(s) {
        const sbRoom = document.getElementById("irc-sb-room");
        const sbMode = document.getElementById("irc-sb-mode");
        const sbTopic = document.getElementById("irc-sb-topic");
        const chTitle = document.getElementById("irc-channel-title");
        if (sbRoom) sbRoom.textContent = s.room || "lobby";
        if (sbMode) sbMode.textContent = (s.mode || "BROADCAST").toUpperCase();
        if (sbTopic) sbTopic.textContent = s.topic || "";
        if (chTitle) chTitle.textContent = "#" + (s.room || "agentirc");
    }

    // ── Render the nick list ──
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

        // Wire nick clicks → DM
        list.querySelectorAll(".nick-name").forEach(span => {
            span.addEventListener("click", () => {
                const name = span.closest(".nick-entry").dataset.name;
                insertDM(name);
            });
        });

        const on = agents.filter(a => a.enabled).length;
        if (footer) footer.textContent = `${on}/${agents.length} active`;
    }

    // ── Toggle via /enable /disable ──
    function toggleAgent(name, enable) {
        sendChatMessage(enable ? `/enable ${name}` : `/disable ${name}`);
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

    // ── MutationObserver: detect sync pings → re-fetch + hide ──
    function startObserver() {
        const observer = new MutationObserver(mutations => {
            let shouldFetch = false;
            for (const m of mutations) {
                for (const node of m.addedNodes) {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        // Check for sync pings
                        const all = node.classList && node.classList.contains("irc-sync-ping")
                            ? [node]
                            : (node.querySelectorAll ? [...node.querySelectorAll(".irc-sync-ping")] : []);
                        if (all.length > 0) {
                            shouldFetch = true;
                            // Hide the entire message wrapper containing the ping
                            all.forEach(ping => {
                                let el = ping;
                                for (let i = 0; i < 10; i++) {
                                    el = el.parentElement;
                                    if (!el) break;
                                    if (el.className && (
                                        el.className.includes("step") ||
                                        el.className.includes("message") ||
                                        el.className.includes("Message")
                                    )) {
                                        el.style.display = "none";
                                        el.style.height = "0";
                                        el.style.overflow = "hidden";
                                        el.style.padding = "0";
                                        el.style.margin = "0";
                                        break;
                                    }
                                }
                                ping.style.display = "none";
                            });
                        }

                        // Strip "Avatar for" text from any new elements
                        stripAvatarText(node);
                    }
                }
            }
            if (shouldFetch) fetchAgents();
        });
        observer.observe(document.body, { childList: true, subtree: true });
    }

    // ── Remove "Avatar for" text that Chainlit injects ──
    function stripAvatarText(root) {
        const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
            acceptNode(node) {
                return node.textContent.includes("Avatar for")
                    ? NodeFilter.FILTER_ACCEPT
                    : NodeFilter.FILTER_REJECT;
            }
        });
        const toRemove = [];
        while (walker.nextNode()) toRemove.push(walker.currentNode);
        toRemove.forEach(node => {
            node.textContent = node.textContent.replace(/Avatar for\s*/g, "");
            if (!node.textContent.trim()) node.parentElement?.remove();
        });
    }

    // ── Init ──
    function init() {
        createPanel();
        createStatusBar();
        fetchAgents();
        startObserver();

        // Also poll every 3 seconds as a backup
        if (pollInterval) clearInterval(pollInterval);
        pollInterval = setInterval(fetchAgents, 3000);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", () => { init(); stripAvatarText(document.body); });
    } else {
        init();
        stripAvatarText(document.body);
    }

    // Re-inject if Chainlit removes panel
    const recheck = new MutationObserver(() => {
        if (!document.getElementById("irc-nick-panel")) {
            createPanel();
            createStatusBar();
            renderNickList();
        }
    });
    recheck.observe(document.body, { childList: true, subtree: true });
})();
