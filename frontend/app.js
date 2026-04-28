// ============================================================
// CONSTANTS
// ============================================================
const API_URL = ""; 
const SUMMARIZER_API = "/api/summarize";

// ============================================================
// STATE
// ============================================================
let editingId   = null;
let deletingId  = null;
let currentPage = "home";
let selectedTags  = [];   // tags currently selected in the modal
let allTags       = [];   // all tags fetched from GET /tags
let currentDept = "CS";
let currentType = null;

// ============================================================
// ELEMENT REFS
// ============================================================
const resourceModal   = document.getElementById("resource-modal");
const confirmModal    = document.getElementById("confirm-modal");
const modalTitle      = document.getElementById("modal-title");
const inputTitle      = document.getElementById("input-title");
const inputLink       = document.getElementById("input-link");
const inputDesc       = document.getElementById("input-description");
const inputDept       = document.getElementById("input-department");
const inputType       = document.getElementById("input-type");
const btnSave         = document.getElementById("btn-save");
const btnConfirmDel   = document.getElementById("btn-confirm-delete");
const btnConfirmCan   = document.getElementById("btn-confirm-cancel");
const searchInput     = document.getElementById("search-input");
const filterDept      = document.getElementById("filter-department");
const filterType      = document.getElementById("filter-type");
const globalSearch    = document.getElementById("global-search");

// ============================================================
// HELPERS — THUMBNAIL
// ============================================================

function getYouTubeId(url) {
    if (!url) return null;
    const patterns = [
        /youtube\.com\/watch\?v=([^&]+)/,
        /youtu\.be\/([^?]+)/,
        /youtube\.com\/embed\/([^?]+)/,
        /youtube\.com\/shorts\/([^?]+)/,
    ];
    for (const p of patterns) {
        const m = url.match(p);
        if (m) return m[1];
    }
    return null;
}

function buildThumbnail(resource) {
    const type = resource.resource_type;
    const ytId  = (type === "Video" || type === "Playlist") ? getYouTubeId(resource.link) : null;

    if (ytId) {
        const img = document.createElement("img");
        img.className = "res-thumb";
        img.alt = resource.title;
        img.src = `https://img.youtube.com/vi/${ytId}/hqdefault.jpg`;
        img.onerror = () => { img.replaceWith(iconPlaceholder(type)); };
        return img;
    }
    return iconPlaceholder(type);
}

function iconPlaceholder(type) {
    const div = document.createElement("div");
    const cls = typeClass(type);
    div.className = `res-thumb-placeholder type-${cls}`;
    div.textContent = typeEmoji(type);
    return div;
}

// ============================================================
// HELPERS — TYPE STYLING
// ============================================================
function typeClass(type) {
    const map = { "Video": "yt", "Playlist": "pl", "Website": "web", "Github Repo": "gh" };
    return map[type] || "web";
}

function typeEmoji(type) {
    const map = { "Video": "▶", "Playlist": "☰", "Website": "◈", "Github Repo": "◎" };
    return map[type] || "◈";
}

function typeBadgeClass(type) {
    const map = { "Video": "badge-yt", "Playlist": "badge-pl", "Website": "badge-web", "Github Repo": "badge-gh" };
    return map[type] || "badge-web";
}

function typeLabel(type) {
    const map = { "Video": "YouTube Video", "Playlist": "YouTube Playlist", "Website": "Website", "Github Repo": "GitHub Repo" };
    return map[type] || type;
}

function openBtnClass(type) {
    const map = { "Video": "btn-open-yt", "Playlist": "btn-open-pl", "Website": "btn-open-web", "Github Repo": "btn-open-gh" };
    return map[type] || "btn-open-web";
}

function deptLabel(dept) {
    const map = { "CS": "Computer Science", "ECE": "Electronics", "Other": "Other Fun Stuff" };
    return map[dept] || dept;
}

