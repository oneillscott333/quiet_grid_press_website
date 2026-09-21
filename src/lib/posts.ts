import { getCollection } from "astro:content";

/** Posts that are not drafts and whose publishDate has arrived (build-time check).
 *  Future-dated posts stay invisible until a rebuild after their date — the daily
 *  scheduled rebuild (.github/workflows/daily-rebuild.yml) reveals them. */
export async function getPublishedPosts() {
  const now = new Date();
  const posts = await getCollection(
    "blog",
    ({ data }) => !data.draft && data.publishDate.valueOf() <= now.valueOf(),
  );
  return posts.sort(
    (a, b) => b.data.publishDate.valueOf() - a.data.publishDate.valueOf(),
  );
}
