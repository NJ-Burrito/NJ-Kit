import React from "react";
import { C, DISPLAY, TEXT } from "./theme";

// The approved words carry provenance markers inline: **bold**, [A] (assumption),
// #552(draft) / #554(verified) (knowledge-base entry), *(E3)* (review edit).
// Nothing is dropped: each marker becomes a small chip, the words stay verbatim.
const TOKEN = /(\*\*[^*]+\*\*)|(\*\([^)]*\)\*)|(#\d+\([^)]*\))|(\[[AVU]\])/g;
const NUM = /(\d[\d,.]*\d|\d)(\s?%)?/g;

const chipBase: React.CSSProperties = {
  display: "inline-block", direction: "ltr", unicodeBidi: "isolate", fontFamily: TEXT, fontWeight: 700,
  fontSize: "0.56em", lineHeight: 1, padding: "0.28em 0.5em", borderRadius: "0.6em", margin: "0 0.28em",
  verticalAlign: "0.55em", letterSpacing: 0.3, whiteSpace: "nowrap",
};

const Chip: React.FC<{ raw: string; dark: boolean }> = ({ raw, dark }) => {
  if (raw.startsWith("[")) {
    return <span style={{ ...chipBase, background: C.amber, color: C.navy }}>{raw.slice(1, -1)}</span>;
  }
  if (raw.startsWith("#")) {
    const m = raw.match(/^#(\d+)\((.*)\)$/)!;
    const verified = m[2].startsWith("verified");
    const internal = m[2].includes("internal");
    return (
      <span style={{ ...chipBase, background: verified ? C.teal : "transparent", color: verified ? C.navy : dark ? C.paper : C.mute,
        border: verified ? "none" : `1.5px ${internal ? "dashed" : "solid"} ${dark ? "rgba(243,248,249,.55)" : C.mute}` }}>
        #{m[1]} {m[2]}
      </span>
    );
  }
  const inner = raw.slice(2, -2); // *(E2, E5)* -> E2, E5
  return <span style={{ ...chipBase, color: dark ? "rgba(243,248,249,.7)" : C.mute, padding: "0.28em 0.2em" }}>{inner}</span>;
};

/** Plain text with numbers set heavier, so figures read first. */
const Nums: React.FC<{ s: string; strong: string }> = ({ s, strong }) => {
  const out: React.ReactNode[] = [];
  let last = 0;
  for (const m of s.matchAll(NUM)) {
    if (m.index! > last) out.push(s.slice(last, m.index));
    out.push(<span key={m.index} style={{ fontFamily: DISPLAY, fontWeight: 700, color: strong }}>{m[0]}</span>);
    last = m.index! + m[0].length;
  }
  out.push(s.slice(last));
  return <>{out}</>;
};

export const Rich: React.FC<{ s: string; dark?: boolean; nums?: boolean; strong?: string }> = ({ s, dark = false, nums = true, strong }) => {
  const parts: React.ReactNode[] = [];
  let last = 0;
  const col = strong ?? (dark ? C.paper : C.navy);
  const plain = (x: string, k: string) => (nums ? <Nums key={k} s={x} strong={col} /> : <React.Fragment key={k}>{x}</React.Fragment>);
  for (const m of s.matchAll(TOKEN)) {
    if (m.index! > last) parts.push(plain(s.slice(last, m.index), "p" + last));
    const raw = m[0];
    if (raw.startsWith("**")) parts.push(<strong key={m.index} style={{ fontWeight: 700 }}>{raw.slice(2, -2)}</strong>);
    else parts.push(<Chip key={m.index} raw={raw} dark={dark} />);
    last = m.index! + raw.length;
  }
  if (last < s.length) parts.push(plain(s.slice(last), "p" + last));
  return <>{parts}</>;
};

/** "**Label** | value" -> {label, value}; anything else is a paragraph. */
export const splitRow = (line: string): { label: string; value: string } | null => {
  const i = line.indexOf(" | ");
  if (!line.startsWith("**") || i < 0) return null;
  return { label: line.slice(0, i).replace(/^\*\*/, "").replace(/\*\*(?=[^*]*$)/, ""), value: line.slice(i + 3) };
};
