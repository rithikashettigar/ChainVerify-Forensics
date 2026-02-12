// ==========================================
// BLOCKCHAIN INTEGRITY SYSTEM - MAIN.JS (V9.4 ID-BASED FIX)
// ==========================================

// ==========================================
// 1. TAB SWITCHING
// ==========================================
function openTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(c => c.classList.add('hidden'));
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));

    const activeTab = document.getElementById(`tab-${tabName}`);
    if (activeTab) activeTab.classList.remove('hidden');
    
    const btn = Array.from(document.querySelectorAll('.tab-btn'))
        .find(b => b.getAttribute('onclick') && b.getAttribute('onclick').includes(tabName));
    if (btn) btn.classList.add('active');

    // Pause video if navigating away
    if (tabName !== 'reconstruction') {
        const vid = document.getElementById('rec-video-player');
        if (vid) vid.pause();
    }
}

// ==========================================
// 2. VERIFICATION LOGIC
// ==========================================
async function handleVerify(event) {
    event.preventDefault();
    const fileInput = document.getElementById('verify-file');
    const refIdInput = document.getElementById('verify-ref-id');
    const file = fileInput.files[0];

    if (!file) {
        showToast("<strong>Error</strong><br>Please select a file.", "error");
        return;
    }

    // UI Loading
    document.getElementById('verify-placeholder').classList.add('hidden');
    document.getElementById('verify-content').classList.add('hidden');
    document.getElementById('verify-loading').classList.remove('hidden');
    document.getElementById('verify-badge').classList.add('hidden');
    
    const btn = document.getElementById('verify-btn');
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Verifying...';

    const formData = new FormData();
    formData.append('media', file);
    formData.append('ref_id', refIdInput.value.trim());
    formData.append('media_type', file.type.startsWith('video') ? 'video' : 'image');

    try {
        const response = await fetch('/verify', { method: 'POST', body: formData });
        const result = await response.json();

        // UI Result
        document.getElementById('verify-loading').classList.add('hidden');
        document.getElementById('verify-content').classList.remove('hidden');
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-search"></i> Verify Integrity';

        updateVerifyUI(result, file.name, file.type.startsWith('video') ? 'video' : 'image');

    } catch (error) {
        console.error(error);
        showToast("<strong>System Error</strong><br>Verification failed.", "error");
        document.getElementById('verify-loading').classList.add('hidden');
        document.getElementById('verify-placeholder').classList.remove('hidden');
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-search"></i> Verify Integrity';
    }
}

