const http = require('http');
const fs = require('fs');
const path = require('path');
const os = require('os');
const puppeteer = require('./frontend/node_modules/puppeteer-core');

const DIST_DIR = path.join(__dirname, 'frontend', 'dist');
const SCREENSHOTS_DIR = path.join(__dirname, 'screenshots');
const ARTIFACT_DIR = path.join('C:', 'Users', 'Valarmathi', '.gemini', 'antigravity', 'brain', 'db86f052-29a7-4442-965e-7626e7ca5e25');
const EDGE_PATH = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';

if (!fs.existsSync(SCREENSHOTS_DIR)) {
  fs.mkdirSync(SCREENSHOTS_DIR, { recursive: true });
}

function startServer(port) {
  return new Promise((resolve) => {
    const server = http.createServer((req, res) => {
      let reqPath = req.url.split('?')[0].split('#')[0];
      if (reqPath === '/' || reqPath === '') reqPath = '/index.html';
      const filePath = path.join(DIST_DIR, reqPath);

      if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
        const ext = path.extname(filePath);
        const mimeTypes = {
          '.html': 'text/html',
          '.js': 'application/javascript',
          '.css': 'text/css',
          '.svg': 'image/svg+xml',
          '.png': 'image/png',
          '.json': 'application/json'
        };
        res.writeHead(200, { 'Content-Type': mimeTypes[ext] || 'application/octet-stream' });
        fs.createReadStream(filePath).pipe(res);
      } else {
        const indexHtml = path.join(DIST_DIR, 'index.html');
        res.writeHead(200, { 'Content-Type': 'text/html' });
        fs.createReadStream(indexHtml).pipe(res);
      }
    });

    server.listen(port, '127.0.0.1', () => {
      console.log(`Server listening at http://127.0.0.1:${port}`);
      resolve(server);
    });
  });
}

async function run() {
  const port = 4173;
  const server = await startServer(port);

  // Use a completely unique user data dir in os.tmpdir()
  const randomId = Math.random().toString(36).substring(2, 9);
  const tempUserDir = path.join(os.tmpdir(), `edge_headless_${randomId}`);
  fs.mkdirSync(tempUserDir, { recursive: true });

  console.log(`Launching Edge browser from ${EDGE_PATH} with profile ${tempUserDir}...`);
  const browser = await puppeteer.launch({
    executablePath: EDGE_PATH,
    headless: true,
    userDataDir: tempUserDir,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-gpu',
      '--disable-dev-shm-usage',
      '--disable-extensions',
      '--remote-debugging-port=0'
    ]
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1500, height: 960, deviceScaleFactor: 2 });

  const tasks = [
    {
      name: '1_application_tracking_dashboard.png',
      url: `http://127.0.0.1:${port}/#tracking`
    },
    {
      name: '2_institution_records_registry.png',
      url: `http://127.0.0.1:${port}/#records`
    },
    {
      name: '3_predictive_sla_control_room.png',
      url: `http://127.0.0.1:${port}/#sla-alerts`
    }
  ];

  for (const t of tasks) {
    console.log(`Capturing ${t.name} from ${t.url}...`);
    await page.goto(t.url, { waitUntil: 'networkidle0' });
    await new Promise((r) => setTimeout(r, 600));

    const outPath = path.join(SCREENSHOTS_DIR, t.name);
    await page.screenshot({ path: outPath, fullPage: false });
    console.log(`Saved screenshot: ${outPath} (${fs.statSync(outPath).size} bytes)`);

    // Copy to artifact dir
    if (fs.existsSync(ARTIFACT_DIR)) {
      const artPath = path.join(ARTIFACT_DIR, t.name);
      fs.copyFileSync(outPath, artPath);
      console.log(`Copied to artifact dir: ${artPath}`);
    }
  }

  await browser.close();
  try {
    fs.rmSync(tempUserDir, { recursive: true, force: true });
  } catch (e) {}

  server.close();
  console.log('All 3 screenshots successfully generated!');
}

run().catch((err) => {
  console.error('Capture error:', err);
  process.exit(1);
});
