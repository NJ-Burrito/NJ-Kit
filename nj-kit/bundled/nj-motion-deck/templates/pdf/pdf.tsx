// The PDF twin: the same Slide components, rendered at their final frame as live DOM
// (FrameOverride at the last frame, no player), one 1920×1080 page each, printed by Chrome — so the PDF keeps
// real, selectable Thmanyah text instead of pictures of text.
import React from "react";
import { createRoot } from "react-dom/client";
import { Slide, Deck } from "../src/Slide";
import { FrameOverride } from "../src/theme";
import AR from "../src/data/ar.json";
import EN from "../src/data/en.json";

const en = EN as Deck;
const ar: Deck = { ...(AR as Deck), slides: (AR as Deck).slides.map((s, i) => ({ ...s, figure: en.slides[i].figure })) };
const lang = (new URLSearchParams(location.search).get("lang") ?? "ar") as "ar" | "en";
const deck = lang === "ar" ? ar : en;

const App: React.FC = () => (
  <>
    {Array.from({ length: deck.slides.length + 1 }, (_, i) => {
      const dur = i > 0 && deck.slides[i - 1].figure ? 180 : 150;
      return (
        <div key={i} className="page">
          <FrameOverride.Provider value={dur - 1}>
            <div style={{ position: "relative", width: 1920, height: 1080 }}><Slide deck={deck} index={i} lang={lang} /></div>
          </FrameOverride.Provider>
        </div>
      );
    })}
  </>
);

document.fonts.ready.then(() => {
  createRoot(document.getElementById("root")!).render(<App />);
  setTimeout(() => document.body.setAttribute("data-ready", "1"), 4000);
});
