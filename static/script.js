const BASE_URL = window.location.origin;

// ================= REGISTER =================
async function register() {
    const usernameEl = document.getElementById("username");
    const passwordEl = document.getElementById("password");
    const roleEl = document.getElementById("role");

    if (!usernameEl || !passwordEl || !roleEl) {
        alert("Form elements not found");
        return;
    }

    const username = usernameEl.value;
    const password = passwordEl.value;
    const role = roleEl.value;

    const res = await fetch(`${BASE_URL}/register`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ username, password, role })
    });

    const data = await res.json();

    if (res.ok) {
        alert("Registered successfully");

        if (role === "admin") window.location.href = "admin.html";
        else if (role === "student" || role === "teacher") window.location.href = "/static/student.html";
        else window.location.href = "/static/staff.html";

    } else {
        alert(data.detail);
    }
}

// ================= LOGIN =================
async function login() {
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;
    const role = document.getElementById("role").value;

    const res = await fetch(`${BASE_URL}/login`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ username, password, role })
    });

    if (!res.ok) {
        alert("Invalid login ❌");
        return;
    }

    const data = await res.json();
    localStorage.setItem("user", JSON.stringify(data));

    if (data.role === "admin") window.location.href = "/static/admin.html";
    else if (data.role === "student" || data.role === "teacher") window.location.href = "/static/student.html";
    else window.location.href = "/static/staff.html";
}

// ================= CREATE COMPLAINT =================
async function createComplaint() {
    const user = JSON.parse(localStorage.getItem("user"));
    if (!user) {
        alert("Login again");
        return;
    }

    // ✅ GET VALUES
    const title = document.getElementById("title")?.value;
    const description = document.getElementById("description")?.value;
    const category = document.getElementById("category")?.value;
    const sub_category = document.getElementById("subcategory")?.value;
    const priority = document.getElementById("priority")?.value;

    console.log("SENDING:", { title, description, category, sub_category, priority });

    // ❗ VALIDATION
    if (!title || !description || !category) {
        alert("Fill all required fields");
        return;
    }

    let filePath = null;
    const fileInput = document.getElementById("fileInput");

    if (fileInput && fileInput.files.length > 0) {
        const formData = new FormData();
        formData.append("file", fileInput.files[0]);

        const uploadRes = await fetch(`${BASE_URL}/upload`, {
            method: "POST",
            body: formData
        });

        const uploadData = await uploadRes.json();
        filePath = uploadData.file_path;
    }

    // ✅ SEND DATA
    const res = await fetch(`${BASE_URL}/create-complaint`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            title,
            description,
            category,
            sub_category,
            priority,
            user_id: user.id,
            file_path: filePath
        })
    });

    const data = await res.json();
    console.log("RESPONSE:", data);

    alert("Complaint submitted");

    loadUserComplaints();
}

// ================= USER COMPLAINTS =================
async function loadUserComplaints() {
    const user = JSON.parse(localStorage.getItem("user"));
    if (!user) return;

    const res = await fetch(`${BASE_URL}/user-complaints/${user.id}`);
    const complaints = await res.json();

    const container = document.getElementById("complaintList");
    container.innerHTML = "";

    if (!complaints.length) {
        container.innerHTML = "<p>No complaints found</p>";
        return;
    }

    complaints.forEach(c => {
        container.innerHTML += `
            <div class="card">
                <h4>${c.title}</h4>
                <p>${c.description}</p>
                <p><b>Category:</b> ${c.category}</p>
                <p><b>Status:</b> ${c.status}</p>

                ${c.file_path ? `<img src="${BASE_URL}/${c.file_path}" width="120">` : ""}

                <!-- 💬 CHAT SECTION -->
                <div id="chat-${c.id}" class="chat-box"></div>

                <input id="msg-${c.id}" placeholder="Type message">
                <button onclick="sendMessage(${c.id})">Send</button>
            </div>
        `;

        // ✅ VERY IMPORTANT (loads messages)
        loadMessages(c.id);
    });
}