// ============================================================
// BUILD RESOURCE ITEM
// ============================================================
function buildResourceItem(resource) {
    const item = document.createElement("div");
    item.className = "resource-item";

    item.appendChild(buildThumbnail(resource));

    const body = document.createElement("div");
    body.className = "res-body";
    const tagHTML = resource.tags && resource.tags.length
        ? `<div class="res-tags">${resource.tags.map(t =>
            `<span class="tag-chip-card">${t.name}</span>`).join("")}</div>`
        : "";

    body.innerHTML = `
        <div>
            <span class="res-type-badge ${typeBadgeClass(resource.resource_type)}">
                ${typeLabel(resource.resource_type)}
            </span>
            <span class="res-type-badge badge-dept" style="margin-left:6px;">${deptLabel(resource.domain)}</span>
        </div>
        <a class="res-title-link" href="${resource.link}" target="_blank" rel="noopener">${resource.title}</a>
        <p class="res-desc">${resource.description || "No description provided."}</p>
        ${tagHTML}
    `;
    item.appendChild(body);

    const actions = document.createElement("div");
    actions.className = "res-actions";

    const openBtn = document.createElement("a");
    openBtn.href = resource.link;
    openBtn.target = "_blank";
    openBtn.rel = "noopener";
    openBtn.className = `btn-open ${openBtnClass(resource.resource_type)}`;
    openBtn.innerHTML = `<span class="material-symbols-outlined">open_in_new</span> Open`;

    const editRow = document.createElement("div");
    editRow.className = "res-edit-row";

    const editBtn = document.createElement("button");
    editBtn.className = "btn-icon btn-icon-edit";
    editBtn.title = "Edit";
    editBtn.innerHTML = `<span class="material-symbols-outlined">edit</span>`;
    editBtn.onclick = () => openEditModal(resource.id);

    const delBtn = document.createElement("button");
    delBtn.className = "btn-icon btn-icon-del";
    delBtn.title = "Delete";
    delBtn.innerHTML = `<span class="material-symbols-outlined">delete</span>`;
    delBtn.onclick = () => openDeleteConfirm(resource.id);

    editRow.appendChild(editBtn);
    editRow.appendChild(delBtn);
    actions.appendChild(openBtn);
    actions.appendChild(editRow);
    item.appendChild(actions);

    return item;
}

// ============================================================
// NAVIGATION
// ============================================================
function navigate(page, param = null) {
    document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
    document.querySelectorAll(".sidebar-link").forEach(l => l.classList.remove("active"));

    currentPage = page;

    if (page === "home") {
        document.getElementById("page-home").classList.add("active");
        document.getElementById("link-home").classList.add("active");
        setBreadcrumb([{ label: "Home" }]);
        loadHomeData();

    } else if (page === "dept") {
        currentDept = param || currentDept;
        currentType = null;
        document.getElementById("page-dept").classList.add("active");
        document.getElementById("link-dept").classList.add("active");
        setBreadcrumb([
            { label: "Home", action: () => navigate("home") },
            { label: deptLabel(currentDept) }
        ]);
        loadDeptPage(currentDept);

    } else if (page === "resources") {
        document.getElementById("page-resources").classList.add("active");
        document.getElementById("link-resources").classList.add("active");
        setBreadcrumb([
            { label: "Home", action: () => navigate("home") },
            { label: "All Resources" }
        ]);
        loadAllResources();
    }
}

// ============================================================
// BREADCRUMB
// ============================================================
function setBreadcrumb(items) {
    const bc = document.getElementById("breadcrumb");
    bc.innerHTML = "";
    items.forEach((item, i) => {
        const span = document.createElement("span");
        span.className = "bc-item";
        if (i < items.length - 1) {
            span.innerHTML = `<span class="bc-link">${item.label}</span><span class="bc-sep">›</span>`;
            span.querySelector(".bc-link").onclick = item.action || null;
        } else {
            span.innerHTML = `<span class="bc-current">${item.label}</span>`;
        }
        bc.appendChild(span);
    });
}

