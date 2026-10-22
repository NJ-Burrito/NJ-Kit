// One config per project, copied in at project setup — never installed mid-build.
import {Config} from "@remotion/cli/config";
import {enableTailwind} from "@remotion/tailwind-v4";

Config.overrideWebpackConfig((c) => enableTailwind(c));
Config.setPixelFormat("yuva420p"); // alpha, matches the Manim pre-render contract
Config.setCodec("vp8");            // vp9 also carries alpha; vp8 is the documented default
