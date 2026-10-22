import {registerRoot, Composition} from "remotion";
import {SceneComposition} from "./Scene";
import props from "./props.json";
import "./style.css"; // Tailwind entry — @tailwind base/components/utilities

const Root: React.FC = () =>
  Composition({
    id: "SceneComposition",
    component: SceneComposition,
    durationInFrames: Math.round((props.durationSeconds ?? 2) * 30),
    fps: 30,
    width: 1920,
    height: 1080,
    defaultProps: props,
  });

registerRoot(Root);