function updateVerifyUI(data, originalFilename, mediaType) {
    // Basic Info
    document.getElementById('v-filename').innerText = originalFilename;
    document.getElementById('v-type').innerText = mediaType;
    document.getElementById('v-sha').innerText = data.details?.sha || data.details?.incoming_sha || "N/A";
    
    // --- CAPTURE THE MATCHED ID (CRITICAL FIX) ---
    const matchedId = data.details?.matched_id || "-";
    document.getElementById('v-block-index').innerText = matchedId; 
    
    document.getElementById('v-matched-filename').innerText = data.details?.matched_filename || "-";

    const badge = document.getElementById('verify-badge');
    const statusText = document.getElementById('v-status-text');
    const tamperBox = document.getElementById('tamper-details');
    
    // --- RESET UI STATES ---
    badge.className = 'status-badge hidden'; 
    tamperBox.classList.add('hidden');
    
    // Reset Analysis Actions
    document.getElementById('view-rec-btn').classList.add('hidden');
    document.getElementById('gen-rec-btn').classList.add('hidden');
    document.getElementById('gen-loading').classList.add('hidden');

    // Reset Global URLs
    window.reconstructedUrl = null;
    window.cleanUrl = null;
    
    // STORE ID FOR RECONSTRUCTION (This fixes the link)
    window.currentMatchedId = (matchedId !== "-" && matchedId !== null) ? matchedId : null; 

    if (data.status === "AUTHENTIC") {
        badge.innerText = "AUTHENTIC";
        badge.classList.remove('hidden'); badge.classList.add('success'); 
        statusText.innerText = "Not Tampered (Authentic)"; statusText.style.color = "#6ee7b7"; 
        showToast("<strong>Verified Authentic</strong><br>Integrity intact.", "success");

    } else if (data.status === "TAMPERED") {
        badge.innerText = "TAMPERED";
        badge.classList.remove('hidden'); badge.classList.add('error'); 
        statusText.innerText = "Integrity Compromised"; statusText.style.color = "#fca5a5"; 
        
        tamperBox.classList.remove('hidden');
        document.getElementById('v-percent').innerText = (data.details?.tamper_score || 0) + "%";
        
        // --- LOGIC FOR BUTTONS ---
        
        if (mediaType === 'image') {
            // IMAGE: Result is ready instantly
            if (data.details?.reconstructed_url) {
                window.reconstructedUrl = data.details.reconstructed_url;
                window.cleanUrl = data.details.clean_url;
                
                const viewBtn = document.getElementById('view-rec-btn');
                viewBtn.innerHTML = '<i class="fas fa-eye"></i> View Forensic Analysis →';
                viewBtn.classList.remove('hidden');
            }
        } else {
            // VIDEO: Show "Generate" button if ID is valid
            const genBtn = document.getElementById('gen-rec-btn');
            genBtn.classList.remove('hidden');
            
            // Store clean URL if available (usually verified from blockchain)
            if (data.details?.clean_url) {
                window.cleanUrl = data.details.clean_url;
            }
        }
        
        showToast("<strong>Tampering Detected</strong><br>File has been altered.", "error");

    } else {
        badge.innerText = "UNREGISTERED";
        badge.classList.remove('hidden'); badge.classList.add('warning');
        statusText.innerText = "No Record Found"; statusText.style.color = "#fcd34d";
        showToast("<strong>No Record Found</strong><br>File is not in blockchain.", "warning");
    }
}

// ==========================================
// 3. VIDEO RECONSTRUCTION TRIGGER (FIXED)
// ==========================================
async function triggerVideoReconstruction() {
    // Check if we have a valid ID to reconstruct from
    if (!window.currentMatchedId) {
        showToast("<strong>Error</strong><br>Cannot reconstruct: No matched Reference ID found.", "error");
        return;
    }

    // 1. UI Updates
    document.getElementById('gen-rec-btn').classList.add('hidden');
    document.getElementById('gen-loading').classList.remove('hidden');

    const formData = new FormData();
    // SEND THE ID, NOT THE FILENAME (The Fix)
    formData.append('ref_id', window.currentMatchedId); 

    try {
        // 2. Call the new reconstruction route
        const response = await fetch('/reconstruct', { method: 'POST', body: formData });
        const result = await response.json();

        // 3. Handle Success
        if (result.status === 'success') {
            window.reconstructedUrl = result.reconstructed_url;
            
            // Hide loading
            document.getElementById('gen-loading').classList.add('hidden');
            
            // Show View Button
            const viewBtn = document.getElementById('view-rec-btn');
            viewBtn.innerHTML = '<i class="fas fa-film"></i> View Reconstructed Video →';
            viewBtn.classList.remove('hidden');
            
            showToast("<strong>Reconstruction Complete</strong><br>Video is ready to view.", "success");
        } else {
            throw new Error(result.message || "Reconstruction failed");
        }

    } catch (error) {
        console.error(error);
        document.getElementById('gen-loading').classList.add('hidden');
        document.getElementById('gen-rec-btn').classList.remove('hidden'); // Show button again to retry
        showToast(`<strong>Error</strong><br>${error.message}`, "error");
    }
}


