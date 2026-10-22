import React from "react";
import { Composition } from "remotion";
import "./theme";
import { Slide, Deck } from "./Slide";
import AR from "./data/ar.json";
import EN from "./data/en.json";

// One composition per slide per language: AR-00 … AR-30, EN-00 … EN-30 (00 = title).
// 5 s per slide (build ≤ 3 s, hold ≥ 2 s, DECISIONS.md); figure slides get 6 s for the chart to finish.
// Figure ids are layout metadata, not approved words. The Arabic source maps S4 to F4 and S11 to F5,
// which contradicts both slides' own headings; the English mapping (S4 F3, S11 F8) is used for both.
const en = EN as Deck;
const ar: Deck = { ...(AR as Deck), slides: (AR as Deck).slides.map((s, i) => ({ ...s, figure: en.slides[i].figure })) };
const decks: [string, Deck, "ar" | "en"][] = [["AR", ar, "ar"], ["EN", en, "en"]];

export const RemotionRoot: React.FC = () => (
  <>
    {decks.flatMap(([code, deck, lang]) =>
      Array.from({ length: deck.slides.length + 1 }, (_, i) => {
        const fig = i > 0 && deck.slides[i - 1].figure;
        return (
          <Composition key={`${code}-${i}`} id={`${code}-${String(i).padStart(2, "0")}`} component={Slide}
            width={1920} height={1080} fps={30} durationInFrames={fig ? 180 : 150} defaultProps={{ deck, index: i, lang }} />
        );
      }),
    )}
  </>
);