// ============================================================
// HOME PAGE DATA
// ============================================================
async function loadHomeData() {
    try {
        const response  = await fetch(`${API_URL}/resources`);
        const resources = await response.json();

        document.getElementById("stat-total").textContent = resources.length;

        const domainCounts = { CS: 0, ECE: 0, Other: 0 };
        resources.forEach(r => { if (domainCounts[r.domain] !== undefined) domainCounts[r.domain]++; });
        document.getElementById("count-CS").textContent    = `${domainCounts.CS} resources`;
        document.getElementById("count-ECE").textContent   = `${domainCounts.ECE} resources`;
        document.getElementById("count-Other").textContent = `${domainCounts.Other} resources`;

        document.getElementById("sc-total").textContent = resources.length;

        const topDomain = Object.entries(domainCounts).sort((a,b) => b[1]-a[1])[0];
        const domainNames = { CS: "Computer Science", ECE: "Electronics", Other: "Other Fun Stuff" };
        document.getElementById("sc-top-domain").textContent =
            resources.length === 0 ? "—" : `${domainNames[topDomain[0]]}`;

        const mediaCount = resources.filter(r => r.resource_type === "Video" || r.resource_type === "Playlist").length;
        document.getElementById("sc-videos").textContent = mediaCount;

        const newest = resources.length > 0 ? resources[resources.length - 1] : null;
        document.getElementById("sc-newest").textContent = newest ? newest.title : "None yet";

        const typeCounts = { "Video": 0, "Playlist": 0, "Website": 0, "Github Repo": 0 };
        resources.forEach(r => { if (typeCounts[r.resource_type] !== undefined) typeCounts[r.resource_type]++; });
        const total = resources.length || 1;

        const barConfig = [
            { key: "Video",       cls: "bar-yt",  label: "Video",   dot: "#ef4444" },
            { key: "Playlist",    cls: "bar-pl",  label: "Playlist",dot: "#d97706" },
            { key: "Website",     cls: "bar-web", label: "Website", dot: "#2563eb" },
            { key: "Github Repo", cls: "bar-gh",  label: "GitHub",  dot: "#1e293b" },
        ];

        const barsEl   = document.getElementById("breakdown-bars");
        const legendEl = document.getElementById("breakdown-legend");
        barsEl.innerHTML   = "";
        legendEl.innerHTML = "";

        barConfig.forEach(({ key, cls, label, dot }) => {
            const pct = Math.round((typeCounts[key] / total) * 100);
            if (pct > 0) {
                const bar = document.createElement("div");
                bar.className = `breakdown-bar ${cls}`;
                bar.style.width = `${pct}%`;
                bar.title = `${label}: ${typeCounts[key]}`;
                barsEl.appendChild(bar);
            }
            const li = document.createElement("div");
            li.className = "legend-item";
            li.innerHTML = `<div class="legend-dot" style="background:${dot}"></div>${label} <strong>${typeCounts[key]}</strong>`;
            legendEl.appendChild(li);
        });

    } catch (err) {
        console.error("Failed to load home data:", err);
    }
}

