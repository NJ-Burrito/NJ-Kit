import React from "react";
import { continueRender, delayRender, staticFile, interpolate, Easing, useCurrentFrame, Img } from "remotion";

// Ensera tokens (brand/tokens.json). Contrast measured 2026-09-25 with the WCAG formula:
// paper/navy 15.76 · lime/navy 13.49 · teal/navy 5.07 · mute/paper 5.95 · teal/paper 3.11 (large bold only)
// Data colours (blue, green, amber, coral) are drawn on navy2 only: coral/paper is 2.59, refused.
export const C = {
  navy: "#0B1F2A", navy2: "#123240", lime: "#D6F26B", teal: "#0F9D9A",
  blue: "#2D9BE6", green: "#3FD08A", amber: "#F5C451", coral: "#FF6B6B",
  paper: "#F3F8F9", ink: "#0B1F2A", mute: "#4D6270", white: "#FFFFFF",
};

// Thmanyah Serif only (DECISIONS.md, post-build 2026-09-24). Arial is the accepted fallback for "≤" only.
export const DISPLAY = "'Thmanyah Serif Display', Arial, serif";
export const TEXT = "'Thmanyah Serif Text', Arial, serif";

export const FPS = 30;

const faces: [string, string, string][] = [
  ["Thmanyah Serif Display", "thmanyahserifdisplay-Medium.otf", "500"],
  ["Thmanyah Serif Display", "thmanyahserifdisplay-Bold.otf", "700"],
  ["Thmanyah Serif Display", "thmanyahserifdisplay-Black.otf", "900"],
  ["Thmanyah Serif Text", "thmanyahseriftext-Regular.otf", "400"],
  ["Thmanyah Serif Text", "thmanyahseriftext-Medium.otf", "500"],
  ["Thmanyah Serif Text", "thmanyahseriftext-Bold.otf", "700"],
];
if (typeof document !== "undefined") {
  const h = delayRender("thmanyah");
  Promise.all(faces.map(([fam, file, w]) =>
    new FontFace(fam, `url(${staticFile("fonts/" + file)})`, { weight: w }).load().then((f) => document.fonts.add(f)),
  )).then(() => continueRender(h));
}

const OUT = Easing.bezier(0.16, 1, 0.3, 1);
/** 0→1 between two frames, clamped, ease-out. */
export const t = (f: number, a: number, b: number) =>
  interpolate(f, [a, b], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: OUT });

/** Rise-and-fade entrance. `side` shifts along the reading direction instead of up. */
export const enter = (f: number, at: number, dir: "rtl" | "ltr", side = false, dist = 34) => {
  const p = t(f, at, at + 18);
  const s = dir === "rtl" ? 1 : -1;
  return { opacity: p, translate: side ? `${s * dist * (1 - p)}px 0px` : `0px ${dist * (1 - p)}px` };
};

export type Lang = "ar" | "en";
export const lh = (lang: Lang) => (lang === "ar" ? 1.5 : 1.25); // R-DESIGN-009: Arabic needs its own leading

/** Frame override for the PDF twin: slides render outside Remotion at their final state.
 *  null (the default, and always inside a Remotion render) means "use the real frame". */
export const FrameOverride = React.createContext<number | null>(null);
export const useF = (): number => {
  const o = React.useContext(FrameOverride);
  // eslint-disable-next-line react-hooks/rules-of-hooks
  return o !== null ? o : useCurrentFrame();
};

/** Full-frame layer: a plain div, so the same slide renders inside and outside Remotion
 *  (4.0.5xx AbsoluteFill reads the timeline and throws outside a composition). */
export const Fill = (p: { style?: React.CSSProperties; children?: React.ReactNode }) =>
  React.createElement("div", { style: { position: "absolute", inset: 0, display: "flex", flexDirection: "column", ...p.style } }, p.children);

/** Remotion's <Img> while rendering video (it waits for the load), a plain <img> in the PDF twin. */
export const Pic = (p: { src: string; style?: React.CSSProperties }) => {
  const o = React.useContext(FrameOverride);
  return o !== null ? React.createElement("img", { src: p.src, style: p.style }) : React.createElement(Img, { src: p.src, style: p.style });
};
