// frontend/main.js
const { app, BrowserWindow, Tray, Menu } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let pythonProcess;
let tray;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        frame: true,
        transparent: false,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false
        }
    });

    mainWindow.loadFile('index.html');

    // Hide instead of close
    mainWindow.on('close', (event) => {
        if (!app.isQuitting) {
            event.preventDefault();
            mainWindow.hide();
        }
    });
}

function createTray() {
    tray = new Tray(path.join(__dirname, 'assets/icon.png')); // Add an icon file

    const contextMenu = Menu.buildFromTemplate([
        { label: 'Show Marvix', click: () => mainWindow.show() },
        { label: 'Hide', click: () => mainWindow.hide() },
        { type: 'separator' },
        { label: 'Quit', click: () => {
            app.isQuitting = true;
            app.quit();
        }}
    ]);

    tray.setToolTip('Marvix');
    tray.setContextMenu(contextMenu);

    tray.on('click', () => {
        mainWindow.isVisible() ? mainWindow.hide() : mainWindow.show();
    });
}

function startPythonBackend() {
    // Option 1: Absolute path (most reliable)
    pythonProcess = spawn('python', ['C:/MARVIX/backend/jarvis_backend.py']);
    
    // Option 2: Relative from frontend folder
    // pythonProcess = spawn('python', ['../backend/jarvis_backend.py']);

    pythonProcess.stdout.on('data', (data) => {
        console.log(`Python: ${data}`);
    });

    pythonProcess.stderr.on('data', (data) => {
        console.error(`Python Error: ${data}`);
    });
}

// Auto-startup on boot
app.setLoginItemSettings({
    openAtLogin: true,
    openAsHidden: false
});

app.whenReady().then(async () => {
    try {
        startPythonBackend();
        createTray();
        setTimeout(createWindow, 2000);
    } catch (error) {
        console.error('Setup failed:', error);
        createWindow();
    }
});

app.on('window-all-closed', () => {
    if (pythonProcess) pythonProcess.kill();
    app.quit();
});

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
    }
});