// ============================================================
// DEPARTMENT PAGE
// ============================================================
async function loadDeptPage(dept) {
    try {
        // FIX: was ?department= — backend expects ?domain=
        const response  = await fetch(`${API_URL}/resources?domain=${dept}`);
        const resources = await response.json();

        const heroConfig = {
            CS:    { label: "Computer Science", sub: "Algorithms, data structures, AI, and software engineering.", icon: "terminal",  cls: "dept-cs"    },
            ECE:   { label: "Electronics",       sub: "Circuits, microcontrollers, and embedded systems.",          icon: "memory",    cls: "dept-ece"   },
            Other: { label: "Other Fun Stuff",   sub: "Curiosity-driven learning beyond the syllabus.",            icon: "explore",   cls: "dept-other" },
        };
        const cfg = heroConfig[dept] || heroConfig.CS;
        const hero = document.getElementById("dept-page-hero");
        hero.className = `dept-page-hero ${cfg.cls}`;
        hero.innerHTML = `
            <div class="dept-icon ${`dept-icon-${dept.toLowerCase().replace(' ','-')}`}">
                <span class="material-symbols-outlined" style="font-variation-settings:'FILL' 1">${cfg.icon}</span>
            </div>
            <div>
                <div class="dept-hero-title">${cfg.label}</div>
                <div class="dept-hero-sub">${cfg.sub}</div>
            </div>
        `;

        const types = ["Video", "Playlist", "Website", "Github Repo"];
        const counts = {};
        types.forEach(t => counts[t] = 0);
        resources.forEach(r => { if (counts[r.resource_type] !== undefined) counts[r.resource_type]++; });

        const catGrid = document.getElementById("cat-grid");
        catGrid.innerHTML = "";
        const typeConfig = {
            "Video":       { cls: "cat-yt",  emoji: "▶", label: "YouTube Videos"  },
            "Playlist":    { cls: "cat-pl",  emoji: "☰", label: "Playlists"       },
            "Website":     { cls: "cat-web", emoji: "◈", label: "Websites"        },
            "Github Repo": { cls: "cat-gh",  emoji: "◎", label: "GitHub Repos"    },
        };
        types.forEach(type => {
            const tc = typeConfig[type];
            const chip = document.createElement("div");
            chip.className = `cat-chip ${tc.cls}`;
            chip.innerHTML = `
                <div class="cat-stripe"></div>
                <div class="cat-icon-wrap">${tc.emoji}</div>
                <div class="cat-label">${tc.label}</div>
                <div class="cat-count">${counts[type]} resource${counts[type] !== 1 ? 's' : ''}</div>
            `;
            chip.onclick = () => loadDeptTypeResources(dept, type, chip);
            catGrid.appendChild(chip);
        });

        document.getElementById("dept-resources-section").style.display = "none";

    } catch (err) {
        console.error("Failed to load dept page:", err);
    }
}

async function loadDeptTypeResources(dept, type, chipEl) {
    document.querySelectorAll(".cat-chip").forEach(c => c.classList.remove("active"));
    chipEl.classList.add("active");
    currentType = type;

    setBreadcrumb([
        { label: "Home",               action: () => navigate("home") },
        { label: deptLabel(dept),      action: () => navigate("dept", dept) },
        { label: typeLabel(type) }
    ]);

    try {
        // FIX: was ?department= — backend expects ?domain=
        const response  = await fetch(`${API_URL}/resources?domain=${dept}&resource_type=${encodeURIComponent(type)}`);
        const resources = await response.json();

        const section = document.getElementById("dept-resources-section");
        const list    = document.getElementById("dept-resources-list");
        const title   = document.getElementById("dept-resources-title");

        section.style.display = "block";
        title.textContent = `${typeLabel(type)} — ${deptLabel(dept)}`;
        list.innerHTML = "";

        if (resources.length === 0) {
            list.innerHTML = `<div class="empty-state"><span class="material-symbols-outlined">search_off</span>No ${type} resources in ${deptLabel(dept)} yet.</div>`;
        } else {
            resources.forEach(r => list.appendChild(buildResourceItem(r)));
        }

        section.scrollIntoView({ behavior: "smooth", block: "start" });

    } catch (err) {
        console.error("Failed to load dept type resources:", err);
    }
}

// ============================================================
// ALL RESOURCES PAGE
// ============================================================
async function loadAllResources() {
    const params = new URLSearchParams();
    const search = searchInput ? searchInput.value.trim() : "";
    const dept   = filterDept  ? filterDept.value  : "";
    const type   = filterType  ? filterType.value  : "";
    if (search) params.append("title", search);
    // FIX: was "department" — backend expects "domain"
    if (dept)   params.append("domain", dept);
    if (type)   params.append("resource_type", type);

    try {
        const response  = await fetch(`${API_URL}/resources?${params}`);
        const resources = await response.json();
        const container = document.getElementById("resources-container");
        container.innerHTML = "";
        if (resources.length === 0) {
            container.innerHTML = `<div class="empty-state"><span class="material-symbols-outlined">search_off</span>No resources found.</div>`;
        } else {
            resources.forEach(r => container.appendChild(buildResourceItem(r)));
        }
    } catch (err) {
        console.error("Failed to load resources:", err);
    }
}

