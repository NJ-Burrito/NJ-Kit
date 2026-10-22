import React from "react";
import { staticFile, interpolate } from "remotion";
import { C, DISPLAY, TEXT, t, Lang, lh, useF, Pic } from "./theme";
import FIG from "./data/figures.json";

type L2 = { en: string; ar: string };
const tr = (x: L2, lang: Lang) => x[lang];

const Panel: React.FC<{ children: React.ReactNode; dark?: boolean; style?: React.CSSProperties }> = ({ children, dark = true, style }) => (
  <div style={{ background: dark ? C.navy2 : C.white, borderRadius: 26, padding: "34px 38px", color: dark ? C.paper : C.ink,
    boxShadow: dark ? "none" : "0 18px 50px rgba(11,31,42,.10)", ...style }}>{children}</div>
);
const Title: React.FC<{ s: string; dark?: boolean }> = ({ s, dark = true }) => (
  <div style={{ fontFamily: DISPLAY, fontWeight: 500, fontSize: 26, lineHeight: 1.35, color: dark ? C.paper : C.ink, marginBottom: 22 }}>{s}</div>
);

// ── F1 · NDVI corridor scan: the real Sentinel-2 raster, a scan sweep, an honest legend ─────
export const F1Map: React.FC<{ lang: Lang; at: number; big?: boolean }> = ({ lang, at, big }) => {
  const f = useF();
  const F = FIG.F1;
  const W = big ? 840 : 740, H = Math.round(W * 612 / 748);
  const sweep = interpolate(f, [at + 10, at + 70], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const x = lang === "ar" ? W * (1 - sweep) : W * sweep;
  return (
    <div style={{ width: W, opacity: t(f, at, at + 16) }}>
      <div style={{ position: "relative", width: W, height: H, borderRadius: 22, overflow: "hidden", boxShadow: "0 18px 50px rgba(11,31,42,.16)" }}>
        <Pic src={staticFile("ndvi.png")} style={{ width: W, height: H, display: "block", scale: String(1.06 - 0.06 * t(f, at, at + 90)) }} />
        {sweep > 0 && sweep < 1 ? (
          <div style={{ position: "absolute", top: 0, left: x - 3, width: 6, height: H, background: C.teal,
            boxShadow: `0 0 40px 14px rgba(15,157,154,.55)` }} />
        ) : null}
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 14, marginTop: 16, direction: "ltr", opacity: t(f, at + 60, at + 76) }}>
        <span style={{ fontFamily: TEXT, fontSize: 18, color: C.mute }}>-0.2</span>
        <div style={{ flex: 1, height: 12, borderRadius: 6, background: "linear-gradient(90deg,#f7fcf5,#c7e9c0,#74c476,#238b45,#00441b)" }} />
        <span style={{ fontFamily: TEXT, fontSize: 18, color: C.mute }}>0.8</span>
        <span style={{ fontFamily: TEXT, fontWeight: 700, fontSize: 18, color: C.ink }}>NDVI</span>
      </div>
      <div style={{ opacity: t(f, at + 66, at + 82), marginTop: 12, lineHeight: lh(lang) }}>
        <div style={{ fontFamily: DISPLAY, fontWeight: 500, fontSize: 22, color: C.ink }}>{tr(F.title, lang)}</div>
        <div style={{ fontFamily: TEXT, fontSize: 19, color: C.mute }}>{tr(F.note, lang)}</div>
        <div style={{ fontFamily: TEXT, fontSize: 16, color: C.mute }}>{tr(F.credit, lang)}</div>
      </div>
    </div>
  );
};

// ── F3 · What the research killed: each claim is struck through as its finding lands ─────────
export const F3Killed: React.FC<{ lang: Lang; at: number; width: number }> = ({ lang, at, width }) => {
  const f = useF();
  const F = FIG.F3;
  return (
    <Panel style={{ width, opacity: t(f, at, at + 14) }}>
      <Title s={tr(F.title, lang)} />
      {F.rows.map(([claim, found], i) => {
        const a = at + 12 + i * 12, strike = t(f, a + 10, a + 26);
        return (
          <div key={i} style={{ padding: "14px 0", borderTop: i ? "1px solid rgba(243,248,249,.14)" : "none", opacity: t(f, a, a + 12) }}>
            <div style={{ position: "relative", display: "inline-block", fontFamily: DISPLAY, fontWeight: 500, fontSize: 27, lineHeight: lh(lang) }}>
              {tr(claim, lang)}
              <div style={{ position: "absolute", top: "54%", [lang === "ar" ? "right" : "left"]: 0, height: 4, borderRadius: 2,
                width: `${strike * 100}%`, background: C.coral }} />
            </div>
            <div style={{ fontFamily: TEXT, fontSize: 21, lineHeight: lh(lang), color: "rgba(243,248,249,.78)", opacity: t(f, a + 20, a + 32) }}>
              {tr(found, lang)}
            </div>
          </div>
        );
      })}
    </Panel>
  );
};

