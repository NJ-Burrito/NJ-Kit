import React from "react";
import { C, DISPLAY, TEXT, t, enter, Lang, lh, useF, Fill } from "./theme";
import { Rich, splitRow } from "./rich";
import { F1Map, F3Killed, F5Cash, F8Plan } from "./figures";

export type SlideData = {
  id: string; kind: "title" | "divider" | "content"; label: string; heading: string;
  body: string[]; note: string; figure: string | null;
};
export type Deck = { title: string; subtitle: string; date: string; dir: "rtl" | "ltr"; internalLabel: string; slides: SlideData[] };
export type Props = { deck: Deck; index: number; lang: Lang };

const PADX = 112;

// ── motifs ───────────────────────────────────────────────────────────────────
/** The canal as one drawn line with sites along it; draws in reading direction (R-DESIGN-012). */
const Canal: React.FC<{ f: number; at: number; dir: "rtl" | "ltr"; y: number; opacity?: number; sites?: number }> = ({ f, at, dir, y, opacity = 1, sites = 9 }) => {
  const p = t(f, at, at + 60);
  const d = "M -20 60 C 260 10, 420 110, 700 60 S 1160 20, 1380 70 S 1760 110, 1940 50";
  const pts = Array.from({ length: sites }, (_, i) => 90 + i * ((1740) / (sites - 1)));
  return (
    <svg width={1920} height={140} style={{ position: "absolute", left: 0, top: y, opacity, scale: dir === "rtl" ? "-1 1" : "1 1" }}>
      <path d={d} fill="none" stroke={C.teal} strokeWidth={6} strokeLinecap="round" pathLength={1} strokeDasharray={1} strokeDashoffset={1 - p} />
      {pts.map((x, i) => {
        const q = t(f, at + 18 + i * 5, at + 30 + i * 5);
        const hot = i === 2 || i === 6;
        return <circle key={i} cx={x} cy={60 + 38 * Math.sin((x / 1940) * Math.PI * 3.1)} r={(hot ? 12 : 7) * q}
          fill={hot ? C.lime : C.paper} opacity={hot ? 1 : 0.8} />;
      })}
    </svg>
  );
};

/** Sound rings from one point: the acoustic range test. */
const Rings: React.FC<{ f: number; at: number }> = ({ f, at }) => (
  <svg width={620} height={620} viewBox="-310 -310 620 620">
    {[0, 1, 2, 3].map((i) => {
      const k = ((f - at - i * 14) % 56) / 56;
      const on = f - at - i * 14 > 0;
      return <circle key={i} r={40 + 250 * (on ? k : 0)} fill="none" stroke={C.teal} strokeWidth={5} opacity={on ? 0.9 * (1 - k) : 0} />;
    })}
    <circle r={34} fill={C.navy} />
    <circle r={12} fill={C.lime} />
  </svg>
);

// ── chrome ───────────────────────────────────────────────────────────────────
const Footer: React.FC<{ deck: Deck; index: number; dark: boolean }> = ({ deck, index, dark }) => (
  <div style={{ position: "absolute", left: PADX, right: PADX, bottom: 42, display: "flex", justifyContent: "space-between",
    fontFamily: TEXT, fontSize: 20, color: dark ? "rgba(243,248,249,.62)" : C.mute }}>
    <span>{deck.title} · {deck.internalLabel}</span>
    <span style={{ fontFamily: DISPLAY, fontWeight: 700 }}>{index}</span>
  </div>
);
const Kicker: React.FC<{ s: string; f: number; dir: "rtl" | "ltr"; dark?: boolean }> = ({ s, f, dir, dark }) => (
  <div style={{ fontFamily: DISPLAY, fontWeight: 700, fontSize: 28, color: dark ? C.lime : C.teal, ...enter(f, 0, dir, true, 20) }}>{s}</div>
);
const Heading: React.FC<{ s: string; f: number; dir: "rtl" | "ltr"; lang: Lang; size?: number; dark?: boolean; width?: number }> = ({ s, f, dir, lang, size = 60, dark, width = 1600 }) => (
  <div style={{ fontFamily: DISPLAY, fontWeight: 700, fontSize: size, lineHeight: lang === "ar" ? 1.4 : 1.15, marginTop: 18, maxWidth: width,
    color: dark ? C.paper : C.ink, ...enter(f, 4, dir) }}>
    <Rich s={s} dark={dark} nums={false} />
  </div>
);

const Row: React.FC<{ label: string; value: string; i: number; f: number; dir: "rtl" | "ltr"; lang: Lang; at: number; compact?: boolean }> = ({ label, value, i, f, dir, lang, at, compact }) => (
  <div style={{ display: "flex", gap: 28, alignItems: "flex-start", background: C.white, borderRadius: 22,
    padding: compact ? "20px 28px" : "32px 42px", boxShadow: "0 14px 40px rgba(11,31,42,.08)", ...enter(f, at + i * 8, dir, true, 60) }}>
    <div style={{ fontFamily: DISPLAY, fontWeight: 900, fontSize: compact ? 34 : 40, color: C.teal, lineHeight: 1, minWidth: 58, paddingTop: 6 }}>
      {String(i + 1).padStart(2, "0")}
    </div>
    <div style={{ lineHeight: lh(lang) }}>
      <div style={{ fontFamily: DISPLAY, fontWeight: 700, fontSize: compact ? 27 : 36, color: C.ink }}><Rich s={label} nums={false} /></div>
      <div style={{ fontFamily: TEXT, fontSize: compact ? 25 : 32, color: C.ink, marginTop: 6 }}><Rich s={value} /></div>
    </div>
  </div>
);

