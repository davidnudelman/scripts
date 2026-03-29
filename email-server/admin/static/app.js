/* =====================================================
   Mail Server Admin — Client-Side Application
   ===================================================== */

const API = {
    token: localStorage.getItem("token") || "",

    async request(method, path, body = null) {
        const opts = {
            method,
            headers: { "Content-Type": "application/json" },
        };
        if (this.token) opts.headers["Authorization"] = `Bearer ${this.token}`;
        if (body) opts.body = JSON.stringify(body);
        const res = await fetch(path, opts);
        if (res.status === 401) {
            this.logout();
            return null;
        }
        if (res.status === 204) return null;
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || `Request failed (${res.status})`);
        }
        return res.json();
    },

    get(path) { return this.request("GET", path); },
    post(path, body) { return this.request("POST", path, body); },
    put(path, body) { return this.request("PUT", path, body); },
    del(path) { return this.request("DELETE", path); },

    login(token) {
        this.token = token;
        localStorage.setItem("token", token);
    },

    logout() {
        this.token = "";
        localStorage.removeItem("token");
        App.showLogin();
    },
};

/* ── Toast Notifications ─────────────────────────────── */
function toast(message, type = "success") {
    const el = document.getElementById("toast");
    el.textContent = message;
    el.className = `toast toast-${type} show`;
    setTimeout(() => el.classList.remove("show"), 3000);
}

/* ── Modal Helpers ───────────────────────────────────── */
function showModal(id) { document.getElementById(id).classList.add("show"); }
function hideModal(id) { document.getElementById(id).classList.remove("show"); }

/* ── Format Bytes ────────────────────────────────────── */
function formatBytes(bytes) {
    if (bytes === 0) return "0 B";
    const units = ["B", "KB", "MB", "GB", "TB"];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return (bytes / Math.pow(1024, i)).toFixed(1) + " " + units[i];
}

/* ── Main Application ────────────────────────────────── */
const App = {
    currentPage: "dashboard",

    init() {
        if (API.token) {
            this.showApp();
            this.navigate("dashboard");
        } else {
            this.showLogin();
        }
    },

    showLogin() {
        document.getElementById("login-view").style.display = "flex";
        document.getElementById("app-view").style.display = "none";
    },

    showApp() {
        document.getElementById("login-view").style.display = "none";
        document.getElementById("app-view").style.display = "flex";
    },

    navigate(page) {
        this.currentPage = page;
        document.querySelectorAll(".sidebar nav a").forEach(a => {
            a.classList.toggle("active", a.dataset.page === page);
        });
        document.querySelectorAll(".page").forEach(p => {
            p.style.display = p.id === `page-${page}` ? "block" : "none";
        });
        this.loadPage(page);
    },

    async loadPage(page) {
        try {
            switch (page) {
                case "dashboard": await Pages.dashboard(); break;
                case "domains": await Pages.domains(); break;
                case "users": await Pages.users(); break;
                case "aliases": await Pages.aliases(); break;
                case "dkim": await Pages.dkim(); break;
                case "dns": await Pages.dns(); break;
                case "settings": await Pages.settings(); break;
            }
        } catch (err) {
            toast(err.message, "error");
        }
    },
};

