import React from "react";
import {
  AbsoluteFill,
  Easing,
  interpolate,
  staticFile,
  continueRender,
  delayRender,
} from "remotion";

// Palette taken from the tested site.
export const RED = "#EC3013";
export const INK = "#1A1A1A";
export const PAPER = "#FFFFFF";
export const GREY = "#F3F2F2";
export const MUTE = "#6B6A69";
export const OK = "#2E7D32";

export const DISPLAY = "'Thmanyah Serif Display', serif";
export const SANS = "'Thmanyah Sans', sans-serif";

// House face, loaded from public/fonts so the render never depends on system lookup.
const faces: [string, string, string][] = [
  ["Thmanyah Serif Display", "thmanyahserifdisplay-Medium.otf", "500"],
  ["Thmanyah Serif Display", "thmanyahserifdisplay-Bold.otf", "700"],
  ["Thmanyah Sans", "thmanyahsans-Regular.otf", "400"],
  ["Thmanyah Sans", "thmanyahsans-Medium.otf", "500"],
  ["Thmanyah Sans", "thmanyahsans-Bold.otf", "700"],
];
if (typeof document !== "undefined") {
  const handle = delayRender("fonts");
  Promise.all(
    faces.map(([family, file, weight]) => {
      const f = new FontFace(family, `url(${staticFile("fonts/" + file)})`, { weight });
      return f.load().then((l) => document.fonts.add(l));
    }),
  ).then(() => continueRender(handle));
}

const OUT = Easing.bezier(0.16, 1, 0.3, 1);

/** 0→1 between two frames, clamped, ease-out. */
export const t = (frame: number, a: number, b: number) =>
  interpolate(frame, [a, b], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: OUT,
  });

/** A pulsing red box drawn over a region (image pixels × scale). */
export const Pulse: React.FC<{
  frame: number;
  at: number;
  x: number;
  y: number;
  w: number;
  h: number;
  label?: string;
  labelBelow?: boolean;
  labelRight?: boolean;
}> = ({ frame, at, x, y, w, h, label, labelBelow, labelRight }) => {
  const k = t(frame, at, at + 12);
  const beat = frame > at + 12 ? 0.5 + 0.5 * Math.cos(((frame - at - 12) / 30) * Math.PI * 2) : 1;
  return (
    <>
      <div
        style={{
          position: "absolute",
          left: x,
          top: y,
          width: w,
          height: h,
          border: `4px solid ${RED}`,
          borderRadius: 10,
          boxShadow: `0 0 ${10 + 16 * beat}px rgba(236,48,19,${0.25 + 0.35 * beat})`,
          opacity: k,
          scale: String(1.25 - 0.25 * k),
        }}
      />
      {label ? (
        <div style={{ position: "absolute", left: labelRight ? x + w - 1200 : x, width: 1200,
          top: labelBelow ? y + h + 10 : y - 48, display: "flex",
          justifyContent: labelRight ? "flex-end" : "flex-start" }}>
          <div
            style={{
              background: RED,
              color: PAPER,
              fontFamily: SANS,
              fontWeight: 700,
              fontSize: 24,
              padding: "6px 14px",
              borderRadius: 8,
              whiteSpace: "nowrap",
              opacity: t(frame, at + 8, at + 20),
              translate: `0px ${(1 - t(frame, at + 8, at + 20)) * 12}px`,
            }}
          >
            {label}
          </div>
        </div>
      ) : null}
    </>
  );
};

/** A tick or a cross, drawn as SVG (the house face has no ✓ or ✕ glyphs). */
export const Mark: React.FC<{ ok: boolean; p: number; size?: number }> = ({ ok, p, size = 40 }) => {
  const len = 60;
  return (
    <svg width={size} height={size} viewBox="0 0 40 40" style={{ flex: "0 0 auto" }}>
      <circle cx="20" cy="20" r="19" fill={ok ? OK : RED} opacity={Math.min(1, p * 2)} />
      {ok ? (
        <path d="M11 21 L17 27 L29 13" stroke={PAPER} strokeWidth="4" fill="none"
          strokeLinecap="round" strokeLinejoin="round" strokeDasharray={len} strokeDashoffset={len * (1 - p)} />
      ) : (
        <path d="M13 13 L27 27 M27 13 L13 27" stroke={PAPER} strokeWidth="4" fill="none"
          strokeLinecap="round" strokeDasharray={len} strokeDashoffset={len * (1 - p)} />
      )}
    </svg>
  );
};

export const Fill: React.FC<{ bg: string; children: React.ReactNode }> = ({ bg, children }) => (
  <AbsoluteFill style={{ background: bg, fontFamily: SANS, color: INK }}>{children}</AbsoluteFill>
);
