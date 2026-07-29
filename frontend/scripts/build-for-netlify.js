const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..", "..");
const SRC_STATIC = path.join(ROOT, "static");
const SRC_TEMPLATES = path.join(ROOT, "templates");
const DIST = path.join(ROOT, "dist", "frontend");

function copyRecursive(src, dest) {
    const stats = fs.statSync(src);
    if (stats.isDirectory()) {
        if (!fs.existsSync(dest)) fs.mkdirSync(dest, { recursive: true });
        for (const entry of fs.readdirSync(src)) {
            copyRecursive(path.join(src, entry), path.join(dest, entry));
        }
    } else {
        fs.copyFileSync(src, dest);
    }
}

function build() {
    if (fs.existsSync(DIST)) fs.rmSync(DIST, { recursive: true });
    fs.mkdirSync(DIST, { recursive: true });

    if (fs.existsSync(SRC_STATIC)) {
        copyRecursive(SRC_STATIC, path.join(DIST, "static"));
    }

    let html = fs.readFileSync(path.join(SRC_TEMPLATES, "index.html"), "utf-8");

    html = html.replace(
        /\{\{\s*url_for\('static',\s*filename='([^']+)'\)\s*\}\}/g,
        (match, filename) => `/static/${filename}`
    );

    html = html.replace(
        '<script src="/static/app.js"></script>',
        '<script src="/static/env-config.js"></script>\n    <script src="/static/app.js"></script>'
    );

    fs.writeFileSync(path.join(DIST, "index.html"), html);

    const apiBase = process.env.API_BASE || "";
    const envConfig = `window.__API_BASE__ = "${apiBase}";\n`;
    fs.writeFileSync(path.join(DIST, "static", "env-config.js"), envConfig);

    console.log("Frontend built successfully in dist/frontend/");
    console.log("API_BASE:", apiBase || "(empty)");
}

build();
