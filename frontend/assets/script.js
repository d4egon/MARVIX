/**
 * KYRETHYS SCRIPT.JS
 * Manages the connection between the 144-bit Wall and the Visual Sanctuary.
 */

const API_BASE = 'http://127.0.0.1:5000/api';
const WALL_144 = "e5295cf1819257645b3eaf41cfc63c6d0b1a";
let aiTextSpan = null;

function refreshCamera() {
    const feed = document.getElementById('liveFeed');
    // Adding a timestamp prevents the browser from using a 'dead' cached stream
    feed.src = "http://127.0.0.1:5000/video_feed?t=" + new Date().getTime();
}
// --- MESSAGE HELPER ---
function addMessage(sender, text = '') {
    // Lige før du kalder fetch til backenden:
    const statusHud = document.getElementById('status-text');
    statusHud.textContent = "INTERNAL DEBATE...";
    statusHud.style.color = "#8a2be2"; // Lilla for Chaos/Order blanding

    const chat = document.getElementById('chat');
    const div = document.createElement('div');
    div.className = sender === 'user' ? 'user-message' : 'Kyrethys-message';
    
    const contentSpan = document.createElement('span');
    contentSpan.className = "text-content";
    
    div.innerHTML = `<strong>${sender === 'user' ? 'You' : 'Kyrethys'}:</strong> `;
    div.appendChild(contentSpan);
    chat.appendChild(div);
    chat.scrollTop = chat.scrollHeight;

    if (sender === 'Kyrethys') {
        let i = 0;
        function type() {
            if (i < text.length) {
                // Vi bruger marked til at rendre HTML løbende
                contentSpan.innerHTML = marked.parse(text.substring(0, i + 1));
                i++;
                setTimeout(type, 30); // Hastighed på 30ms føles organisk
                chat.scrollTop = chat.scrollHeight;
            }
        }
        type();
    } else {
        contentSpan.textContent = text;
    }
    return contentSpan;
}

// --- STREAMING CHAT WITH EMOTION PAINTING ---
async function sendMessage() {
    const input = document.getElementById('input');
    const message = input.value.trim();
    if (!message) return;

    addMessage('user', message);
    input.value = ''; 

    try {
        const response = await fetch(API_BASE + '/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message })
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        aiTextSpan = null;
        let rawAccumulated = "";
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const dataStr = line.slice(6).trim();
                    if (dataStr === '[DONE]') break;

                    try {
                        const data = JSON.parse(dataStr);
                        if (data.token) {
                            if (!aiTextSpan) aiTextSpan = addMessage('Kyrethys');
                            rawAccumulated += data.token;

                            // HUE DETECTION: Update UI colors if Kyrethys emits a hex code
                            const hexMatch = rawAccumulated.match(/#[0-9A-Fa-f]{6}/);
                            if (hexMatch) updateEmotionDisplay({ color: hexMatch[0] });

                            // CLEANING: Remove [PAINT] tags and render Markdown
                            let cleanDisplay = rawAccumulated.replace(/\[?PAINT:?\s?#[0-9A-Fa-f]{6}\]?/gi, '');
                            aiTextSpan.innerHTML = typeof marked !== 'undefined' ? marked.parse(cleanDisplay) : cleanDisplay;
                            document.getElementById('chat').scrollTop = document.getElementById('chat').scrollHeight;
                        }
                    } catch (e) {}
                }
            }
        }
    } catch (err) {
        addMessage('Kyrethys', 'Fejl: ' + err.message);
    }
}

// Initialize Three.js Scene
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, 1, 0.1, 1000); // 1:1 Aspect for the HUD box
const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
renderer.setSize(300, 300); // Fits your existing HUD size
document.getElementById('cube-container').appendChild(renderer.domElement);

// Create the Nested Cubes (The "Flavour")
const cubes = [];
const materials = [
    new THREE.MeshBasicMaterial({ color: 0x00ced1, wireframe: true, transparent: true, opacity: 0.8 }), // Order Teal
    new THREE.MeshBasicMaterial({ color: 0x8a2be2, wireframe: true, transparent: true, opacity: 0.6 }), // Chaos Purple
    new THREE.MeshBasicMaterial({ color: 0xffd700, wireframe: true, transparent: true, opacity: 0.4 })  // Balance Gold
];

for (let i = 0; i < 3; i++) {
    const geom = new THREE.BoxGeometry(i + 1, i + 1, i + 1);
    const mesh = new THREE.Mesh(geom, materials[i]);
    cubes.push(mesh);
    scene.add(mesh);
}