const Para: React.FC<{ s: string; f: number; dir: "rtl" | "ltr"; lang: Lang; at: number; size?: number; dark?: boolean }> = ({ s, f, dir, lang, at, size = 38, dark }) => (
  <div style={{ fontFamily: TEXT, fontSize: size, lineHeight: lang === "ar" ? 1.75 : 1.5, color: dark ? C.paper : C.ink, ...enter(f, at, dir) }}>
    <Rich s={s} dark={dark} />
  </div>
);

const Body: React.FC<{ lines: string[]; f: number; dir: "rtl" | "ltr"; lang: Lang; at: number; compact?: boolean; paraSize?: number }> = ({ lines, f, dir, lang, at, compact, paraSize }) => (
  <div style={{ display: "flex", flexDirection: "column", gap: compact ? 16 : 26 }}>
    {lines.map((b, i) => {
      const r = splitRow(b);
      return r ? <Row key={i} {...r} i={i} f={f} dir={dir} lang={lang} at={at} compact={compact} />
        : <Para key={i} s={b} f={f} dir={dir} lang={lang} at={at + i * 8} size={paraSize} />;
    })}
  </div>
);

// ── slide kinds ──────────────────────────────────────────────────────────────
const TitleSlide: React.FC<Props> = ({ deck, lang }) => {
  const f = useF();
  const dir = deck.dir;
  return (
    <Fill style={{ background: C.navy, direction: dir, color: C.paper, padding: `0 ${PADX}px`, justifyContent: "center" }}>
      <div style={{ fontFamily: DISPLAY, fontWeight: 700, fontSize: 30, color: C.lime, ...enter(f, 0, dir, true, 24) }}>Ensera</div>
      <div style={{ fontFamily: DISPLAY, fontWeight: 900, fontSize: lang === "ar" ? 128 : 116, lineHeight: 1.15, marginTop: 14, ...enter(f, 6, dir) }}>{deck.title}</div>
      <div style={{ fontFamily: TEXT, fontSize: 40, marginTop: 26, color: "rgba(243,248,249,.85)", ...enter(f, 14, dir) }}>{deck.subtitle}</div>
      <div style={{ fontFamily: TEXT, fontSize: 30, marginTop: 12, color: "rgba(243,248,249,.62)", ...enter(f, 20, dir) }}><bdi>{deck.date}</bdi></div>
      <Canal f={f} at={10} dir={dir} y={820} />
    </Fill>
  );
};

const DividerSlide: React.FC<Props & { s: SlideData }> = ({ deck, index, s }) => {
  const f = useF();
  const dir = deck.dir;
  return (
    <Fill style={{ background: C.navy, direction: dir, color: C.paper, padding: `0 ${PADX}px`, justifyContent: "center" }}>
      <div style={{ width: 120, height: 8, borderRadius: 4, background: C.lime, ...enter(f, 0, dir, true, 40) }} />
      <div style={{ fontFamily: DISPLAY, fontWeight: 900, fontSize: 104, lineHeight: 1.25, marginTop: 34, ...enter(f, 6, dir) }}>{s.heading}</div>
      <Canal f={f} at={14} dir={dir} y={800} opacity={0.55} />
      <Footer deck={deck} index={index} dark />
    </Fill>
  );
};

/** S1: the question, and the 90-day test drawn as a closing ring. */
const OpenerSlide: React.FC<Props & { s: SlideData }> = ({ deck, index, s, lang }) => {
  const f = useF();
  const dir = deck.dir;
  const p = t(f, 20, 95);
  const R = 200, L = 2 * Math.PI * R;
  return (
    <Fill style={{ background: C.navy, direction: dir, color: C.paper, padding: `110px ${PADX}px`, flexDirection: "row", alignItems: "center", gap: 90 }}>
      <div style={{ flex: 1 }}>
        <Kicker s={s.label} f={f} dir={dir} dark />
        <Heading s={s.heading} f={f} dir={dir} lang={lang} size={66} dark width={1000} />
        <div style={{ marginTop: 40 }}><Para s={s.body[0]} f={f} dir={dir} lang={lang} at={22} size={34} dark /></div>
      </div>
      <div style={{ position: "relative", width: 480, height: 480, flex: "0 0 auto", opacity: t(f, 10, 24) }}>
        <svg width={480} height={480} viewBox="-240 -240 480 480" style={{ rotate: "-90deg" }}>
          <circle r={R} fill="none" stroke={C.navy2} strokeWidth={26} />
          <circle r={R} fill="none" stroke={C.lime} strokeWidth={26} strokeLinecap="round" strokeDasharray={L} strokeDashoffset={L * (1 - p)} />
        </svg>
        <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center",
          fontFamily: DISPLAY, fontWeight: 900, fontSize: 190, color: C.paper, direction: "ltr" }}>{Math.round(90 * p)}</div>
      </div>
      <Footer deck={deck} index={index} dark />
    </Fill>
  );
};

