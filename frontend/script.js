const API_BASE = "http://localhost:8000";
let userId = localStorage.getItem("investAI_userId") || null;

const chatMessages = document.getElementById("chat-messages");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const profileForm = document.getElementById("profile-form");
const profileStatus = document.getElementById("profile-status");

// Initialize
window.onload = async () => {
    if (userId) {
        await loadProfile();
        await loadHistory();
        showProfileStatus("Profile loaded ✓", "success");
    }
};

async function loadProfile() {
    try {
        const res = await fetch(`${API_BASE}/profile/${userId}`);
        if (res.ok) {
            const data = await res.json();
            document.getElementById("goal").value = data.goal || "";
            document.getElementById("horizon").value = data.time_horizon || "";
            document.getElementById("budget").value = data.monthly_budget || "";
            document.getElementById("risk").value = data.risk_tolerance || "medium";
            if (data.existing_holdings) {
                document.getElementById("holdings").value = data.existing_holdings;
            }
        } else if (res.status === 404) {
            // Profile no longer exists, clear stored userId
            localStorage.removeItem("investAI_userId");
            userId = null;
        }
    } catch (e) {
        console.error("Failed to load profile", e);
    }
}

async function loadHistory() {
    try {
        const res = await fetch(`${API_BASE}/history/${userId}`);
        if (res.ok) {
            const data = await res.json();
            data.forEach(msg => appendMessage(msg.role, msg.content));
        }
    } catch (e) {
        console.error("Failed to load history", e);
    }
}

profileForm.onsubmit = async (e) => {
    e.preventDefault();
    const profile = {
        goal: document.getElementById("goal").value,
        time_horizon: parseInt(document.getElementById("horizon").value),
        monthly_budget: parseFloat(document.getElementById("budget").value),
        risk_tolerance: document.getElementById("risk").value,
        existing_holdings: document.getElementById("holdings").value || null
    };

    try {
        let res;
        if (userId) {
            // Update existing profile via PUT
            res = await fetch(`${API_BASE}/profile/${userId}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(profile)
            });
            // If profile not found on server, fall back to creating a new one
            if (res.status === 404) {
                res = await fetch(`${API_BASE}/profile`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(profile)
                });
            }
        } else {
            // Create new profile via POST
            res = await fetch(`${API_BASE}/profile`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(profile)
            });
        }

        if (!res.ok) {
            throw new Error(`Server error: ${res.status}`);
        }

        const data = await res.json();
        userId = data.id;
        localStorage.setItem("investAI_userId", userId);
        showProfileStatus("Profile saved successfully ✓", "success");
    } catch (e) {
        console.error("Profile save error:", e);
        showProfileStatus("Failed to save profile ✗", "error");
    }
};

chatForm.onsubmit = async (e) => {
    e.preventDefault();
    const text = chatInput.value.trim();
    if (!text) return;

    if (!userId) {
        appendMessage("assistant", "⚠️ Please save your profile first to get personalized insights.");
        return;
    }

    appendMessage("user", text);
    chatInput.value = "";

    // Add loading indicator
    const loadingId = appendLoadingMessage();

    try {
        const res = await fetch(`${API_BASE}/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user_id: parseInt(userId), message: text })
        });
        if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.detail || `Server error ${res.status}`);
        }
        const data = await res.json();
        updateMessage(loadingId, data.response);
    } catch (e) {
        updateMessage(loadingId, `Sorry, I encountered an error: ${e.message}`);
    }
};

function appendMessage(role, content) {
    const id = `msg-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`;
    const div = document.createElement("div");
    div.className = `message ${role}`;
    div.id = id;
    // Render markdown using marked.js
    const formatted = marked.parse(content);
    div.innerHTML = `<div class="bubble">${formatted}</div>`;
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return id;
}

function appendLoadingMessage() {
    const id = `msg-${Date.now()}-loading`;
    const div = document.createElement("div");
    div.className = "message assistant";
    div.id = id;
    div.innerHTML = `<div class="bubble loading-bubble"><span class="dot-pulse"></span><span class="dot-pulse"></span><span class="dot-pulse"></span></div>`;
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return id;
}

function updateMessage(id, content) {
    const el = document.getElementById(id);
    if (el) {
        const formatted = marked.parse(content);
        el.querySelector(".bubble").innerHTML = formatted;
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

function showProfileStatus(msg, type) {
    if (!profileStatus) return;
    profileStatus.textContent = msg;
    profileStatus.className = `profile-status ${type}`;
    profileStatus.style.display = "block";
    setTimeout(() => { profileStatus.style.display = "none"; }, 3000);
}

function escapeHtml(text) {
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}