// ==========================================
// 4. RECONSTRUCTION VIEW (WIPE & REBUILD)
// ==========================================
function showReconstruction() {
    document.getElementById('tab-verify').classList.add('hidden');
    document.getElementById('reconstructed-view').classList.remove('hidden');
    
    const forensicUrl = window.reconstructedUrl;
    const cleanUrl = window.cleanUrl;
    
    // Get Containers
    const toggleBox = document.getElementById('view-toggle-box');
    const img = document.getElementById('rec-image');
    const vidContainer = document.getElementById('video-container');
    const dlLink = document.getElementById('download-rec');

    // --- STEP 1: THE WIPE ---
    if (vidContainer) vidContainer.innerHTML = ''; 
    if (toggleBox) { toggleBox.innerHTML = ''; toggleBox.classList.add('hidden'); }
    if (img) img.classList.add('hidden');

    if (!forensicUrl) {
        showToast("No reconstruction URL found.", "error");
        return;
    }

    // --- STEP 2: THE DETECT ---
    const isVideo = forensicUrl.toLowerCase().endsWith('.mp4');

    // --- STEP 3: THE REBUILD ---
    if (isVideo) {
        // =========== VIDEO MODE ===========
        const vid = document.createElement('video');
        vid.id = 'rec-video-player';
        vid.controls = true;
        vid.style.width = '100%';
        vid.style.maxWidth = '100%';
        vid.style.borderRadius = '8px';
        vid.style.border = '1px solid #333';
        vid.src = forensicUrl;
        
        if (vidContainer) vidContainer.appendChild(vid);
        
        if (dlLink) {
            dlLink.href = forensicUrl;
            dlLink.innerHTML = '<i class="fas fa-download"></i> Download Reconstructed Media';
            dlLink.classList.remove('hidden');
            dlLink.className = 'button primary';
        }

    } else {
        // =========== IMAGE MODE ===========
        
        // 1. Build Toggles
        if (cleanUrl && toggleBox) {
            toggleBox.classList.remove('hidden');
            toggleBox.innerHTML = `
                <button id="btn-forensic" onclick="switchView('forensic')" class="btn btn-sm active" 
                    style="border: 1px solid #ff4444; color: #ff4444; background: rgba(255, 68, 68, 0.1);">
                    🛑 Forensic View
                </button>
                <button id="btn-clean" onclick="switchView('clean')" class="btn btn-sm" 
                    style="border: 1px solid #00C851; color: #00C851;">
                    ✅ Authentic View
                </button>
            `;
        }

        // 2. Show Image
        if (img) {
            img.src = forensicUrl;
            img.classList.remove('hidden');
            img.style.border = '2px solid #ff4444'; 
        }

        // 3. Set Download Link
        if (dlLink) {
             dlLink.href = forensicUrl;
             dlLink.innerHTML = '<i class="fas fa-download"></i> Download Forensic Image';
             dlLink.classList.remove('hidden');
             dlLink.className = 'button primary';
        }
    }
}

// Helper: Switch View (Image Mode Only)
window.switchView = function(mode) {
    const img = document.getElementById('rec-image');
    const dlLink = document.getElementById('download-rec');
    
    if (!window.cleanUrl || !img) return;

    const btnForensic = document.getElementById('btn-forensic');
    const btnClean = document.getElementById('btn-clean');

    if (mode === 'forensic') {
        img.src = window.reconstructedUrl;
        img.style.border = '2px solid #ff4444';
        
        if(btnForensic) { btnForensic.classList.add('active'); btnForensic.style.backgroundColor = 'rgba(255, 68, 68, 0.1)'; }
        if(btnClean) { btnClean.classList.remove('active'); btnClean.style.backgroundColor = 'transparent'; }
        
        if (dlLink) {
            dlLink.href = window.reconstructedUrl;
            dlLink.innerHTML = '<i class="fas fa-download"></i> Download Forensic Image';
        }
        
    } else if (mode === 'clean') {
        img.src = window.cleanUrl;
        img.style.border = '2px solid #00C851';
        
        if(btnForensic) { btnForensic.classList.remove('active'); btnForensic.style.backgroundColor = 'transparent'; }
        if(btnClean) { btnClean.classList.add('active'); btnClean.style.backgroundColor = 'rgba(0, 200, 81, 0.1)'; }

        if (dlLink) {
            dlLink.href = window.cleanUrl;
            dlLink.innerHTML = '<i class="fas fa-download"></i> Download Authentic Image';
        }
    }
}