// ============================================================
// TAG SYSTEM
// ============================================================
async function loadAllTags() {
    try {
        const response = await fetch(`${API_URL}/tags`);
        allTags = await response.json();
    } catch (err) {
        console.error("Failed to load tags:", err);
    }
}

function renderTagPresets() {
    const container = document.getElementById("tag-presets");
    if (!container) return;
    container.innerHTML = "";
    allTags.forEach(tag => {
        const btn = document.createElement("button");
        btn.className = "tag-preset-btn" + (selectedTags.includes(tag.name) ? " used" : "");
        btn.textContent = tag.name;
        btn.type = "button";
        btn.onclick = () => addTag(tag.name);
        container.appendChild(btn);
    });
}

function addTag(name) {
    name = name.trim().toLowerCase();
    if (!name || selectedTags.includes(name)) return;
    selectedTags.push(name);
    renderSelectedTags();
    renderTagPresets();
}

function removeTag(name) {
    selectedTags = selectedTags.filter(t => t !== name);
    renderSelectedTags();
    renderTagPresets();
}

function renderSelectedTags() {
    const container = document.getElementById("tag-selected");
    if (!container) return;
    container.innerHTML = "";
    selectedTags.forEach(name => {
        const pill = document.createElement("span");
        pill.className = "tag-pill-selected";
        pill.innerHTML = `${name}<button onclick="removeTag('${name}')" title="Remove">×</button>`;
        container.appendChild(pill);
    });
}

function initTagInput() {
    const input = document.getElementById("tag-input");
    if (!input) return;
    input.addEventListener("keydown", e => {
        if (e.key === "Enter" || e.key === ",") {
            e.preventDefault();
            const val = input.value.trim().replace(/,$/, "");
            if (val) { addTag(val); input.value = ""; }
        }
        if (e.key === "Backspace" && input.value === "" && selectedTags.length > 0) {
            removeTag(selectedTags[selectedTags.length - 1]);
        }
    });
    input.addEventListener("blur", () => {
        const val = input.value.trim();
        if (val) { addTag(val); input.value = ""; }
    });
    document.getElementById("tag-input-wrap").addEventListener("click", () => input.focus());
}

// ============================================================
// MODAL — ADD
// ============================================================
function openAddModal() {
    editingId = null;
    modalTitle.textContent = "Add Resource";
    inputTitle.value = "";
    inputLink.value  = "";
    inputDesc.value  = "";
    inputDept.value  = "CS";
    inputType.value  = "Video";
    selectedTags = [];
    renderSelectedTags();
    renderTagPresets();
    initTagInput();
    resourceModal.classList.remove("hidden");
}

// ============================================================
// MODAL — EDIT
// ============================================================
async function openEditModal(id) {
    editingId = id;
    modalTitle.textContent = "Edit Resource";
    try {
        const response = await fetch(`${API_URL}/resources/${id}`);
        const resource = await response.json();
        inputTitle.value = resource.title;
        inputLink.value  = resource.link;
        inputDesc.value  = resource.description || "";
        inputDept.value  = resource.domain;
        inputType.value  = resource.resource_type;
        selectedTags = resource.tags ? resource.tags.map(t => t.name) : [];
        renderSelectedTags();
        renderTagPresets();
        initTagInput();
        resourceModal.classList.remove("hidden");
    } catch (err) {
        console.error("Failed to load resource for edit:", err);
    }
}

function closeModal() {
    resourceModal.classList.add("hidden");
}

// ============================================================
// MODAL — DELETE
// ============================================================
function openDeleteConfirm(id) {
    deletingId = id;
    confirmModal.classList.remove("hidden");
}

function closeConfirmModal() {
    deletingId = null;
    confirmModal.classList.add("hidden");
}

