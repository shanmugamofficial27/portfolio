// Builds the public copy of the site into dist/: minified HTML, CSS and JS (no comments, mangled names),
// plus the images. Edit index.html as usual, then run:  node tools/build.mjs
// Publish dist/ only; keep this readable source private.
import { execSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

const root = path.dirname(path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1")));
const dist = path.join(root, "dist");
fs.rmSync(dist, { recursive: true, force: true });
fs.mkdirSync(dist);

execSync(
  `npx --yes html-minifier-terser@7 "${path.join(root, "index.html")}" -o "${path.join(dist, "index.html")}" ` +
    "--collapse-whitespace --remove-comments --minify-css true " +
    `--minify-js "{\\"mangle\\":true,\\"compress\\":true,\\"format\\":{\\"comments\\":false}}"`,
  { stdio: "inherit", cwd: root }
);

// move the inline CSS and JS into separate hashed files, so View source shows only a short HTML page
import crypto from "node:crypto";
{
  const f = path.join(dist, "index.html");
  let html = fs.readFileSync(f, "utf8");
  fs.mkdirSync(path.join(dist, "assets"));
  const save = (body, ext) => {
    const name = `${ext === "css" ? "style" : "app"}.${crypto.createHash("md5").update(body).digest("hex").slice(0, 8)}.${ext}`;
    fs.writeFileSync(path.join(dist, "assets", name), body);
    return "assets/" + name;
  };
  let css = "";
  html = html.replace(/<style>([\s\S]*?)<\/style>/g, (_, body) => { css += body; return "<!--css-->"; });
  html = html.replace("<!--css-->", `<link rel="stylesheet" href="${save(css, "css")}">`).replace(/<!--css-->/g, "");
  html = html.replace(/<script>([\s\S]*?)<\/script>/g, (_, body) => `<script src="${save(body, "js")}"></script>`);
  fs.writeFileSync(f, html);
}

// copy everything the page loads; nothing from tools/ or the git history goes out
for (const item of ["images", "resume.pdf", "LICENSE"]) {
  const from = path.join(root, item);
  if (fs.existsSync(from)) fs.cpSync(from, path.join(dist, item), { recursive: true });
}
fs.writeFileSync(path.join(dist, "robots.txt"), "User-agent: *\nAllow: /\n");

const kb = f => Math.round(fs.statSync(f).size / 1024);
console.log(`dist/index.html: ${kb(path.join(dist, "index.html"))} KB (source ${kb(path.join(root, "index.html"))} KB)`);
