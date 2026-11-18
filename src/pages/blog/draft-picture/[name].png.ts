// Local preview only: shows the picture of a blog post Scott has not approved yet, read
// straight from the campaign folder. The public build makes nothing here (no paths), so an
// unapproved picture never reaches the public site. Approved pictures are copied to
// public/images/blog/ by build_blog.py.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import blog from "../../../data/blog_posts.json";

export function getStaticPaths() {
  if (!import.meta.env.DEV) return [];
  return blog.posts
    .filter((p) => p.hero && p.status !== "approved")
    .map((p) => ({ params: { name: p.hero.replace(/\.png$/, "") } }));
}

export function GET({ params }) {
  if (!import.meta.env.DEV) return new Response("Not found", { status: 404 });
  const name = `${params.name}.png`;
  const m = /^market_(c\d+)_blog_\d+_hero\.png$/.exec(name);
  if (!m) return new Response("Not found", { status: 404 });
  // this file: <website>/src/pages/blog/draft-picture/ ; the campaigns: <website>/../../06_market/00_imprint
  const here = path.dirname(fileURLToPath(import.meta.url));
  const market = path.resolve(here, "../../../../../../06_market/00_imprint");
  if (!fs.existsSync(market)) return new Response("Not found", { status: 404 });
  for (const folder of fs.readdirSync(market)) {
    if (!folder.startsWith(`${m[1]}_`)) continue;
    const file = path.join(market, folder, "assets", "blog", name);
    if (fs.existsSync(file)) {
      return new Response(fs.readFileSync(file), {
        headers: { "Content-Type": "image/png", "Cache-Control": "no-store" },
      });
    }
  }
  return new Response("Not found", { status: 404 });
}