// ============================================================
// SAVE — create or update
// ============================================================
async function saveResource() {
    const tagInputEl = document.getElementById("tag-input");
    if (tagInputEl && tagInputEl.value.trim()) {
        addTag(tagInputEl.value.trim());
        tagInputEl.value = "";
    }

    const body = {
        title:         inputTitle.value.trim(),
        link:          inputLink.value.trim(),
        description:   inputDesc.value.trim(),
        domain:        inputDept.value,
        resource_type: inputType.value,
        tags:          [...selectedTags],
    };

    if (!body.title || !body.link) {
        alert("Title and Link are required.");
        return;
    }

    const method = editingId === null ? "POST" : "PUT";
    const url    = editingId === null
        ? `${API_URL}/resources/`
        : `${API_URL}/resources/${editingId}`;

    try {
        await fetch(url, {
            method,
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        });
        closeModal();
        refreshCurrentPage();
    } catch (err) {
        console.error("Failed to save resource:", err);
    }
}

// ============================================================
// DELETE
// ============================================================
async function deleteResource() {
    try {
        await fetch(`${API_URL}/resources/${deletingId}`, { method: "DELETE" });
        closeConfirmModal();
        refreshCurrentPage();
    } catch (err) {
        console.error("Failed to delete resource:", err);
    }
}

// ============================================================
// AI SUMMARIZER
// ============================================================
async function autoSummarize() {
    const url = inputLink.value.trim();
    const statusEl = document.getElementById("summarize-status");
    const btnSummarize = document.getElementById("btn-summarize");

    if (!url) {
        alert("Please paste a link first!");
        return;
    }

    statusEl.style.display = "block";
    statusEl.innerText = "✨ Gemini is thinking...";
    btnSummarize.disabled = true;
    inputDesc.placeholder = "Gemini is thinking...";

    try {
        const response = await fetch(SUMMARIZER_API, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url })
        });

        const data = await response.json();

        if (data.success) {
            // Always fill description
            inputDesc.value = data.summary || "";

            // Fill title — ask first if field already has content
            if (data.title) {
                if (inputTitle.value.trim() === "") {
                    inputTitle.value = data.title;
                } else {
                    const overwrite = confirm(
                        `AI suggested this title:\n\n"${data.title}"\n\nReplace your current title?`
                    );
                    if (overwrite) inputTitle.value = data.title;
                }
            }

            statusEl.innerText = "✨ Done!";
            setTimeout(() => { statusEl.style.display = "none"; }, 3000);
        } else {
            throw new Error(data.error || "Unknown error");
        }
    } catch (error) {
        statusEl.innerText = "❌ Could not summarize.";
        inputDesc.placeholder = "Enter description manually...";
    } finally {
        btnSummarize.disabled = false;
    }
}

// ============================================================
// REFRESH
// ============================================================
function refreshCurrentPage() {
    if (currentPage === "home")           loadHomeData();
    else if (currentPage === "dept")      loadDeptPage(currentDept);
    else if (currentPage === "resources") loadAllResources();
}

// ============================================================
// EVENT LISTENERS
// ============================================================
btnSave.addEventListener("click", saveResource);

document.getElementById("btn-summarize").addEventListener("click", (e) => {
    e.preventDefault();
    autoSummarize();
});

btnConfirmDel.addEventListener("click", deleteResource);
btnConfirmCan.addEventListener("click", closeConfirmModal);

if (searchInput) searchInput.addEventListener("input", loadAllResources);
if (filterDept)  filterDept.addEventListener("change", loadAllResources);
if (filterType)  filterType.addEventListener("change", loadAllResources);

if (globalSearch) {
    globalSearch.addEventListener("keydown", e => {
        if (e.key === "Enter" && globalSearch.value.trim()) {
            navigate("resources");
            setTimeout(() => {
                if (searchInput) {
                    searchInput.value = globalSearch.value.trim();
                    loadAllResources();
                }
            }, 50);
        }
    });
}

document.getElementById("resource-modal").addEventListener("click", function(e) {
    if (e.target === this) closeModal();
});
document.getElementById("confirm-modal").addEventListener("click", function(e) {
    if (e.target === this) closeConfirmModal();
});

// ============================================================
// INIT
// ============================================================
loadAllTags();
navigate("home");