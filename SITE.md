# Site: Quiet Grid Press (public website)

Local copy of the public site (Astro). Edited here, pushed to GitHub, pulled by the hosting system (Netlify; a daily rebuild reveals future-dated posts).
Path: `/Users/scoton/01_ai_workzone/qgp_books/tools/qgp_website` (the earlier Local Site Manager registration `quiet-grid-press`, port 48113, pointed at the old workspace path; re-register if you use it).
Before first run: `npm install`.

The site is the reference implementation of the brand: palette and fonts in `src/styles/global.css` match `qgp_brand/color_standard.md` and `typography_standard.md`; the logo in the header (Evergreen on Cream) and footer (inverted on Evergreen Deep) matches `color_standard.md` §3. When building anything new for another channel, check this site's components first.

Content: blog posts in `src/content/blog/` (The Quiet Grid issues and reveal notes, future-dated); book pages in `src/pages/books/`; the contact page states the business location, which should be confirmed with the founder.