/* ── Page Renderers ──────────────────────────────────── */
const Pages = {
    async dashboard() {
        const [domains, users, aliases] = await Promise.all([
            API.get("/api/domains/"),
            API.get("/api/users/"),
            API.get("/api/aliases/"),
        ]);
        document.getElementById("stat-domains").textContent = domains.length;
        document.getElementById("stat-users").textContent = users.length;
        document.getElementById("stat-aliases").textContent = aliases.length;
        document.getElementById("stat-active-users").textContent =
            users.filter(u => u.active).length;
    },

    /* ── Domains ─────────────────────────────────────── */
    _domains: [],

    async domains() {
        this._domains = await API.get("/api/domains/");
        const tbody = document.getElementById("domains-tbody");
        tbody.innerHTML = this._domains.map(d => `
            <tr>
                <td><strong>${esc(d.name)}</strong></td>
                <td>${d.user_count}</td>
                <td><span class="badge ${d.active ? 'badge-active' : 'badge-inactive'}">
                    ${d.active ? 'Active' : 'Inactive'}</span></td>
                <td>${new Date(d.created_at).toLocaleDateString()}</td>
                <td>
                    <button class="btn btn-sm btn-outline" onclick="Pages.toggleDomain(${d.id}, ${!d.active})">
                        ${d.active ? 'Disable' : 'Enable'}
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="Pages.deleteDomain(${d.id})">Delete</button>
                </td>
            </tr>
        `).join("");
    },

    async addDomain() {
        const name = document.getElementById("domain-name").value.trim();
        if (!name) return;
        try {
            await API.post("/api/domains/", { name });
            hideModal("modal-domain");
            document.getElementById("domain-name").value = "";
            toast("Domain added");
            await this.domains();
        } catch (err) { toast(err.message, "error"); }
    },

    async toggleDomain(id, active) {
        await API.put(`/api/domains/${id}`, { active });
        toast(`Domain ${active ? 'enabled' : 'disabled'}`);
        await this.domains();
    },

    async deleteDomain(id) {
        if (!confirm("Delete this domain and ALL its users?")) return;
        await API.del(`/api/domains/${id}`);
        toast("Domain deleted");
        await this.domains();
    },

    /* ── Users ───────────────────────────────────────── */
    async users() {
        const users = await API.get("/api/users/");
        const tbody = document.getElementById("users-tbody");
        tbody.innerHTML = users.map(u => `
            <tr>
                <td><strong>${esc(u.email)}</strong></td>
                <td>${esc(u.display_name)}</td>
                <td>${formatBytes(u.quota)}</td>
                <td><span class="badge ${u.active ? 'badge-active' : 'badge-inactive'}">
                    ${u.active ? 'Active' : 'Inactive'}</span></td>
                <td>${u.is_admin ? 'Admin' : 'User'}</td>
                <td>
                    <button class="btn btn-sm btn-outline" onclick="Pages.editUser(${u.id})">Edit</button>
                    <button class="btn btn-sm btn-danger" onclick="Pages.deleteUser(${u.id})">Delete</button>
                </td>
            </tr>
        `).join("");
    },

    async addUser() {
        const email = document.getElementById("user-email").value.trim();
        const password = document.getElementById("user-password").value;
        const displayName = document.getElementById("user-display-name").value.trim();
        const quota = parseInt(document.getElementById("user-quota").value) * 1024 * 1024;
        if (!email || !password) return;
        try {
            await API.post("/api/users/", {
                email, password, display_name: displayName, quota,
            });
            hideModal("modal-user");
            toast("User created");
            await this.users();
        } catch (err) { toast(err.message, "error"); }
    },

    async editUser(id) {
        const newPassword = prompt("New password (leave empty to keep current):");
        if (newPassword === null) return;
        if (newPassword && newPassword.length < 8) {
            toast("Password must be at least 8 characters", "error");
            return;
        }
        try {
            const body = {};
            if (newPassword) body.password = newPassword;
            await API.put(`/api/users/${id}`, body);
            toast("User updated");
        } catch (err) { toast(err.message, "error"); }
    },

    async deleteUser(id) {
        if (!confirm("Delete this user and their mailbox?")) return;
        await API.del(`/api/users/${id}`);
        toast("User deleted");
        await this.users();
    },

    /* ── Aliases ─────────────────────────────────────── */
    async aliases() {
        const aliases = await API.get("/api/aliases/");
        const tbody = document.getElementById("aliases-tbody");
        tbody.innerHTML = aliases.map(a => `
            <tr>
                <td>${esc(a.source)}</td>
                <td>${esc(a.destination)}</td>
                <td><span class="badge ${a.active ? 'badge-active' : 'badge-inactive'}">
                    ${a.active ? 'Active' : 'Inactive'}</span></td>
                <td>
                    <button class="btn btn-sm btn-danger" onclick="Pages.deleteAlias(${a.id})">Delete</button>
                </td>
            </tr>
        `).join("");
    },

    async addAlias() {
        const source = document.getElementById("alias-source").value.trim();
        const destination = document.getElementById("alias-destination").value.trim();
        if (!source || !destination) return;
        try {
            await API.post("/api/aliases/", { source, destination });
            hideModal("modal-alias");
            toast("Alias created");
            await this.aliases();
        } catch (err) { toast(err.message, "error"); }
    },

    async deleteAlias(id) {
        if (!confirm("Delete this alias?")) return;
        await API.del(`/api/aliases/${id}`);
        toast("Alias deleted");
        await this.aliases();
    },

    /* ── DKIM ────────────────────────────────────────── */
    async dkim() {
        const domains = await API.get("/api/domains/");
        const container = document.getElementById("dkim-content");
        if (domains.length === 0) {
            container.innerHTML = '<p>Add a domain first to manage DKIM keys.</p>';
            return;
        }

        let html = '';
        for (const domain of domains) {
            const keys = await API.get(`/api/domains/${domain.id}/dkim/`);
            html += `
                <div class="card">
                    <h3 style="margin-bottom: 1rem; display: flex; justify-content: space-between; align-items: center;">
                        ${esc(domain.name)}
                        <button class="btn btn-sm btn-primary" onclick="Pages.generateDkim(${domain.id})">
                            Generate DKIM Key
                        </button>
                    </h3>
                    ${keys.length === 0 ? '<p style="color: var(--text-muted);">No DKIM keys. Generate one to enable email signing.</p>' : ''}
                    ${keys.map(k => `
                        <div class="dns-record">
                            <div style="margin-bottom: 0.5rem; font-weight: 600;">
                                Selector: ${esc(k.selector)} | ${k.key_size}-bit |
                                <span class="badge ${k.active ? 'badge-active' : 'badge-inactive'}">
                                    ${k.active ? 'Active' : 'Inactive'}
                                </span>
                            </div>
                            <div>DNS TXT Record:</div>
                            <div style="margin-top: 0.25rem;">${esc(k.dns_record)}</div>
                        </div>
                    `).join("")}
                </div>
            `;
        }
        container.innerHTML = html;
    },

    async generateDkim(domainId) {
        try {
            await API.post(`/api/domains/${domainId}/dkim/`, { selector: "mail", key_size: 2048 });
            toast("DKIM key generated — add the DNS TXT record shown below");
            await this.dkim();
        } catch (err) { toast(err.message, "error"); }
    },

    /* ── DNS Records ─────────────────────────────────── */
    async dns() {
        const data = await API.get("/api/dns-records");
        const container = document.getElementById("dns-content");
        container.innerHTML = data.records.map(r => `
            <div class="dns-record">
                <div><span class="type">${esc(r.type)}</span> ${esc(r.name)}</div>
                <div style="margin-top: 0.25rem;">${esc(r.value)}</div>
                <div style="margin-top: 0.25rem; color: var(--text-muted); font-size: 0.75rem;">
                    ${esc(r.description)}
                </div>
            </div>
        `).join("");
    },

    /* ── Settings ────────────────────────────────────── */
    async settings() {
        const settings = await API.get("/api/settings/");
        const container = document.getElementById("settings-form");
        const labels = {
            max_message_size: "Max Message Size (bytes)",
            quota_default: "Default Quota (bytes)",
            spam_threshold: "Spam Score Threshold",
            greylist_enabled: "Greylisting Enabled",
            antivirus_enabled: "Antivirus Enabled",
            welcome_email_enabled: "Send Welcome Email",
            autoconfig_enabled: "Autoconfig/Autodiscover Enabled",
        };
        container.innerHTML = settings.map(s => `
            <div class="form-group">
                <label>${labels[s.key] || s.key}</label>
                <input type="text" id="setting-${s.key}" value="${esc(s.value)}" data-key="${esc(s.key)}">
            </div>
        `).join("") + `
            <button class="btn btn-primary" onclick="Pages.saveSettings()">Save Settings</button>
        `;
    },

    async saveSettings() {
        const inputs = document.querySelectorAll("#settings-form input[data-key]");
        try {
            for (const input of inputs) {
                await API.put("/api/settings/", { key: input.dataset.key, value: input.value });
            }
            toast("Settings saved");
        } catch (err) { toast(err.message, "error"); }
    },
};

/* ── HTML Escaping ───────────────────────────────────── */
function esc(str) {
    const div = document.createElement("div");
    div.textContent = str || "";
    return div.innerHTML;
}

/* ── Login Handler ───────────────────────────────────── */
async function handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById("login-email").value;
    const password = document.getElementById("login-password").value;
    try {
        const data = await API.request("POST", "/api/auth/login", { email, password });
        if (data) {
            API.login(data.access_token);
            App.showApp();
            App.navigate("dashboard");
        }
    } catch (err) {
        toast(err.message, "error");
    }
}

/* ── Navigation Handler ──────────────────────────────── */
document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".sidebar nav a").forEach(a => {
        a.addEventListener("click", e => {
            e.preventDefault();
            App.navigate(a.dataset.page);
        });
    });
    App.init();
});
