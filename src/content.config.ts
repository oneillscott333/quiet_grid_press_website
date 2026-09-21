import { defineCollection, z } from "astro:content";
import { glob } from "astro/loaders";

const blog = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/blog" }),
  schema: z.object({
    title: z.string(),
    description: z.string(),
    publishDate: z.coerce.date(),
    updatedDate: z.coerce.date().optional(),
    book: z
      .enum(["bible-verse-sudoku", "usa250-sudoku", "none"])
      .default("none"),
    module: z.string().optional(),
    draft: z.boolean().default(false),
  }),
});

export const collections = { blog };