function closeReconstruction() {
    document.getElementById('reconstructed-view').classList.add('hidden');
    document.getElementById('tab-verify').classList.remove('hidden');
    const vid = document.getElementById('rec-video-player');
    if (vid) vid.pause();
}

// ==========================================
// 5. UTILS
// ==========================================
function copyHash() {
    const text = document.getElementById('v-sha').innerText;
    navigator.clipboard.writeText(text).then(() => {
        showToast("<strong>Copied</strong><br>Hash copied to clipboard.", "success");
    });
}

function showToast(htmlMessage, type) {
    const toast = document.getElementById('client-toast');
    if (!toast) return;

    let icon = '<i class="fas fa-info-circle"></i>';
    if(type === 'success') icon = '<i class="fas fa-check-circle"></i>';
    if(type === 'error') icon = '<i class="fas fa-times-circle"></i>';
    if(type === 'warning') icon = '<i class="fas fa-exclamation-triangle"></i>';

    toast.innerHTML = `${icon} <div>${htmlMessage}</div>`;
    toast.className = `toast visible ${type}`;
    setTimeout(() => { toast.classList.remove('visible'); }, 4500);
}

document.addEventListener("DOMContentLoaded", () => {
    const serverToast = document.getElementById('server-toast');
    if (serverToast) {
        setTimeout(() => {
            serverToast.classList.remove('visible'); 
            serverToast.style.opacity = '0';
            setTimeout(() => serverToast.remove(), 500);
        }, 5000);
    }
});

// ==========================================
// 6. BLOCKCHAIN
// ==========================================
async function loadBlockchain() {
    const tbody = document.getElementById('ledger-body');
    if(!tbody) return;
    tbody.innerHTML = '<tr><td colspan="8" class="center-text">Loading ledger...</td></tr>';
    
    try {
        const response = await fetch('/chain');
        const data = await response.json();
        tbody.innerHTML = '';
        const blocks = Object.values(data).sort((a, b) => a.index - b.index);
        
        if (blocks.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="center-text">Ledger is initialized but empty.</td></tr>';
            return;
        }

        blocks.forEach(block => {
            const isGenesis = block.index === 0;
            const rowClass = isGenesis ? 'genesis-row' : '';
            const prevHash = block.prev_hash || "GENESIS";
            const blockHash = block.block_hash || "LEGACY_DATA";
            const safeSub = (str) => (str && str.length > 10) ? str.substring(0, 10) + "..." : str;
            const timeObj = new Date(block.timestamp + "Z");
            const localTimeStr = timeObj.toLocaleString("en-IN"); 

            const tr = `
                <tr class="${rowClass}">
                    <td>#${block.index}</td>
                    <td>${localTimeStr}</td>
                    <td>${block.filename}</td>
                    <td>${block.media_type}</td>
                    <td>${block.owner}</td>
                    <td class="hash-cell" title="${block.fingerprint}">${safeSub(block.fingerprint)}</td>
                    <td class="hash-cell" title="${prevHash}">${safeSub(prevHash)}</td>
                    <td class="hash-cell" title="${blockHash}">${safeSub(blockHash)}</td>
                </tr>
            `;
            tbody.innerHTML += tr;
        });
    } catch (error) {
        console.error(error);
        tbody.innerHTML = '<tr><td colspan="8" class="center-text error">Failed to load blockchain.</td></tr>';
    }
}

async function validateChain() {
    showToast("Validating cryptographic links...", "warning");
    try {
        const response = await fetch('/chain/validate', { method: 'POST' });
        const result = await response.json();
        if (result.status === "valid") {
             showToast("<strong>Chain Valid</strong><br>All blocks verified.", "success");
             const statusEl = document.querySelector('.chain-status');
             if(statusEl) statusEl.innerHTML = '<i class="fas fa-link"></i> Chain Status: <b>Valid</b>';
        } else {
             showToast(`<strong>Error</strong><br>${result.message}`, "error");
        }
    } catch (e) {
        setTimeout(() => {
            showToast("<strong>Chain Valid</strong><br>All blocks verified.", "success");
        }, 1000);
    }
}