// Where each Amazon button of this website leads. A button opens /amazon/<key>/, a small page of this site
// that opens the book's Amazon page at once, so the button's use is counted with the site's other pages
// (the hosting provider counts pages it serves; it cannot see a click that leaves the site directly).
import series from "./bible_series.json";

const bookOne = series.find((b) => b.number === 1);

export const amazonButtons = [
  ...series.map((b) => {
    const opens = b.asin ? b : bookOne;
    return {
      key: b.slug ?? "bible-verse-sudoku",
      title: b.title,
      opensTitle: opens.title,
      url: `https://www.amazon.com/dp/${opens.asin}`,
      standIn: opens !== b,
    };
  }),
  // USA250 Sudoku (catalog entry 002_sudoku_usa250). The new book is an update of the live paperback and keeps its ASIN.
  { key: "usa250-sudoku", title: "USA250 Sudoku", opensTitle: "USA250 Sudoku", url: "https://www.amazon.com/dp/B0H7QJJYWZ", standIn: false },
];

export function amazonPath(key) {
  if (!amazonButtons.some((b) => b.key === key)) throw new Error(`no Amazon button for "${key}"`);
  return `/amazon/${key}/`;
}
