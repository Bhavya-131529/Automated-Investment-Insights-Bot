const API_BASE = "http://localhost:8001";
let userId = localStorage.getItem("investAI_userId") || null;

const chatMessages = document.getElementById("chat-messages");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const profileForm = document.getElementById("profile-form");

// Initialize
window.onload = async () => {
    if (userId) {
        await loadProfile();
        await loadHistory();
    }
};

async function loadProfile() {
    try {
        const res = await fetch(`${API_BASE}/profile/${userId}`);
        if (res.ok) {
            const data = await res.json();
            document.getElementById("goal").value = data.goal;
            document.getElementById("horizon").value = data.time_horizon;
            document.getElementById("budget").value = data.monthly_budget;
            document.getElementById("risk").value = data.risk_tolerance;
            if (document.getElementById("holdings") && data.existing_holdings) {
                document.getElementById("holdings").value = data.existing_holdings;
            }
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
        existing_holdings: document.getElementById("holdings") ? document.getElementById("holdings").value : null
    };

    try {
        const res = await fetch(`${API_BASE}/profile`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(profile)
        });
        const data = await res.json();
        userId = data.id;
        localStorage.setItem("investAI_userId", userId);
        alert("Profile saved successfully!");
    } catch (e) {
        alert("Failed to save profile");
    }
};

chatForm.onsubmit = async (e) => {
    e.preventDefault();
    const text = chatInput.value.trim();
    if (!text) return;

    if (!userId) {
        alert("Please save your profile first to get personalized insights.");
        return;
    }

    appendMessage("user", text);
    chatInput.value = "";
    
    // Add loading indicator
    const loadingId = appendMessage("assistant", "Thinking...");

    try {
        const res = await fetch(`${API_BASE}/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user_id: parseInt(userId), message: text })
        });
        const data = await res.json();
        updateMessage(loadingId, data.response);
    } catch (e) {
        updateMessage(loadingId, "Sorry, I encountered an error. Is the backend running?");
    }
};

function appendMessage(role, content) {
    const id = Date.now();
    const div = document.createElement("div");
    div.className = `message ${role}`;
    div.id = `msg-${id}`;
    div.innerHTML = `<div class="bubble">${content}</div>`;
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return `msg-${id}`;
}

function updateMessage(id, content) {
    const el = document.getElementById(id);
    if (el) {
        el.querySelector(".bubble").textContent = content;
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}
