#!/usr/bin/env node
/**
 * Local preview for GitHub Pages static export (basePath /shared-agents).
 * Plain `serve out` 404s because assets live at out/_next/ but HTML requests
 * /shared-agents/_next/ — GitHub Pages rewrites that; this script does the same.
 */
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT_DIR = path.resolve(__dirname, "../out");
const BASE_PATH = (
  process.env.PREVIEW_BASE_PATH ||
  process.env.NEXT_PUBLIC_BASE_PATH ||
  "/shared-agents"
).replace(/\/$/, "");
const PORT = Number(process.env.PORT || 3000);

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".webp": "image/webp",
  ".woff2": "font/woff2",
  ".woff": "font/woff",
  ".txt": "text/plain; charset=utf-8",
  ".ico": "image/x-icon",
};

function resolveFile(urlPathname) {
  let rel = urlPathname;

  if (rel === BASE_PATH) {
    rel = "/";
  } else if (rel.startsWith(`${BASE_PATH}/`)) {
    rel = rel.slice(BASE_PATH.length) || "/";
  } else if (rel !== "/" && !rel.startsWith(`${BASE_PATH}/`)) {
    return null;
  }

  if (rel.endsWith("/")) {
    rel = `${rel}index.html`;
  } else if (!path.extname(rel)) {
    const withHtml = `${rel}.html`;
    const withIndex = path.join(rel, "index.html");
    const htmlPath = path.join(OUT_DIR, withHtml);
    const indexPath = path.join(OUT_DIR, withIndex);
    if (fs.existsSync(htmlPath) && fs.statSync(htmlPath).isFile()) {
      rel = withHtml;
    } else if (fs.existsSync(indexPath) && fs.statSync(indexPath).isFile()) {
      rel = withIndex;
    }
  }

  const filePath = path.normalize(path.join(OUT_DIR, rel));
  if (!filePath.startsWith(OUT_DIR)) return null;
  return filePath;
}

function send(res, status, headers, body) {
  res.writeHead(status, headers);
  if (body instanceof fs.ReadStream) {
    body.pipe(res);
  } else {
    res.end(body);
  }
}

const server = http.createServer((req, res) => {
  const url = new URL(req.url ?? "/", `http://127.0.0.1:${PORT}`);
  const pathname = url.pathname;

  if (pathname === "/" || pathname === "") {
    send(res, 302, { Location: `${BASE_PATH}/` }, "");
    return;
  }

  const filePath = resolveFile(pathname);
  if (!filePath) {
    send(res, 404, { "Content-Type": "text/plain" }, "Not found\n");
    return;
  }

  fs.stat(filePath, (err, stat) => {
    if (err || !stat.isFile()) {
      const notFound = path.join(OUT_DIR, "404.html");
      if (fs.existsSync(notFound)) {
        send(res, 404, { "Content-Type": "text/html; charset=utf-8" }, fs.createReadStream(notFound));
      } else {
        send(res, 404, { "Content-Type": "text/plain" }, "Not found\n");
      }
      return;
    }

    const ext = path.extname(filePath);
    send(res, 200, { "Content-Type": MIME[ext] ?? "application/octet-stream" }, fs.createReadStream(filePath));
  });
});

server.listen(PORT, () => {
  console.log(`GitHub Pages preview (basePath ${BASE_PATH})`);
  console.log(`  → http://localhost:${PORT}${BASE_PATH}/`);
  console.log(`  (Serving files from ${OUT_DIR})`);
});