// ================= STAFF =================
async function loadAssignedComplaints() {
    const user = JSON.parse(localStorage.getItem("user"));
    if (!user) return;

    const staffId = parseInt(user.id);

    const res = await fetch(`${BASE_URL}/staff-complaints/${staffId}`);
    const data = await res.json();

    const list = document.getElementById("assignedList");
    list.innerHTML = "";

    if (!data.length) {
        list.innerHTML = "<p>No assigned complaints</p>";
        return;
    }

    data.forEach(c => {
        list.innerHTML += `
            <div class="card">
                <h4>${c.title}</h4>
                <p>${c.description}</p>
                <p><b>Status:</b> ${c.status}</p>

                <!-- 💬 CHAT SECTION -->
                <div id="chat-${c.id}" class="chat-box"></div>

                <input id="msg-${c.id}" placeholder="Type message">
                <button onclick="sendMessage(${c.id})">Send</button>

                <br><br>

                <!-- ⚙️ ACTIONS -->
                <button onclick="updateStatus(${c.id}, 'Closed')">Resolve</button>
                <button onclick="updateStatus(${c.id}, 'In Progress')">This will take time</button>
            </div>
        `;

        // ✅ VERY IMPORTANT (load chat messages)
        loadMessages(c.id);
    });
}

// ================= UPDATE STATUS =================
async function updateStatus(id, status) {
    await fetch(`${BASE_URL}/update-status/${id}`, {
        method: "PUT",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ status })
    });

    alert("Updated");
    loadAssignedComplaints();
}

// ================= COMMENT =================
async function addComment(id) {
    const comment = document.getElementById(`comment-${id}`).value;

    await fetch(`${BASE_URL}/add-comment/${id}`, {
        method: "PUT",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ comment })
    });

    alert("Comment added");
    loadAssignedComplaints();
}

// ================= ADMIN =================
async function loadStaffList() {
    const res = await fetch(`${BASE_URL}/all-staff`);
    const data = await res.json();

    const list = document.getElementById("staffList");
    list.innerHTML = "";

    data.forEach(s => {
        list.innerHTML += `
            <div class="card">
                <p>ID: ${s.id}</p>
                <p>${s.username}</p>
                <p>${s.role}</p>
            </div>
        `;
    });
}

async function loadAllComplaints() {
    const res = await fetch(`${BASE_URL}/all-complaints`);
    const data = await res.json();

    const list = document.getElementById("allComplaints");
    list.innerHTML = "";

    data.forEach(c => {
        list.innerHTML += `
            <div class="card">
                <h4>${c.title}</h4>
                <p>${c.description}</p>
                <p>${c.category}</p>
                <button onclick="assignComplaint(${c.id})">Assign</button>
            </div>
        `;
    });
}

