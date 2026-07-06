const VAULT = "http://127.0.0.1:8001";

const token = localStorage.getItem("token");

if (!token) {
    window.location = "index.html";
}

document.getElementById("logoutBtn").onclick = () => {
    localStorage.removeItem("token");
    window.location = "index.html";
};


// Upload PDF
document.getElementById("uploadBtn").onclick = async () => {
    const fileInput = document.getElementById("pdfFile");

    if (fileInput.files.length === 0) {
        alert("Please choose a PDF file");
        return;
    }

    const file = fileInput.files[0];

    document.getElementById("uploadStatus").innerText =
        "Generating upload URL...";

    const response = await fetch(VAULT + "/upload-url", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token
        },
        body: JSON.stringify({
            filename: file.name
        })
    });

    const data = await response.json();

    if (!response.ok) {
        alert(data.detail || "Could not generate upload URL");
        return;
    }

    document.getElementById("uploadStatus").innerText =
        "Uploading file to S3...";

    const uploadResponse = await fetch(data.upload_url, {
        method: "PUT",
        body: file
    });

    if (!uploadResponse.ok) {
        document.getElementById("uploadStatus").innerText =
            "Upload failed";
        return;
    }

    document.getElementById("uploadStatus").innerText =
        "Upload successful. Lambda is processing...";

    fileInput.value = "";

    setTimeout(async () => {
        await fetch(VAULT + "/complete/" + data.file_key, {
            method: "PUT"
        });

        document.getElementById("uploadStatus").innerText =
            "Processing complete.";

        loadDocuments();

    }, 10000);

    loadDocuments();
};


// Load Documents
async function loadDocuments() {
    const response = await fetch(VAULT + "/documents", {
        headers: {
            "Authorization": "Bearer " + token
        }
    });

    const data = await response.json();

    const ownedContainer =
        document.getElementById("ownedDocumentsContainer");

    const sharedContainer =
        document.getElementById("sharedDocumentsContainer");

    ownedContainer.innerHTML = "";
    sharedContainer.innerHTML = "";

    const ownedDocs = data.owned || [];
    const sharedDocs = data.shared || [];

    if (ownedDocs.length === 0) {
        ownedContainer.innerHTML = "<p>No documents uploaded yet.</p>";
    }

    if (sharedDocs.length === 0) {
        sharedContainer.innerHTML = "<p>No documents shared with you.</p>";
    }

    ownedDocs.forEach(doc => {
        ownedContainer.innerHTML += createOwnedCard(doc);
    });

    sharedDocs.forEach(doc => {
        sharedContainer.innerHTML += createSharedCard(doc);
    });
}


// Owned document card
function createOwnedCard(doc) {
    const statusClass =
        doc.status === "Processed" ? "processed" : "pending";

    const downloadButton =
        doc.status === "Processed"
            ? `<button class="downloadBtn" onclick="downloadFile(${doc.id})">
                    Download
               </button>`
            : `<button disabled>Waiting</button>`;

    return `
        <div class="doc-card">
            <div>
                <h4>📄 ${doc.filename}</h4>
                <p class="${statusClass}">Status: ${doc.status}</p>

                <input
                    type="email"
                    id="share-${doc.id}"
                    placeholder="Enter email to share"
                    class="share-input"
                >

                <button onclick="shareDocument(${doc.id})">
                    Share
                </button>

                <button onclick="viewDocumentLogs(${doc.id})">
                    View History
                </button>
            </div>

            <div>
                ${downloadButton}
            </div>
        </div>
    `;
}


// Shared document card
function createSharedCard(doc) {
    const statusClass =
        doc.status === "Processed" ? "processed" : "pending";

    const downloadButton =
        doc.status === "Processed"
            ? `<button class="downloadBtn" onclick="downloadFile(${doc.id})">
                    Download
               </button>`
            : `<button disabled>Waiting</button>`;

    return `
        <div class="doc-card">
            <div>
                <h4>📄 ${doc.filename}</h4>
                <p class="${statusClass}">Status: ${doc.status}</p>
                <p>Shared with you</p>
            </div>

            <div>
                ${downloadButton}
            </div>
        </div>
    `;
}


// Share document
async function shareDocument(id) {
    const emailInput = document.getElementById("share-" + id);
    const email = emailInput.value;

    if (!email) {
        alert("Please enter an email");
        return;
    }

    const response = await fetch(
        VAULT + "/share/" + id +
        "?shared_with_email=" + encodeURIComponent(email),
        {
            method: "POST",
            headers: {
                "Authorization": "Bearer " + token
            }
        }
    );

    const data = await response.json();

    if (!response.ok) {
        alert(data.detail || "Could not share document");
        return;
    }

    alert("Document shared successfully");
    emailInput.value = "";
    loadDocuments();
}


// Download document
async function downloadFile(id) {
    const response = await fetch(VAULT + "/download/" + id, {
        headers: {
            "Authorization": "Bearer " + token
        }
    });

    const data = await response.json();

    if (!response.ok) {
        alert(data.detail || "Download failed");
        return;
    }

    window.open(data.download_url, "_blank");
    loadDocuments();
}


// View who downloaded/viewed this document
async function viewDocumentLogs(id) {
    const response = await fetch(VAULT + "/document-logs/" + id, {
        headers: {
            "Authorization": "Bearer " + token
        }
    });

    const logs = await response.json();

    if (!response.ok) {
        alert(logs.detail || "Could not fetch document history");
        return;
    }

    let message = "View / Download History:\n\n";

    if (logs.length === 0) {
        message += "No one has viewed/downloaded this document yet.";
    } else {
        logs.forEach(log => {
            message += `${log.user_email} viewed/downloaded on ${log.created_at}\n`;
        });
    }

    alert(message);
    loadDocuments();
}


// Initial load
loadDocuments();

// Auto refresh
//setInterval(loadDocuments, 5000);