// Data-driven template: rows (props.json) in, frames out. One composition per
// tagged scene. House face is a local @font-face, never a CDN font.
import {AbsoluteFill} from "remotion";

export const SceneComposition: React.FC<{title?: string}> = ({title}) => (
  <AbsoluteFill className="items-center justify-center bg-transparent">
    <style>{`
      @font-face {
        font-family: 'Thmanyah';
        src: url('./fonts/thmanyah-sans-Bold.w700.woff2') format('woff2');
        font-weight: 700;
      }
    `}</style>
    <h1 style={{fontFamily: "Thmanyah", fontSize: 96, color: "#fff"}}>{title}</h1>
  </AbsoluteFill>
);