async function assignComplaint(id) {
    const res = await fetch(`${BASE_URL}/all-staff`);
    const staffList = await res.json();

    let options = staffList.map(s => 
        `${s.id} - ${s.role}`
    ).join("\n");

    const staffId = prompt("Select Staff ID:\n" + options);

    if (!staffId) return;

    await fetch(`${BASE_URL}/assign-complaint/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ staff_id: staffId })
    });

    alert("Assigned successfully");
    loadAllComplaints();
}

// ================= CSV =================
function downloadUserCSV() {
    const user = JSON.parse(localStorage.getItem("user"));
    window.open(`${BASE_URL}/download-user/${user.id}`);
}

function downloadStaffCSV() {
    const user = JSON.parse(localStorage.getItem("user"));
    const staffId = parseInt(user.id); // 🔥 FIX
    window.open(`${BASE_URL}/download-staff/${staffId}`);
}

function downloadAllCSV() {
    window.open(`${BASE_URL}/download-all`);
}

// ================= LOGOUT =================
function logout() {
    localStorage.removeItem("user");
    window.location.href = "/static/login.html";
}

// ================= SUBCATEGORY =================
const subcategories = {
    Academic: ["Faculty", "Exam", "Time Table", "Other"],
    Hostel: ["Maintenance", "Mess", "Roommate Issues", "Other"],
    Infrastructure: ["Campus Facilities", "WiFi/Internet", "Labs", "Other"],
    Administrative: ["Fees", "Certificate", "Documents", "Other"]
};

const categoryEl = document.getElementById("category");

if (categoryEl) {
    categoryEl.addEventListener("change", function () {
        const subSelect = document.getElementById("subcategory");
        subSelect.innerHTML = '<option>Select Sub Category</option>';

        subcategories[this.value]?.forEach(sub => {
            const option = document.createElement("option");
            option.value = sub;
            option.textContent = sub;
            subSelect.appendChild(option);
        });
    });
}
async function filterComplaints() {
    const status = document.getElementById("filterStatus").value;
    const category = document.getElementById("filterCategory").value;

    let url = `${BASE_URL}/filter-complaints?`;

    if (status) url += `status=${status}&`;
    if (category) url += `category=${category}`;

    const res = await fetch(url);

    if (!res.ok) {
        alert("Filter API not working ❌");
        return;
    }

    const data = await res.json();

    const list = document.getElementById("allComplaints");
    list.innerHTML = "";

    if (!Array.isArray(data)) {
        list.innerHTML = "<p>Error loading data</p>";
        return;
    }

    data.forEach(c => {
        list.innerHTML += `
            <div class="card">
                <h4>${c.title}</h4>
                <p>${c.description}</p>

                <p><b>Category:</b> ${c.category}</p>
                <p><b>Status:</b> ${c.status}</p>

                <button onclick="assignComplaint(${c.id})">Assign</button>

                <hr>
            </div>
        `;
    });
}
async function loadAdminStats() {
    const res = await fetch(`${BASE_URL}/admin-stats`);
    const data = await res.json();

    // Update numbers
    document.getElementById("totalCount").innerText = data.total;
    document.getElementById("resolvedCount").innerText = data.resolved;
    document.getElementById("pendingCount").innerText = data.pending;

    // Draw graph
    const ctx = document.getElementById("complaintChart").getContext("2d");

    new Chart(ctx, {
        type: "bar",
        data: {
            labels: ["Total", "Resolved", "Pending"],
            datasets: [{
                label: "Complaints Overview",
                data: [data.total, data.resolved, data.pending],
                backgroundColor: ["blue", "green", "orange"]
            }]
        },
        options: {
            responsive: true
        }
    });
}
if (window.location.pathname.includes("admin.html")) {
    loadAdminStats();
}
async function sendMessage(complaintId) {
    const user = JSON.parse(localStorage.getItem("user"));
    const msgInput = document.getElementById(`msg-${complaintId}`);
    const message = msgInput.value;

    if (!message) return;

    await fetch(`${BASE_URL}/add-message`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            complaint_id: complaintId,
            user_id: user.id,
            message: message
        })
    });

    msgInput.value = "";
    loadMessages(complaintId);
}

async function loadMessages(complaintId) {
    const res = await fetch(`${BASE_URL}/get-messages/${complaintId}`);
    const data = await res.json();

    const chatBox = document.getElementById(`chat-${complaintId}`);
    if (!chatBox) return;

    chatBox.innerHTML = "";

    data.forEach(m => {
        chatBox.innerHTML += `<p><b>User ${m.user_id}:</b> ${m.message}</p>`;
    });
}
async function loadNotifications() {
    const user = JSON.parse(localStorage.getItem("user"));
    if (!user) return;

    const res = await fetch(`${BASE_URL}/notifications/${user.id}`);
    const data = await res.json();

    const box = document.getElementById("notifications");
    box.innerHTML = "";

    if (!data.length) {
        box.innerHTML = "<p>No notifications</p>";
        return;
    }

    data.forEach(n => {
        box.innerHTML += `
            <div class="card">
                <p>${n.message}</p>
            </div>
        `;
    });
}
let notifVisible = false;

async function toggleNotifications() {
    const box = document.getElementById("notifications");
    const btn = document.getElementById("notifBtn");

    notifVisible = !notifVisible;

    if (notifVisible) {
        box.style.display = "block";
        btn.innerText = "❌ Hide Notifications";

        const user = JSON.parse(localStorage.getItem("user"));
        if (!user) return;

        const res = await fetch(`${BASE_URL}/notifications/${user.id}`);
        const data = await res.json();

        box.innerHTML = "";

        if (!data.length) {
            box.innerHTML = "<p>No notifications</p>";
            return;
        }

        data.forEach(n => {
            box.innerHTML += `
                <div class="card">
                    <p>${n.message}</p>
                </div>
            `;
        });

    } else {
        box.style.display = "none";
        btn.innerText = "🔔 Show Notifications";
    }
}