// ── F5 · Role A cumulative cash flow: three scenario lines draw in, time runs left to right ───
export const F5Cash: React.FC<{ lang: Lang; at: number; width: number }> = ({ lang, at, width }) => {
  const f = useF();
  const F = FIG.F5;
  const W = width - 76, H = 380, padL = 118, padR = 150, padT = 16, padB = 46;
  const min = -50000, max = 450000;
  const X = (i: number) => padL + (i / 4) * (W - padL - padR);
  const Y = (v: number) => padT + (1 - (v - min) / (max - min)) * (H - padT - padB);
  const keys = ["low", "base", "high"] as const;
  const col = { low: C.coral, base: C.blue, high: C.green };
  const fmt = (v: number) => Math.round(v).toLocaleString("en-US");
  const note = tr(F.note as L2, lang).replace("{base_npv}", F.npv.base).replace("{high_npv}", F.npv.high).replace("{low_npv}", F.npv.low);
  return (
    <Panel style={{ width, opacity: t(f, at, at + 14) }}>
      <Title s={tr(F.title, lang)} />
      <svg width={W} height={H} style={{ direction: "ltr", overflow: "visible" }}>
        {[0, 100000, 200000, 300000, 400000].map((v) => (
          <g key={v}>
            <line x1={padL} x2={W - padR} y1={Y(v)} y2={Y(v)} stroke={v === 0 ? "rgba(243,248,249,.55)" : "rgba(243,248,249,.12)"} strokeWidth={v === 0 ? 2 : 1} />
            <text x={padL - 14} y={Y(v) + 7} textAnchor="end" fill="rgba(243,248,249,.7)" style={{ fontFamily: TEXT, fontSize: 19 }}>{fmt(v)}</text>
          </g>
        ))}
        {[1, 2, 3, 4, 5].map((yr, i) => (
          <text key={yr} x={X(i)} y={H - 12} textAnchor="middle" fill="rgba(243,248,249,.7)" style={{ fontFamily: TEXT, fontSize: 20 }}>{yr}</text>
        ))}
        {keys.map((k, ki) => {
          const p = t(f, at + 16 + ki * 10, at + 70 + ki * 10);
          const pts = F.series[k].map((v: number, i: number) => `${X(i)},${Y(v)}`).join(" ");
          const last = F.series[k][4];
          return (
            <g key={k}>
              <polyline points={pts} fill="none" stroke={col[k]} strokeWidth={5} strokeLinejoin="round" strokeLinecap="round"
                pathLength={1} strokeDasharray={1} strokeDashoffset={1 - p} />
              <circle cx={X(4)} cy={Y(last)} r={8 * t(f, at + 66 + ki * 10, at + 76 + ki * 10)} fill={col[k]} />
              <text x={X(4) + 18} y={Y(last) + (k === "low" ? 22 : k === "base" ? -6 : 7)} fill={col[k]}
                style={{ fontFamily: DISPLAY, fontWeight: 700, fontSize: 22, opacity: t(f, at + 70 + ki * 10, at + 82 + ki * 10) }}>
                {tr(F.names[k], lang)} {fmt(last)}
              </text>
            </g>
          );
        })}
      </svg>
      <div style={{ fontFamily: TEXT, fontSize: 18, color: "rgba(243,248,249,.72)", marginTop: 10, lineHeight: lh(lang), opacity: t(f, at + 84, at + 96) }}>
        {tr(F.year, lang)}: 1-5 · {note}
      </div>
    </Panel>
  );
};

// ── F8 · Phase 0 plan: a 90-day Gantt, bars grow as the plan is read ───────────────────────
export const F8Plan: React.FC<{ lang: Lang; at: number; width: number }> = ({ lang, at, width }) => {
  const f = useF();
  const F = FIG.F8;
  const trackW = Math.round((width - 76) * 0.5);
  const pos = (d: number) => (d / 90) * trackW;
  return (
    <Panel style={{ width, opacity: t(f, at, at + 14) }}>
      <Title s={tr(F.title, lang)} />
      <div style={{ display: "flex", justifyContent: "space-between", fontFamily: TEXT, fontWeight: 700, fontSize: 18, color: C.lime, marginBottom: 8 }}>
        <span>{tr(F.head[0], lang)}</span>
        <span style={{ width: trackW, display: "flex", justifyContent: "space-between", direction: "ltr" }}>
          {[0, 30, 60, 90].map((d) => <span key={d}>{d}</span>)}
        </span>
      </div>
      {F.rows.map((r, i) => {
        const a = at + 12 + i * 9, g = t(f, a + 6, a + 26);
        const running = r.days.en === "running", mile = r.from === r.to;
        return (
          <div key={i} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "9px 0",
            borderTop: "1px solid rgba(243,248,249,.12)", opacity: t(f, a, a + 12) }}>
            <div style={{ lineHeight: 1.3 }}>
              <div style={{ fontFamily: DISPLAY, fontWeight: 500, fontSize: 22 }}>{tr(r.step, lang)}</div>
              <div style={{ fontFamily: TEXT, fontSize: 17, color: "rgba(243,248,249,.7)" }}>
                {tr(F.head[2], lang)}: {tr(r.owner, lang)} · {tr(F.head[3], lang)}: <bdi>{tr(r.cash, lang)}</bdi>
              </div>
            </div>
            <div style={{ position: "relative", width: trackW, height: 22, direction: "ltr", flex: "0 0 auto" }}>
              <div style={{ position: "absolute", inset: "9px 0", background: "rgba(243,248,249,.10)", borderRadius: 3 }} />
              {mile ? (
                <div style={{ position: "absolute", left: pos(r.to) - 12, top: -1, width: 24, height: 24, background: C.lime,
                  rotate: "45deg", scale: String(g) }} />
              ) : (
                <div style={{ position: "absolute", left: pos(r.from), top: 2, height: 18, borderRadius: 9,
                  width: (pos(r.to) - pos(r.from)) * g, background: running ? "transparent" : C.teal,
                  border: running ? `2px dashed ${C.teal}` : "none", boxSizing: "border-box" }} />
              )}
            </div>
          </div>
        );
      })}
      <div style={{ fontFamily: TEXT, fontSize: 16, lineHeight: lh(lang), color: "rgba(243,248,249,.72)", marginTop: 14, opacity: t(f, at + 70, at + 84) }}>
        {tr(F.kill, lang)}
      </div>
    </Panel>
  );
};