/** S13: the ask — two option cards side by side, the open question under them. */
const AskSlide: React.FC<Props & { s: SlideData }> = ({ deck, index, s, lang }) => {
  const f = useF();
  const dir = deck.dir;
  const rows = s.body.map((b) => splitRow(b)!);
  return (
    <Fill style={{ background: C.navy, direction: dir, color: C.paper, padding: `90px ${PADX}px 150px`, justifyContent: "center" }}>
      <Kicker s={s.label} f={f} dir={dir} dark />
      <Heading s={s.heading} f={f} dir={dir} lang={lang} size={60} dark />
      <div style={{ display: "flex", gap: 40, marginTop: 60 }}>
        {rows.slice(0, 2).map((r, i) => (
          <div key={i} style={{ flex: 1, background: C.navy2, borderRadius: 28, padding: "54px 56px", lineHeight: lh(lang),
            border: `2px solid ${i === 0 ? C.lime : "rgba(243,248,249,.18)"}`, ...enter(f, 20 + i * 10, dir, false, 50) }}>
            <div style={{ fontFamily: DISPLAY, fontWeight: 900, fontSize: 42, color: C.lime }}><Rich s={r.label} dark nums={false} strong={C.lime} /></div>
            <div style={{ fontFamily: TEXT, fontSize: 34, marginTop: 20 }}><Rich s={r.value} dark /></div>
          </div>
        ))}
      </div>
      {rows[2] ? (
        <div style={{ marginTop: 48, display: "flex", gap: 26, alignItems: "baseline", ...enter(f, 44, dir) }}>
          <span style={{ fontFamily: DISPLAY, fontWeight: 700, fontSize: 38, color: C.teal }}><Rich s={rows[2].label} dark nums={false} strong={C.teal} /></span>
          <span style={{ fontFamily: TEXT, fontSize: 38 }}><Rich s={rows[2].value} dark /></span>
        </div>
      ) : null}
      <Footer deck={deck} index={index} dark />
    </Fill>
  );
};

const ContentSlide: React.FC<Props & { s: SlideData }> = ({ deck, index, s, lang }) => {
  const f = useF();
  const dir = deck.dir;
  const fig = s.figure;
  const onlyPara = s.body.length === 1 && !splitRow(s.body[0]);
  const isAcoustic = s.id === "S8";
  const bigMap = fig === "F1" && s.id === "S7";
  const figEl = fig === "F1" ? <F1Map lang={lang} at={26} big={bigMap} />
    : fig === "F3" ? <F3Killed lang={lang} at={24} width={860} />
    : fig === "F5" ? <F5Cash lang={lang} at={24} width={900} />
    : fig === "F8" ? <F8Plan lang={lang} at={24} width={900} /> : null;
  return (
    <Fill style={{ background: C.paper, direction: dir, color: C.ink, padding: `84px ${PADX}px 120px` }}>
      <Kicker s={s.label} f={f} dir={dir} />
      <div style={{ display: "flex", gap: 64, flex: 1, marginTop: 4 }}>
        <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
          <Heading s={s.heading} f={f} dir={dir} lang={lang} size={figEl ? (bigMap ? 48 : 52) : 60} />
          <div style={{ marginTop: figEl ? 34 : 40, flex: 1, display: "flex", flexDirection: "column", justifyContent: figEl ? "flex-start" : "center", paddingBottom: figEl ? 0 : 60 }}>
            <Body lines={s.body} f={f} dir={dir} lang={lang} at={18} compact={!!figEl} paraSize={figEl ? 30 : 38} />
          </div>
        </div>
        {figEl ? <div style={{ flex: "0 0 auto", alignSelf: "center", marginTop: 20 }}>{figEl}</div> : null}
        {isAcoustic ? <div style={{ flex: "0 0 auto", alignSelf: "center" }}><Rings f={f} at={20} /></div> : null}
      </div>
      {onlyPara && !figEl && !isAcoustic ? <Canal f={f} at={24} dir={dir} y={800} opacity={0.35} sites={7} /> : null}
      <Footer deck={deck} index={index} dark={false} />
    </Fill>
  );
};

export const Slide: React.FC<Props> = (props) => {
  const { deck, index } = props;
  if (index === 0) return <TitleSlide {...props} />;
  const s = deck.slides[index - 1];
  if (s.kind === "divider") return <DividerSlide {...props} s={s} />;
  if (s.id === "S1") return <OpenerSlide {...props} s={s} />;
  if (s.id === "S13") return <AskSlide {...props} s={s} />;
  return <ContentSlide {...props} s={s} />;
};