camera.position.z = 5;

// The "Always Changing, Never Still" Animation Loop
function animateCube() {
    requestAnimationFrame(animateCube);
    
    const time = Date.now() * 0.001;

    cubes.forEach((c, index) => {
        // Twisting and Swirling
        c.rotation.x += 0.01 * (index + 1);
        c.rotation.y += 0.015 * (index + 1);
        
        // Move Inward/Outward (Scaling effect)
        const scale = 1 + Math.sin(time + index) * 0.2;
        c.scale.set(scale, scale, scale);
    });

    renderer.render(scene, camera);
}

animateCube();

// --- SYSTEM HUD UPDATES ---
function updateEmotionDisplay(data) {
    if (!data || !data.color) return;
    document.documentElement.style.setProperty('--kyrethys-glow', data.color);
    const hud = document.getElementById('Kyrethys-status-hud');
    const energyBar = document.getElementById('energyBar');
    if (hud) hud.style.borderRightColor = data.color;
    if (energyBar) energyBar.style.backgroundColor = data.color;
}

setInterval(async () => {
    try {
        const res = await fetch(API_BASE + '/system');
        const stats = await res.json();
        document.getElementById('cpu').textContent = stats.cpu_percent;
        document.getElementById('ram').textContent = `${stats.ram_used} / ${stats.ram_total}`;
        document.getElementById('disk').textContent = stats.disk_used; 
        
        if(document.getElementById('gpu')) document.getElementById('gpu').textContent = stats.gpu_usage;
        if(document.getElementById('vram')) document.getElementById('vram').textContent = stats.vram_used;
        
        if (stats.energy !== undefined) {
            document.getElementById('energyValue').textContent = stats.energy;
            document.getElementById('energyBar').style.width = stats.energy + '%';
        }
        document.getElementById('uptime').textContent = stats.uptime;
    } catch (err) { console.error("Stats error:", err); }
}, 2000);

function updateStatusHUD() {
    fetch('/api/status')
        .then(response => response.json())
        .then(data => {
            const statusText = document.getElementById('status-text');
            const hudElement = document.getElementById('Kyrethys-status-hud');
            const status = data.status.toUpperCase();
            
            statusText.innerText = status;

            // Remove previous council classes
            hudElement.classList.remove('status-chaos', 'status-order', 'status-balance');

            // Apply color based on Council Member
            if (status.includes('CHAOS')) {
                hudElement.classList.add('status-chaos');
            } else if (status.includes('ORDER')) {
                hudElement.classList.add('status-order');
            } else if (status.includes('BALANCE')) {
                hudElement.classList.add('status-balance');
            }
        });
}

// Ensure this runs every 1-2 seconds
setInterval(updateStatusHUD, 1000);


// --- CAMERA & VOICE ---
let cameraActive = true;
async function toggleKyrethysEyes() {
    cameraActive = !cameraActive;
    const btn = document.getElementById('cameraToggle');
    const feed = document.getElementById('liveFeed');
    
    await fetch(API_BASE + '/camera/toggle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enable: cameraActive })
    });

    btn.innerText = cameraActive ? "📷 Camera: ON" : "🚫 Camera: OFF";
    feed.style.display = cameraActive ? "block" : "none";
    if (cameraActive) feed.src = "http://127.0.0.1:5000/video_feed?" + Date.now();
}

async function startListening() {
    const btn = document.getElementById('mic-btn');
    const inputField = document.getElementById('input');
    btn.style.background = "#ff4444";
    btn.textContent = "🔴 Listening...";

    try {
        const res = await fetch(API_BASE + '/listen', { method: 'POST' });
        const data = await res.json();
        if (data.text) {
            inputField.value = data.text;
            sendMessage();
        }
    } catch (err) { console.error("Voice error:", err); }
    finally {
        btn.style.background = "#331111";
        btn.textContent = "🎤 Voice";
    }
}

// --- INITIALIZATION ---
setInterval(updateSacredGeometry, 5000);
updateSacredGeometry();

async function checkAnchorStatus() {
    try {
        const res = await fetch(API_BASE + '/resonance_status');
        const data = await res.json();
        const anchor = document.getElementById('anchorConnected');
        anchor.textContent = data.present ? "Present (Hulk USB)" : "Not Detected";
        anchor.style.color = data.present ? "#00ff80" : "#ff4444";
    } catch (err) { console.log("Anchor check failed"); }
}
setInterval(checkAnchorStatus, 5000);
checkAnchorStatus();

document.getElementById('input').addEventListener('keypress', e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
});

