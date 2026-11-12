# 03 - Rive and Theatre.js as direction tools (plus GSAP/Lottie comparison)

Lane: RIVE AND THEATRE.JS AS DIRECTION TOOLS (nj-animation-direction knowledge base)
Retrieved: 2026-11-13 (every entry). Method: nj-researcher (context7 for library docs, web fetch for vendor docs, npm registry and GitHub API for versions/issues; no registry hits needed). Nothing was installed, cloned or run.

## How to read the confidence labels

Pages were read through a fetch tool that returns an extracted summary, not raw HTML.

- **quote** = the fetch result put the words in quotation marks (likely exact, not byte-checked).
- **paraphrase** = the fetch result described the content in its own words.
- **source-read** = a TypeScript/C++ source or .d.ts file was fetched and its code read (still through the extractor).
- **registry** = npm registry JSON or GitHub API JSON (machine data, high trust for versions/dates).
- **single-source** = one page only. **vendor** = marketing/vendor claim. **search-snippet** = seen only in a search summary, page not opened (a lead, not a citation).
- **INFERENCE** = my own deduction from the cited entries; never a documented fact. Every inference names the entries it rests on.

Source type: **primary** = the tool maker's own docs, source, registry or issue tracker. **secondary** = third party. **community** = forum/blog/dev.to.

Versions seen on 2026-11-13: `@rive-app/canvas` / `webgl2` / `canvas-advanced` 2.50.0, `@rive-app/react-canvas` 4.39.0, `@theatre/core|studio|r3f` 0.7.2, `gsap` 3.15.1, `@lottiefiles/dotlottie-web` 0.83.2.

---

## A. Rive: versions, packages, licence, export

**RT-001** Current npm versions: `@rive-app/canvas` 2.50.0 (MIT), `@rive-app/webgl2` 2.50.0 (MIT), `@rive-app/canvas-advanced` 2.50.0 (MIT), `@rive-app/react-canvas` 4.39.0 (MIT, depends on `@rive-app/canvas` 2.50.0). `canvas` 2.50.0 was published by GitHub Actions with a SLSA provenance attestation.
Source: npm registry JSON, https://registry.npmjs.org/@rive-app/canvas/latest (and /webgl2/latest, /canvas-advanced/latest, /react-canvas/latest). Version 2.50.0, retrieved 2026-11-13. Type: primary. Confidence: registry.

**RT-002** The runtime ships very fast: rive-wasm 2.50.0 was published 2026-11-09, 2.49.4 on 2026-11-05, 2.49.3 on 2026-11-04, 2.49.2 on 2026-11-03, 2.49.1 on 2026-11-02, 2.49.0 on 2026-10-29. 2.50.0 adds opt-in `fetch()` for scripts on `@rive-app/webgl2-threads`; 2.49.0 introduced a shared replay worker for `webgl2-threads`; 2.48.0 added gamepad params. A `.riv` feature newer than the pinned runtime is skipped, not an error.
Source: GitHub Releases API, https://api.github.com/repos/rive-app/rive-wasm/releases (retrieved 2026-11-13); skip-behaviour from RT-005. Type: primary. Confidence: registry (release summaries paraphrased by the extractor).

**RT-003** Licence: the runtime repo `rive-app/rive-wasm` is MIT. Rive's pricing page says "No revenue share, no runtime fees, no royalties, and MIT open-source runtimes" (quote). Separately, "Free exports play a Rive splash screen. Upgrade to remove it." (quote); the Cadet plan and up ship "without the splash screen". The pricing page states no licence terms for commercial use of exported `.riv` beyond that.
Source: GitHub repo page https://github.com/rive-app/rive-wasm; Rive pricing https://rive.app/pricing; export doc https://rive.app/docs/editor/exporting/exporting-for-runtime ("Free plan exports play a Rive splash screen. Paid plans export without it.") (all retrieved 2026-11-13). Type: primary. Confidence: quote, two pages agree on the splash; the commercial-use gap is "not stated", not "allowed".

**RT-004** Web packages: `@rive-app/webgl2` is the recommended one (uses the Rive Renderer, "supports everything you can author in the Rive Editor"); Canvas2D packages share the same API with different trade-offs; `@rive-app/canvas-lite` is smaller and drops Rive Text, Layouts, Scripting and Audio; `@rive-app/canvas-advanced` is the low-level package with your own render loop; `@rive-app/webgl2-threads` needs a cross-origin-isolated page. The overview's examples pin `2.40.1` and advise manual updates.
Source: Rive web overview https://rive.app/docs/runtimes/web/web-js; repo README and CONTRIBUTING https://github.com/rive-app/rive-wasm (retrieved 2026-11-13). Type: primary. Confidence: paraphrase.

**RT-005** `.riv` is the production asset: it keeps artboards, animations, state machines, data binding and scripts; `.rev` is the editable backup. Files are backward compatible: "a file from the latest editor can load in older runtimes"; a feature newer than the runtime "is skipped while the rest of the file still runs". An agent therefore cannot tell from a successful load that every feature played.
Source: Rive docs, Exporting for runtime, https://rive.app/docs/editor/exporting/exporting-for-runtime (retrieved 2026-11-13). Type: primary. Confidence: paraphrase with quoted fragments.

**RT-006** Editor video export exists: Cloud Renderer, paid plans only, formats H.264 (.mp4), WebM, GIF, PNG sequence, SVG sequence; presets per artboard; two modes: Animation ("renders a single timeline") and State Machine ("renders a State Machine as it plays over time"). Frame rate and size are settable; no maximum is documented. The page does not say how a state-machine render receives its inputs.
Source: Rive docs, Exporting for Video or Static Design, https://rive.app/docs/editor/exporting/exporting-for-video-and-static-design (retrieved 2026-11-13). Type: primary. Confidence: quote/paraphrase. Input handling: not documented.

## B. Rive: authoring model (what a director can design in the editor)

**RT-007** State machine layers run concurrently; "To play more than one animation at once, add more layers." Each layer is its own graph; the docs' example is one layer for idle/walk and another for blinking. If two layers animate the same property, "the layer lower in the list wins"; different properties: order does not matter. Layers can be disabled to test one at a time.
Source: Rive docs, State machine layers, https://rive.app/docs/editor/state-machine/layers (retrieved 2026-11-13). Type: primary. Confidence: quote.

**RT-008** State types: every layer has Entry, Any and Exit states. An animation state ("Single") plays one timeline, with a Speed (negative plays backward). Blend states on that page are 1D (mixes timelines by one number) and Additive (stack …"Mix by value", "Mix by view model" or "Mix by input"). No "Direct" blend is mentioned on that page. "Randomize Exit" picks one outgoing transition at random, weighted by each transition's Factor. States can run actions on start/end (set a view model property, report an event, move focus).
Source: Rive docs, States, https://rive.app/docs/editor/state-machine/states (retrieved 2026-11-13). Type: primary. Confidence: paraphrase.

**RT-009** Transitions: conditions have source value, operator and comparison value; "All conditions must be met"; separate transitions between the same two states give "or". Duration defaults to zero ("happens immediately"), with an Interpolation easing (default linear); Exit Time (off by default; time or percentage; 100% fires after the timeline finished); "Allow exit during transition" controls interruptibility; "Pause Source When Exiting". The page does not describe trigger-consumption semantics or how multiple outgoing transitions are prioritised.
Source: Rive docs, Transitions, https://rive.app/docs/editor/state-machine/transitions (retrieved 2026-11-13). Type: primary. Confidence: quote. Priority/trigger semantics: not documented here.

**RT-010** Listeners have a target, a "listen to"and an action. Listen-to types: pointer (Enter, Exit, Move, Down, Up, Drag, Click), Focus/Blur, Keyboard, Text Input, Gamepad, Semantic Action, View Model Change and Rive …"strongly recommend[s] using Data Binding to communicate between artboards instead of relying on nested Rive events".
Source: Rive docs, Listeners, https://rive.app/docs/editor/state-machine/listeners (retrieved 2026-11-13). Type: primary. Confidence: quote/paraphrase.

**RT-011** State machine inputs (Number, Boolean, Trigger) and runtime Events are DEPRECATED in favour of data binding. Rive's migration guide: "Inputs are limited to driving state machine transitions and must be used as-is"; "View model properties always reflect the latest value and can be observed directly"; existing files keep working and "You do not need to update existing files"; the editor has "Convert Inputs to View Models"in the hamburger menu; events become view-model properties (trigger/list) updated from an animation, listener or script and subscribed to in runtime code. The Events page …"DEPRECATED: Use Data Binding instead of Events" ("legacy support only"). No version or date is given on either page.
Source: https://rive.app/docs/editor/data-binding/migration-guide and https://rive.app/docs/runtimes/web/rive-events (retrieved 2026-11-13). Type: primary. Confidence: quote.

**RT-012** Data binding model: view models "define the structure of your data", view model instances hold the values, bindings "connect View Model data to properties in your scene"; data can be updated "from the Editor, runtime code, state machines, or scripting". Runtime property types (web API): number, boolean, string, color, enum, trigger, list, image, font, artboard, nested viewModel. View model properties can drive blend states and other bindable properties, use converters and be shared across a file (inputs cannot).
Source: https://rive.app/docs/editor/data-binding/overview; migration guide (RT-011); https://rive.app/docs/runtimes/web/rive-parameters (retrieved 2026-11-13). Type: primary. Confidence: paraphrase/quote.

**RT-013** Character rigging: bones form a skeleton (the first bone is the only one with X/Y position); elements are controlled by transforming, deforming a vector or deforming an image; "a vertex can be influenced by one or more bound bones, but its combined weights always equal 100%"; tools: Edit Weights, Smooth, Auto-Weights; raster images deform through a mesh. Docs advise parenting for rigid parts (hand, shoe) and weights for flexible ones …"control the properties of an object through another target object"). Follow-path/scroll constraints were not on the overview page.
Source: https://rive.app/docs/editor/manipulating-shapes/bones ; https://rive.app/docs/editor/constraints/constraints-overview (retrieved 2026-11-13). Type: primary. Confidence: quote/paraphrase.

**RT-014** Rive Scripting (Luau) exists: protocols listed are Node, Layout, Converter, Path Effect, Transition Conditions (custom transition conditions), Listener Actions, Blank, Test, File Format, Text File Format. The docs say nothing about deterministic time or seeded random. A search snippet calls scripting "early access" on the features page (page not opened). 2.50.0 notes mention scripts using `fetch()` (opt-in, threads build) and an unspecified "parallel-parts limit for scripts" in 2.49.0.
Source: https://rive.app/docs/scripting/protocols/overview.md (retrieved 2026-11-13); search-snippet for "early access" from https://rive.app/features; releases (RT-002). Type: primary / search-snippet. Confidence: paraphrase; "early access" low.

## C. Rive: runtime control from JS, and what "seek" means

**RT-015** High-level web `Rive` constructor options (RiveParameters, from `js/src/rive.ts`): `canvas`, `src` | `buffer` | `riveFile`, `artboard`, `stateMachine` (single name), `autoplay`, `layout`, `useOffscreenRenderer`, `autoBind`, `assetLoader`, `enableRiveAssetCDN` (default on), `onLoad`, `onPlay`, `onPause`, `onStop`, `onAdvance`. DEPRECATED in the source: `animations`, `stateMachines` (plural), `onLoop`, `onStateChange`, `automaticallyHandleEvents`.
Source: rive-wasm `js/src/rive.ts` via Context7 https://github.com/rive-app/rive-wasm/blob/master/js/src/rive.ts ; https://rive.app/docs/runtimes/web/rive-parameters (retrieved 2026-11-13). Type: primary. Confidence: source-read.

**RT-016** `Rive` playback methods: `play(names?)`, `pause(names?)`, `stop(names?)`, `reset(params?)` ("resets the artboard and state machine to the start or entry state"); pausing keeps position, stopping restarts from the entry state; `load()`, `cleanup()`, `cleanupInstances()`, `deleteRiveRenderer()` (only after `cleanup()`); `resizeDrawingSurfaceToCanvas()`.
Source: https://rive.app/docs/runtimes/web/rive-parameters and https://rive.app/docs/runtimes/web/state-machines.md (retrieved 2026-11-13). Type: primary. Confidence: quote/paraphrase.

**RT-017** There is NO `advance(dt)` on the high-level `Rive` class. It has `drawFrame()` ("advances and draws one frame", docs say you "typically don't need to call it manually", dt semantics not stated), `stopRendering()`/`startRendering()`, `drawingOptions` (`DrawOnChanged` default draws only when the artboard visually changes; `AlwaysDraw`) and an `onAdvance` callback with elapsed seconds. `scrub()` …"Use a state machine instead"). The high-level loop advances "once per frame by the time elapsed since the previous frame" (wall clock).
Source: https://rive.app/docs/runtimes/web/rive-parameters ; https://rive.app/docs/runtimes/web/state-machines.md (retrieved 2026-11-13). Type: primary. Confidence: quote/paraphrase.

**RT-018** Data-binding control from JS (high level): set `autoBind: true`, then in `onLoad` read `r.viewModelInstance`; `vmi.number("path").value = 10`, `vmi.boolean(...)`, `vmi.string(...)`, `vmi.color(...)` (0xAARRGGBB, plus `rgb/rgba/argb/opacity`), `vmi.enum(...)`, `vmi.trigger("name").trigger()`; nested properties by chaining or slash paths; observe with `property.on(cb)` / `off(cb?)`. Get view models by `viewModelByName/ByIndex/defaultViewModel()`; instances by `instance()` (blank), `defaultInstance()`, `instanceByIndex`, `instanceByName`; …"the changes will not apply to their bound elements until the state machine or artboard advances" (quote).
Source: https://rive.app/docs/runtimes/web/data-binding and rive-docs `runtimes/web/data-binding.mdx` via Context7 (retrieved 2026-11-13). Type: primary. Confidence: quote.

**RT-019** Legacy input API still works but is deprecated: `r.stateMachineInputs("name")` returns inputs with `name`, `type` (`StateMachineInputType.Number=56, Trigger=58, Boolean=59`), `value` (number/boolean, get/set) and `fire()` (trigger). Deprecated siblings: `setBooleanStateAtPath`, `setNumberStateAtPath`, `fireStateAtPath`, `get/setTextRunValue`.
Source: https://rive.app/docs/runtimes/web/inputs and `rive-parameters` (retrieved 2026-11-13). Type: primary. Confidence: quote.

**RT-020** The low-level API (`@rive-app/canvas-advanced`) lets you drive time yourself. `StateMachineInstance.advance(sec)` "Advances/scrubs the StateMachineInstance by the set amount of seconds. Note that this does not apply changes to the properties of objects in the Artboard yet"; `advanceAndApply(sec)` applies them. `Artboard.advance(sec)` "should be called after ... advance() of a LinearAnimationInstance or StateMachineInstance". Per-frame loop in the repo's own example: `renderer.clear()` -> `animation.advance(dt); animation.apply(1)` -> `artboard.advance(dt)` -> `renderer.save(); renderer.align(Fit, Alignment, frame, artboard.bounds); artboard.draw(renderer); renderer.restore()` -> `renderer.flush()` -> `rive.resolveAnimationFrame()`. Entry points: `load(buffer, assetLoader?, enableRiveAssetCDN?)` returns a File; `makeRenderer(canvas, useOffscreenRenderer?)`; `artboardByName(name)`; `artboard.stateMachineByName(name)`; `new StateMachineInstance(sm, artboard)`.
Source: `js/src/rive_advanced.mjs.d.ts` https://github.com/rive-app/rive-wasm/blob/master/js/src/rive_advanced.mjs.d.ts ; example https://github.com/rive-app/rive-wasm/blob/master/wasm/examples/out_of_band_example/index.ts (retrieved 2026-11-13). Type: primary. Confidence: source-read. (Which class declares `artboardByName` is not visible in the excerpt: verify before coding.)

**RT-021** More low-level members: `StateMachineInstance.inputCount()`, `input(i)` returning `SMIInput` (`value` get/set, `fire()`, `asBool/asNumber/asTrigger`); `reportedEventCount()` and `reportedEventAt(i)` ("events reported from the last advance call"); `bindViewModelInstance(instance)` on both Artboard and StateMachineInstance; `pointerDown/Move/Up(x, y, id)`. `SMIInput.name` was NOT in the extracted declaration excerpt. `LinearAnimationInstance` has `advance(sec)`, `apply(mix)` ("must be called after `advance()`"), `duration`, `workStart`, `workEnd` and a public `time: number` ("Number of seconds the animation has advanced by"); no `totalTime`, no `resetState`.
Source: same `.d.ts` as RT-020 (retrieved 2026-11-13). Type: primary. Confidence: source-read; the `time` field's write semantics are not documented (see Open Q1).

**RT-022** No documented way to seek a state machine to an absolute time. Searches of the web runtime docs, the C++ rendering-loop page and the Rive forum found no `seek`/`setTime` for state machines. The docs describe them as advancing once per frame by elapsed dt; the Unity docs say direct state access is limited and "state machines are indirectly controlled through transitions conditioned on Data Binding properties"; a Rive staffer's workaround for "jump to a state" was the Any state plus an input. Only `LinearAnimationInstance.time` (RT-021) hints at a timeline seek.
Source: https://rive.app/docs/runtimes/web/state-machines.md ; https://rive.app/docs/game-runtimes/unity/state-machines ; forum thread https://rive.app/community/forums/support/fsnLLkXUaA62/sports-captioning---clips-and-pics-jumping-to-set-end-point-in-runtime/ftmnJ0cSRm8L (retrieved 2026-11-13). Type: primary + community. Confidence: absence of evidence in several pages (not a proof).

**RT-023** Determinism statement (C++ runtime docs): "State machines and animations are deterministic at fixed `dt`s." Advice: wrap real elapsed time in an accumulator so playback is reproducible across frame rates; `advanceAndApply` "returns `true` if the state machine has more work; `false` if everything has settled"; "Pointer events and external view-model writes can wake the state machine back up". The page does not mention seeking. The web WASM is compiled from the same runtime layer (CONTRIBUTING: "WASM compiled from the underlying runtime layer"), so INFERENCE: the fixed-dt guarantee should carry to web, but no web page states it (RT-020, RT-021).
Source: https://rive.app/docs/runtimes/cpp/rendering-loop.md ; https://github.com/rive-app/rive-wasm/blob/master/CONTRIBUTING.md (retrieved 2026-11-13). Type: primary. Confidence: quote for C++; web carry-over INFERENCE.

**RT-024** Known limitation, unanswered: rive-wasm issue #402 (open, 2025-07-05): "State machine advancement only supports small increments?". A user driving `advanceAndApply` from Motion Canvas saw large `dt` jumps not advance the machine "as though there's a maximum dt"; their workaround was to keep each step under 0.1 s, splitting into 1/60 s steps. No Rive staff reply; the 0.1 s figure is the reporter's, not Rive's. Practical reading: step at 1/fps, never jump.
Source: https://github.com/rive-app/rive-wasm/issues/402 (retrieved 2026-11-13). Type: primary (issue tracker). Confidence: single-source (one report, unconfirmed by Rive).

**RT-025** Rive docs name Revideo and Remotion as the offline route: "For offline or server-side rendering, you can use external tools like Revideo and Remotion, both of which support Rive." The React "Rendering to a bitmap" page names no API, says bitmap rendering is "not supported directly in the React runtime", and lists snapshot tests and "rendering video from data-bound files" as use cases.
Source: https://rive.app/docs/runtimes/react/rendering-to-a-bitmap.md (retrieved 2026-11-13). Type: primary. Confidence: paraphrase with quote.

**RT-026** `@remotion/rive` (component `<RemotionRiveCanvas>`, added v3.3.75) is TIMELINE-ONLY and delta-driven. Source read: it imports `@rive-app/canvas-advanced`, loads wasm from `unpkg.com/@rive-app/canvas-advanced@2.31.5/rive.wasm`, builds a `LinearAnimationInstance`, and on every `useCurrentFrame()` change does `diff = frame - lastFrame.current; animation.advance(diff / fps); animation.apply(1); artboard.advance(diff / fps)`, then `resolveAnimationFrame()`. No `StateMachineInstance` anywhere. Props: `src`, `fit`, `alignment`, `artboard`/`animation` (name or index), `onLoad`, `assetLoader`, `enableRiveAssetCdn`, `effects`, crop props, plus inherited `<Sequence>` props. Docs: "synchronizes with Remotion's time"; state machine inputs are not mentioned. INFERENCE: it never sets absolute time, so a render tab that starts mid-video (parallel rendering) or a backward jump relies on one big or negative `advance`; fine for a linear timeline, not trustworthy for a state machine (RT-024).
Source: Remotion docs https://www.remotion.dev/docs/rive/remotionrivecanvas ; source https://raw.githubusercontent.com/remotion-dev/remotion/main/packages/rive/src/RemotionRiveCanvas.tsx (retrieved 2026-11-13). Type: primary. Confidence: source-read for the code; INFERENCE flagged.

**RT-027** Asset CDN: `enableRiveAssetCDN` defaults to enabled ("Allow the runtime to automatically load assets hosted in Rive's CDN"). INFERENCE (from this + HyperFrames' ban on render-time network fetches, RT-043): referenced fonts/images may be fetched at load, so pre-load with `assetLoader`/embedded assets for an offline, reproducible render.
Source: RiveParameters in `js/src/rive.ts` (RT-015). Type: primary. Confidence: source-read; INFERENCE on consequence.

## D. Rive as a directing palette

**RT-028** Production precedent: Duolingo drives lip sync with Rive. Each sound maps to a viseme; each character has its own set ("a set of 20+ mouths designed for everyone"); body poses and mouth shapes are SEPARATE animation states plugged into one State Machine, mouth states run at the same time as body states; …"much less than sending down a little movie"); idle behaviours such as blinking and head nods run alongside; the character stops on time if the learner finishes early.
Source: Duolingo blog, "world character visemes", https://blog.duolingo.com/world-character-visemes (retrieved 2026-11-13). Type: secondary (a Rive customer, describing production use). Confidence: quote/paraphrase, single-source.

**RT-029** There is no official Rive viseme standard. Community patterns: one Number input (`phoneme`, `viseme`, `viseme_id`) where each mouth state fires on its value; a mapping table translating a TTS vendor's viseme ids to the file's own values so the `.riv` is not tied to one vendor; or a continuous `mouthOpen` 0.0-1.0 driven by audio amplitude. Numbering schemes are each author's own.
Source: search over dev.to Rive articles and community threads (e.g. https://dev.to/uianimation/how-to-build-real-time-ai-lip-sync-using-rive-state-machine-viseme-data-26o7) (retrieved 2026-11-13). Type: community. Confidence: search-snippet; treat as pattern, not spec.

**RT-030** INFERENCE (from RT-007, RT-008, RT-010, RT-012, RT-028): a state machine built as an "acting palette" is a set of parallel layers, each a menu of poses the director can call by name or number: BODY (idle, react, nod, shrug), HEAD/EYES (a 1D blend driven by two numbers `lookX`/`lookY`, blink as a trigger or a Randomize-Exit loop), MOUTH (viseme states selected by a number), plus an Additive blend for mood (`mix by value/view model`). The director's script is then nothing but timestamped writes to view-model properties.

**RT-031** INFERENCE (from RT-018, RT-020, RT-023): Rive has no beat scheduler. A beat sheet becomes a list of `{t, property, value}` writes that the HOST applies between fixed-dt `advance` steps; the same list plus the same dt sequence replays the same animation. Setting a view-model value between steps takes effect on the next advance (RT-018).

**RT-032** INFERENCE (from RT-005, RT-013): a `.riv` is produced by the Rive editor; none of the pages read documents a programmatic way to author one. One rive-wasm issue reporter wrote their own `.riv` file writer (issue #426, closed; the bug was their ID counter for DataBindContext objects, not the runtime) which shows it can be done but is unsupported. So an AI agent directs a rig that a human (or a custom tool) built; it does not build the rig.
Source: https://github.com/rive-app/rive-wasm/issues/426 (retrieved 2026-11-13). Type: primary. Confidence: INFERENCE; the issue itself is paraphrase.

## E. Theatre.js

**RT-033** Versions and licences: `@theatre/core` 0.7.2 Apache-2.0 (depends on `@theatre/dataverse` 0.7.2); `@theatre/studio` 0.7.2 AGPL-3.0-only (peer `@theatre/core` `*`); `@theatre/r3f` 0.7.2 Apache-2.0 (peers: `react` >=17.0.2, `react-dom` >=17.0.2, `three` >=0.155.0, `@react-three/fiber` ^8.13.6, `@theatre/core` and `@theatre/studio` `*`). README: "Theatre's core (`@theatre/core`) is released under the Apache License"; studio is AGPL 3.0; "You only use the studio during design/development"; "Your project's final bundle only includes `@theatre/core`, so only the Apache License applies". The README does not discuss commercial use directly.
Source: npm registry https://registry.npmjs.org/@theatre/core/latest (also /studio, /r3f); README https://raw.githubusercontent.com/theatre-js/theatre/main/README.md (retrieved 2026-11-13). Type: primary. Confidence: registry + quote. (The repo's `packages/r3f/package.json` on `main` says 0.7.0; npm says 0.7.2.)

**RT-034** Maintenance risk: `@theatre/core` 0.7.2 was published 2024-05-19; 0.7.1 on 2024-04-11; no 1.0 on npm as of 2026-11-13 (dist-tag `latest` = 0.7.2). The newest commit on the public default branch is 2024-04-11 ("Add the 1.0 notice"). The README says "Theatre.js 1.0 is around the corner. We have _temporarily_ moved development to a private repo ... We'll push our work back to this public repo …". Public PRs still open in 2025-2026 (#521, #525, #526) and an issue author called the repo not "updated in years" (issue #506, a user's claim). Treat Theatre as stable-but-frozen: pin 0.7.2, expect no fixes.
Source: https://registry.npmjs.org/@theatre/core (time field); https://api.github.com/repos/theatre-js/theatre/commits ; README ; https://github.com/theatre-js/theatre/issues/506 (retrieved 2026-11-13). Type: primary. Confidence: registry/quote; "not updated in years" is a single user's claim.

**RT-035** Object model: `getProject(id, {state?})` returns (or re-returns) a project; `project.sheet(name, instanceId?)`; `sheet.object(key, props)` where props have a type and initial value (types: `compound`, `number`, `rgba`, `boolean`, `string`, `stringLiteral`, `image`, `file`); `sheet.sequence` is the sheet's single sequence. `obj.value` holds current prop values; `obj.onValuesChange(cb)` returns an unsubscribe fn; `sheet.object(key, props, {reconfigure: true})` updates in place; detaching keeps stored prop values. `project.ready` (Promise) and `project.isReady`: without Studio the project is already ready.
Source: https://www.theatrejs.com/docs/latest/api/core ; https://www.theatrejs.com/docs/latest/manual/objects ; https://www.theatrejs.com/docs/latest/manual/projects (retrieved 2026-11-13). Type: primary. Confidence: quote/paraphrase.

**RT-036** `sequence.play(opts?)` accepts `iterationCount`, `range` `[start,end]`, `rate`, `direction` (`normal|reverse|alternate|alternateReverse`) and `rafDriver` (since 0.6.0); it returns a Promise that resolves `true` on completion and `false` if interrupted. In dev builds it throws for an invalid range (start >= length, end <= start), non-positive-integer `iterationCount`, `rate` <= 0 (use `direction: 'reverse'` instead); an end beyond the length only warns and is clamped. `sequence.pause()`, `sequence.position` (read/write seconds) and `sequence.pointer` (a Pointer to `length`, `position`, `playing`, for `onChange`/`val`) complete the playback API.
Source: https://www.theatrejs.com/docs/latest/api/core ; `packages/core/src/sequences/Sequence.ts` (via Context7 and raw fetch) (retrieved 2026-11-13). Type: primary. Confidence: quote + source-read.

**RT-037** Seeking: the `position` setter "pauses playback and calls `gotoPosition()`": it pauses, clamps to `[0, length]` and writes the position synchronously into the playback state (`this._state.setByPointer(p => p.position, time)`); nothing is deferred to a tick. Dev builds log an error and reset a negative or non-number to 0.
Source: `packages/core/src/sequences/Sequence.ts` and `playbackControllers/DefaultPlaybackController.ts`, https://github.com/theatre-js/theatre (retrieved 2026-11-13). Type: primary. Confidence: source-read.

**RT-038** Evaluation is pull-based and synchronous: `sheetObject.value` returns `der.getValue()` (a derivation); keyframe interpolation is evaluated against the sequence's position prism (`interpolationTripleAtPosition`), so after `sequence.position = t` a read of `obj.value` gives the interpolated values at `t`. Reads keep the derivation hot for `KEEP_HOT_FOR_MS` = 5000 ms. By contrast `onValuesChange(cb, rafDriver?)` is push-based through `onChange` and the ticker, so its callback fires on a tick, not inside the setter. INFERENCE: for a frame loop, set position then read `obj.value` yourself; do not rely on `onValuesChange` timing.
Source: `packages/core/src/sheetObjects/TheatreSheetObject.ts` and `SheetObject.ts` (retrieved 2026-11-13). Type: primary. Confidence: source-read; the INFERENCE is mine.

**RT-039** Interpolation: keyframes have `{id, value, position, handles:[leftX,leftY,rightX,rightY], connectedRight, type?: 'bezier'|'hold'}`; absent `type` means bezier; a `hold` keyframe (or `connectedRight: false`) keeps the left value until the next keyframe (progression 0 via `Math.floor`). Bezier uses the handles of left (handles[2],[3]) and right (handles[0],[1]) keyframes.
Source: `packages/core/src/types/public.ts` and `sequences/interpolationTripleAtPosition.ts` (Context7) (retrieved 2026-11-13). Type: primary. Confidence: source-read.

**RT-040** Time source and manual ticking: `DefaultPlaybackController.play` reads `ticker.time` and computes elapsed time from the ticker's `currentTickerTime` (it does not call `performance.now()` itself). `createRafDriver({name?, start?, stop?})` from `@theatre/core` returns a driver with `tick(time)`; the manual says to "manually tick forward (many ticks per frame, or skipping many frames, etc)" for "recording, rendering to a file, testing, and benchmarking", e.g. `rafDriver.tick(performance.now())` inside `setInterval`, then pass the driver to `onChange(...)` (3rd arg) or `sheet.sequence.play({rafDriver})`; `start()`/`stop()` are called when computations are scheduled / idle; `@theatre/r3f` accepts a driver via `<RafDriverProvider>`; Studio via the experimental `__experimental_rafDriver`. The manual has no video-render example.
Source: https://www.theatrejs.com/docs/latest/manual/advanced ; `packages/core/src/rafDrivers.ts` ; DefaultPlaybackController (retrieved 2026-11-13). Type: primary. Confidence: quote + source-read.

**RT-041** State JSON: authored in Studio, exported ("Export ... to JSON" on the project in the outline panel, or `studio.createContentOfSaveFile(projectId)`), loaded with `getProject('id', {state})`. Inside, per-object tracks live under `sheetsById[sheetId].sequence.tracksByObject[objectKey].trackData[trackId]` and hold keyframes (RT-039). The docs describe the export/import flow but do not publish a schema or promise stability. INFERENCE: hand-writing this JSON is possible but unsupported.
Source: https://www.theatrejs.com/docs/latest/manual/projects ; https://www.theatrejs.com/docs/latest/api/studio ; `SheetObject.ts` `_trackIdToPrism` (retrieved 2026-11-13). Type: primary. Confidence: quote for the flow; schema = source-read; "unsupported" is INFERENCE.

**RT-042** No documented public API for adding keyframes from code. Issue #506 (closed 2026-01-23) says "There is no API for adding keyframes" and proposes `sheet.setKeyframe(...)`/`addKeyframe(...)` as a TODO (no maintainer reply on the page). What exists: `studio.transaction(({set, unset}) => ...)`: "If the prop is sequenced, the value will be a keyframe at the current sequence position." A PR adding `__experimental_sequenceProp` to `studio.transaction()` (#449) is, per a maintainer comment, "merged via 74b68c8" (the search tool had it as not merged; the comment is the better evidence). It is not in the public Studio docs, and it needs `@theatre/studio` (AGPL) running in the session.
Source: https://github.com/theatre-js/theatre/issues/506 ; https://github.com/theatre-js/theatre/pull/449 ; https://www.theatrejs.com/docs/latest/api/studio (retrieved 2026-11-13). Type: primary. Confidence: quote; the experimental flag's call signature is NOT confirmed.

**RT-043** Production recipe (docs): export `state.json`; pass it as `state` to `getProject`; "don't import Studio for your production builds" (for `@theatre/browser-bundles` swap `core-and-studio.js` for `core-only.min.js`); remove every `studio.initialize()`; start playback after `project.ready.then(...)`, e.g. `sheet.sequence.play({iterationCount: Infinity, range: [0, 6]})`. `studio.initialize()` is called once and later calls are ignored; `studio.ui.hide()`/`restore()`/`isHidden` exist.
Source: https://www.theatrejs.com/docs/latest/getting-started/with-html-svg ("Getting ready for production"); https://www.theatrejs.com/docs/latest/api/studio (retrieved 2026-11-13). Type: primary. Confidence: quote.

**RT-044** `@theatre/r3f` direction surface: wrap the scene in `<SheetProvider sheet={getProject(..).sheet(..)}>`; make objects editable with `editable as e` and a unique `theatreKey` ("All editable elements need to have a unique `theatreKey` prop under their `SheetProvider`"); use `PerspectiveCamera` from `@theatre/r3f` with `makeDefault`, `position`, `fov` and `lookAt` (an Object3D or ref) to make the camera editable and sequenceable; in Studio call `studio.extend(extension)` with `import extension from '@theatre/r3f/dist/extension'`. Camera direction = camera object keyframes (position/rotation/fov/lookAt target).
Source: https://www.theatrejs.com/docs/latest/getting-started/with-react-three-fiber ; https://www.theatrejs.com/docs/latest/api/r3f (retrieved 2026-11-13). Type: primary. Confidence: quote.

**RT-045** r3f version trap: `@theatre/r3f` 0.7.2 peers `@react-three/fiber` ^8.13.6 (React 18 line). R3F's own docs pair `fiber@8` with React 18 and `fiber@9` with React 19. INFERENCE: a React 19 / fiber 9 project falls outside Theatre's declared peer range; expect peer-dependency conflicts. Open issues: #446 (`der.onStale is not a function` with Next.js + R3F), #429 (`<PerspectiveCamera/>` type error needing `attachArray/attachObject/attachFns`), #98 (`objRef` initially null), #451 (drei `PositionalAudio` context error), #347 (`PerspectiveCamera` export confusion).
Source: npm `@theatre/r3f` registry JSON; https://r3f.docs.pmnd.rs/tutorials/v9-migration-guide (search-snippet for the pairing); issues https://github.com/theatre-js/theatre/issues/446, /429, /98, /451, /347 (retrieved 2026-11-13). Type: primary + search-snippet. Confidence: registry for peers; pairing = search-snippet; consequence = INFERENCE.

**RT-046** Other open issues worth knowing: #424 a custom `rafDriver` passed to `studio.initialize` breaks spacebar play/pause; #485 asks for a default rafDriver per sheet/project (today it must be passed to every `onValuesChange`); #503 `import studio` crashes a Next.js dev build (`e.charCodeAt is not a function`); #526/#525 (open PRs) add a warning when Studio is imported but not initialised; #466/#477 animation stops in WebXR/Quest immersive mode; #60 reported FPS lower with Studio closed (Theatre 0.4.7, unexplained); #495 `attachAudio` allows one audio file.
Source: https://github.com/theatre-js/theatre/issues/424, /485, /503, /526, /525, /466, /477, /60, /495 (retrieved 2026-11-13). Type: primary. Confidence: paraphrase (issue lists via GitHub search API; bodies not all read).

**RT-047** `sequence.attachAudio(opts)` returns a Promise resolving after the audio is loaded and decoded. `DefaultPlaybackController` has no audio code and no media clock, so audio does not appear to drive Theatre's time there (audio sync lives elsewhere; not read). Multiple audio tracks are not supported (issue #495).
Source: https://www.theatrejs.com/docs/latest/api/core ; DefaultPlaybackController; https://github.com/theatre-js/theatre/issues/495 (retrieved 2026-11-13). Type: primary. Confidence: paraphrase; audio/time coupling = not confirmed.

## F. Integration with frame-accurate renderers

**RT-048** HyperFrames contract: the renderer "pauses your animation and *seeks* it ... before capturing each frame"; the paused timeline is registered on `window.__timelines["<root data-composition-id>"]`; a missing registration gives "a still frame with no motion". "GSAP, Web Animations, Lottie, and other browser runtimes render deterministically" and "usually drop in close to as-is". Contrast: in Remotion "the component is a function of the current frame number".
Source: HyperFrames guide, https://hyperframes.heygen.com/guides/hyperframes-vs-remotion (retrieved 2026-11-13). Type: primary (vendor docs). Confidence: quote.

**RT-049** HyperFrames determinism rules: every frame must be reproducible from its time value alone ("same input time -> same pixels"). Banned for visual state: `Date.now()`, `performance.now()`, any render-time clock, unseeded `Math.random()`, render-time network fetches, hover/scroll/pointer/focus state, unbounded infinite loops. Do not call `tl.play()` for render-critical motion; GSAP timelines must be built `paused: true` and registered only after the build finishes.
Source: installed skill file `hyperframes-core/references/determinism-rules.md` (plugin marketplace copy under `~/.claude/plugins/marketplaces/hyperframes/skills/`), retrieved 2026-11-13. Type: primary (tool's own skill docs). Confidence: quote/paraphrase (local file read, version not stamped in the file).

**RT-050** Built-in HyperFrames runtimes: GSAP, CSS, Anime.js, Lottie, Three.js, Web Animations, TypeGPU. Neither the installed skill set (`grep -w rive|theatre` returned no hit) nor the guides mention Rive or Theatre.js, so there is NO built-in adapter for either. Lottie: players are pushed on `window.__hfLottie` and seeked with `goToAndStop(timeMs, false)`. Three.js: the adapter sets `window.__hfThreeTime` and dispatches `hf-seek` with `{detail:{time}}`; render exactly that time; set `data-duration` (no duration auto-inference). TypeGPU: `hf-seek` carries `{time, waitUntil}`, may re-dispatch the same time while paused ("re-render that exact time; do not advance simulation state").
Source: installed skill files `hyperframes-animation/adapters/{lottie,three,typegpu}.md`; https://hyperframes.heygen.com/concepts/frame-adapters (retrieved 2026-11-13). Type: primary. Confidence: quote/paraphrase.

**RT-051** HyperFrames `FrameAdapter` interface (experimental v0, "may change before v1"): `id`, `init?(context)` (composition id, fps, dimensions, root), `getDurationFrames()`, `seekFrame(frame)`, `destroy?()`. Contract: finite non-negative frame count; "Support forward, backward, and random seeks"; "Return the same state when the same frame is requested again"; no wall-clock timers or unseeded randomness; "Finish async work before the frame is captured". "The host owns capture and encoding. The adapter owns only animation state." How to register a custom adapter is not documented on that page.
Source: https://hyperframes.heygen.com/concepts/frame-adapters (retrieved 2026-11-13). Type: primary. Confidence: quote; registration not documented.

**RT-052** The documented HyperFrames pattern for libraries without an adapter is to put everything on ONE paused GSAP timeline and call the library from a proxy tween's `onUpdate`: e.g. `tl.to(proxy, {value: 1, duration: 2, onUpdate: render}, 0.5)` (TypeGPU doc), "Drive from GSAP timeline - capture + render every frame" (html-in-canvas doc), camera journeys via an `onUpdate: applyCamera`. The camera-journey blueprint warns: never `getBoundingClientRect` in `onUpdate` ("desyncs under parallel frame sampling"), and the gsap doc says render mode "seeks frame-by-frame"with no input events. INFERENCE: frames may be sampled out of order or in parallel, so a render function must be a pure function of …"advance one step".
Source: installed skill files `hyperframes-animation/adapters/typegpu.md`, `html-in-canvas-patterns.md`, `rules/3d-camera-flight.md`, `blueprints/camera-journey.md`, `adapters/gsap-transforms-and-perf.md` (retrieved 2026-11-13). Type: primary. Confidence: paraphrase; out-of-order sampling is INFERENCE from the "parallel frame sampling" wording.

**RT-053** Remotion contract: "Remotion renders each frame independently", so render order is not sequential; "CSS animations don't know which frame Remotion is currently rendering, the animation state will be wrong" (same for `transition`, `@keyframes`, `setTimeout`); the fix is to read `useCurrentFrame()` and compute styles from it ("the animation state is derived from the frame number and is deterministic"). `useCurrentFrame()` is 0-indexed and inside a `<Sequence>`/timed parent returns the frame relative to the parent's start (pass the absolute frame down as a prop if needed).
Source: https://www.remotion.dev/docs/troubleshooting/css-animations ; https://www.remotion.dev/docs/use-current-frame (retrieved 2026-11-13). Type: primary. Confidence: quote.

**RT-054** No Remotion-Theatre or HyperFrames-Theatre or -Rive integration was found in docs or search. For Remotion the Rive path is `@remotion/rive` (RT-026). For Theatre: INFERENCE (from RT-037, RT-038, RT-053): in a frame-driven renderer, set `sheet.sequence.position = frame / fps` and read `obj.value`; Theatre's synchronous seek and pull evaluation make it seek-safe without any rafDriver. Not proven by any source in this lane.

## G. Comparison with GSAP and Lottie for directed shot work

**RT-055** GSAP 3.15.1 uses a "Standard 'no charge' license"(gsap.com/standard-license). The FAQ states commercial use is covered at no charge including plugins formerly members-only (SplitText, MorphSVG), and that AI-generated GSAP code is not a …"Competitive Products"); reverse engineering to build such a product. The text does not address video-rendering pipelines or SaaS explicitly.
Source: https://gsap.com/standard-license/ ; https://registry.npmjs.org/gsap/latest ; https://gsap.com/blog/3-13/ (search-snippet: "100% FREE including ALL of the bonus plugins") (retrieved 2026-11-13). Type: primary. Confidence: paraphrase; not legal advice.

**RT-056** Lottie: `@lottiefiles/dotlottie-web` 0.83.2 is MIT. `.lottie` files can carry state machines (JSON in the `s/` directory: initial state, states, interactions) fed inputs/events at runtime. A third-party skill page says `setFrame()` renders synchronously after `autoplay: false`, and that the older lottie-web equivalent is `goToAndStop(N, true)`; HyperFrames uses `goToAndStop(timeMs, false)` (RT-050). Lottie JSON is exported from After Effects (or similar), so an agent also cannot author a character rig there.
Source: https://registry.npmjs.org/@lottiefiles/dotlottie-web/latest ; https://docs.lottiefiles.com/en/format/dotlottie/interactivity/state-machines.md (search-snippet); https://skills.cat/skills/lottiefiles/dotlottie-web (secondary, search-snippet) (retrieved 2026-11-13). Type: primary (registry) + secondary. Confidence: registry for version/licence; the rest search-snippet.

**RT-057** Seek-safety matrix (INFERENCE built from RT-020-RT-024, RT-037, RT-038, RT-048-RT-051, RT-056):

| Library | Random seek to time t | Agent can author the asset in code | Built-in HyperFrames adapter | Remotion wrapper |
|---|---|---|---|---|
| GSAP (paused timeline) | Yes, native | Yes (it is code) | Yes (primary) | not needed (compute from frame) |
| Lottie | Yes (`goToAndStop` / `setFrame`) | No (AE/editor export) | Yes | `@remotion/lottie` (not read here) |
| Theatre.js core | Yes (`position` setter + `obj.value`) | Partly: state JSON from Studio; no keyframe-add API | No | none found |
| Rive timeline animation | Probably (`LinearAnimationInstance.time` declared; unproven) | No (editor-authored `.riv`) | No | Yes, `<RemotionRiveCanvas>` (delta advance) |
| Rive state machine | No seek API: replay from 0 with fixed dt | No | No | No (timeline only) |

## H. Pitfalls and lifecycle bugs

**RT-058** Memory/lifecycle issues in rive-wasm: #368 (open) `cleanup` is typed in the `.d.ts` but missing at runtime for WebGL renderers in the low-level API, so calling it fails and leaks; #318 (open) cleanup logs a console error and `eventCleanup` avoids it but leaks; #391 (open) high idle memory; #428 (open PR) explicit image `unref()` released late via FinalizationRegistry causing `deleteTexture` errors after cleanup. Closed earlier leaks (#281 Mat2D, #270 Alignment) show the pattern. For one-instance-per-shot replay (RT-031) dispose old instances and prefer the high-level `cleanup()` / `deleteRiveRenderer()` order (RT-016).
Source: https://github.com/rive-app/rive-wasm/issues/368, /318, /391, pull/428, pull/281, pull/270 (retrieved 2026-11-13). Type: primary. Confidence: paraphrase (issue lists via GitHub search API).

**RT-059** Browser-specific fixes in the 2.49.x line: Safari 26.2 to 26.3.1 gets the non-threaded build "because of a known threading bug" (2.49.2); a blank frame during resizes in Safari fixed (2.49.4); zero-size canvas fixes (2.49.1); "the replay worker paces frames more evenly" (2.49.2). INFERENCE: `webgl2-threads` renders on a worker with its own pacing, so do not use it for synchronous per-frame capture; use `canvas` / `webgl2` / `canvas-advanced` on the main thread and size the canvas before the first draw.
Source: GitHub Releases API (RT-002) (retrieved 2026-11-13). Type: primary. Confidence: registry for the notes; INFERENCE flagged.

**RT-060** Rive state machines can "settle": `advanceAndApply` returns false when nothing is left to do, and `DrawOnChanged` (the default `drawingOptions`) draws only when the artboard visually changes. A capture loop that stops drawing when it sees `false`, or that leaves `DrawOnChanged` on, can emit stale or missing frames; set `AlwaysDraw` or draw every frame regardless of the return value. (The settle text is from the web state-machines page and the C++ page; the capture consequence is INFERENCE.)
Source: https://rive.app/docs/runtimes/web/state-machines.md ; https://rive.app/docs/runtimes/web/rive-parameters ; RT-023 (retrieved 2026-11-13). Type: primary. Confidence: quote + INFERENCE.

**RT-061** Third-party "Rive to MP4" converters exist (e.g. Animation Machine): they wrap the `.riv` in an HTML page and screen-capture it; the vendor says auto-advancing machines render correctly while input-driven ones stay in their default state, at USD 5/month. Vendor claim, not a Rive statement; it corroborates RT-022 (inputs must be scripted by the host).
Source: https://animation-machine.pages.dev/rive-to-mp4 (search-snippet; page not opened) (retrieved 2026-11-13). Type: secondary (vendor). Confidence: vendor, search-snippet.

**RT-062** Theatre in production: the manual's "Getting ready for production" is the only documented path; Studio imports left in the bundle will pull in AGPL code (RT-033) and may log the "imported but not initialised" warning (PRs #525/#526). Avoid `@theatre/browser-bundles`' `core-and-studio` file in anything shipped.
Source: RT-033, RT-043, https://github.com/theatre-js/theatre/pull/526 (retrieved 2026-11-13). Type: primary. Confidence: paraphrase; the AGPL consequence is the README's own statement.

---

## Rules for the skill (imperative; each cites its entries)

1. Treat Rive and Theatre as editor-authored assets the agent DIRECTS, not authors: the director's deliverable is a shot list of timestamped property writes (Rive) or a sequence range/position per shot (Theatre), plus a request for the missing rig/keyframes to a human. (RT-032, RT-041, RT-042)
2. Pin versions in every brief and report: Rive `@rive-app/canvas` / `canvas-advanced` 2.50.0, Theatre 0.7.2, GSAP 3.15.1. Re-check Rive per release; it ships almost daily. (RT-001, RT-002, RT-034)
3. For Rive, design state machines as parallel layers (body, head/eyes, mouth, mood) driven by data-binding view-model properties, not by legacy inputs or events. Ask for "Convert Inputs to View Models" on older files. (RT-007, RT-008, RT-011, RT-012, RT-030)
4. Drive Rive with a fixed time step: `advance(1/fps)` every frame, never a variable or large dt; apply scheduled property writes between steps; set a view-model value, then advance, then draw. (RT-018, RT-020, RT-023, RT-024, RT-031)
5. Never assume a Rive state machine can be seeked. To render frame N: build a fresh instance, replay the same input schedule with the same dt from 0, or cache checkpoints by re-instancing; or pre-render the Rive shot once to a video/PNG sequence and treat it as a media clip. (RT-022, RT-023, RT-051, RT-057)
6. Use the high-level `Rive` class only for preview. For render use `@rive-app/canvas-advanced` (own loop, own clock); the high-level loop is wall-clock driven and has no `advance`. (RT-017, RT-020)
7. Keep drawing every frame, even after `advanceAndApply` returns false; set `drawingOptions` to `AlwaysDraw` on the high-level class. Do not capture with `webgl2-threads`. (RT-059, RT-060)
8. Do not use `@remotion/rive` for state machines or inputs: it is timeline-only and delta-driven. Give it single timeline animations; for characters use a pre-render or a custom canvas-advanced component. (RT-026, RT-057)
9. Do not fetch at render time: load the `.riv` and its assets through `buffer`/`assetLoader` before the first frame; turn off or pre-satisfy the Rive asset CDN. (RT-015, RT-027, RT-049)
10. For Rive lip sync, build the phoneme/viseme timing first (from the TTS or alignment data), map vendor visemes through a lookup table to the file's own mouth numbers, and write them as timed `mouth` property changes; keep blink and look on separate layers. (RT-028, RT-029, RT-030)
11. For Theatre, load state from JSON with `getProject(id, {state})`, import only `@theatre/core` in the render page, and never ship `@theatre/studio`. (RT-033, RT-043, RT-062)
12. Seek Theatre with `sheet.sequence.position = t` (synchronous), then read `obj.value`; do not use `sequence.play` or `onValuesChange` for rendering. If a loop needs ticks, use a `createRafDriver` driver and call `tick()` yourself. (RT-036, RT-037, RT-038, RT-040)
13. Always wait for `project.ready` before the first seek; remember the `position` setter clamps to `[0, length]` and pauses playback, so a shot longer than the sequence silently freezes on its last value. (RT-035, RT-037)
14. Direct 3D camera moves with `@theatre/r3f` `PerspectiveCamera` keyframes (position, fov, `lookAt`) only on `@react-three/fiber` 8.x / React 18; for fiber 9 / React 19, drive a plain Three.js camera from `@theatre/core` object values instead. (RT-044, RT-045, RT-054)
15. In HyperFrames, wire non-adapter libraries through one paused GSAP timeline plus a proxy tween whose `onUpdate` calls `renderAt(proxy.t)`; `renderAt` must be a pure function of `t` (no wall clock, no hidden state advance, no layout reads). (RT-049, RT-052)
16. In Remotion, compute everything from `useCurrentFrame()` / `fps`; no CSS transitions, timers or library autoplay. (RT-053)
17. Do not hand-write Theatre `state.json` unless a Studio-made state exists to diff against; the schema is undocumented. If keyframes must be added in code, run Studio in a session and use `studio.transaction` and treat `__experimental_sequenceProp` as unconfirmed. (RT-041, RT-042)
18. Licence gate before any release: Rive runtime MIT but Free-plan exports show a splash screen; Theatre core Apache-2.0 / studio AGPL (do not bundle studio); GSAP standard licence (not for competing visual animation builders; video pipelines not addressed). (RT-003, RT-033, RT-055)
19. State maintenance risk in the brief when choosing Theatre: no public commits since 2024-04-11, no 1.0. Prefer GSAP (pure code, seek-native, HyperFrames-native) when the shot does not need a visual timeline editor. (RT-034, RT-057)
20. Report every unverified claim (a Rive timeline `time` seek, a Remotion Theatre seek) as UNTESTED in the shot report rather than as a result. (Open Q1, Q4)

---

## Code sketches (sketches built from the cited API; NOT run, NOT verified)

All three assume a `shots` list like:

```js
// beat sheet -> shot list. Times in seconds. One entry per shot.
const FPS = 30;
const shots = [
  { id: "s1", t0: 0.0, t1: 2.4, rive: [ // Rive: timestamped property writes
      { t: 0.0, prop: "mood",  value: 0 },
      { t: 0.6, prop: "viseme", value: 3 }, { t: 0.8, prop: "viseme", value: 1 },
      { t: 1.4, prop: "look",  value: 0.7 } ],
    theatre: { range: [0, 2.4] } },       // Theatre: sequence range for the shot
];
```

### Sketch 1: Rive, seek-safe by deterministic replay (canvas-advanced)

Built from RT-018, RT-020, RT-021, RT-023, RT-024. Items marked `VERIFY` are not confirmed by the extracted docs.

```js
import RiveCanvas from "@rive-app/canvas-advanced";            // 2.50.0 (RT-001)

const rive = await RiveCanvas({ locateFile: () => "/vendor/rive.wasm" });   // VERIFY: wasm hosting option
const file = await rive.load(new Uint8Array(await (await fetch("/assets/hero.riv")).arrayBuffer())); // before render (RT-049)
const renderer = rive.makeRenderer(canvas);                    // RT-020

const DT = 1 / FPS;                    // fixed step only (RT-023, RT-024)
let artboard, sm, cursor = -1, writes = [];

function rebuild() {                    // new instance = frame 0 (RT-022: no seek)
  artboard?.delete?.(); sm?.delete?.();                         // VERIFY delete()/cleanup (RT-058)
  artboard = file.artboardByName("Hero");                       // VERIFY owning class (RT-020)
  sm = new rive.StateMachineInstance(artboard.stateMachineByName("Acting"), artboard);
  // data-binding variant (RT-012): create/bind a view model instance and write properties by name;
  // the low-level instance-creation call is VERIFY. Legacy-input variant:
  //   for (let i = 0; i < sm.inputCount(); i++) { const inp = sm.input(i); /* inp.name is VERIFY */ }
  cursor = -1; writes = [...shots.flatMap(s => s.rive.map(w => ({ ...w, t: s.t0 + w.t })))]
                         .sort((a, b) => a.t - b.t);
}

function renderAt(t) {                  // PURE function of t (RT-052)
  const frame = Math.round(t * FPS);
  if (frame <= cursor) rebuild();       // backward or repeated seek: replay from 0
  while (cursor < frame) {
    cursor++;
    const now = cursor * DT;
    for (const w of writes) if (w.t <= now && !w.done) { setProp(w.prop, w.value); w.done = true; }
    sm.advanceAndApply(DT);             // RT-020: apply, then draw
  }
  renderer.clear();
  artboard.advance(0);                  // VERIFY: needed after advanceAndApply (RT-020 says advance after SM advance)
  renderer.save();
  renderer.align(rive.Fit.contain, rive.Alignment.center,
    { minX: 0, minY: 0, maxX: canvas.width, maxY: canvas.height }, artboard.bounds);
  artboard.draw(renderer);
  renderer.restore();
  renderer.flush();
  rive.resolveAnimationFrame();         // RT-020: flush queued draws; always draw (RT-060)
}
```

HyperFrames hookup (RT-052): `tl.to(proxy, { t: DURATION, duration: DURATION, ease: "none", onUpdate: () => renderAt(proxy.t) }, 0); window.__timelines["root"] = tl;` with `tl = gsap.timeline({ paused: true })`. Replay cost is O(frame) per out-of-order seek: for long shots pre-render to media instead (Rule 5).

### Sketch 2: Theatre.js core, seek-safe (HyperFrames or any frame loop)

Built from RT-035, RT-037, RT-038, RT-043, RT-052, RT-054.

```js
import { getProject, types } from "@theatre/core";           // core only, no studio (RT-033, RT-043)
import state from "./hero.theatre-state.json";               // exported from Studio (RT-041)

const project = getProject("Hero", { state });
const sheet = project.sheet("Shots");
const cam = sheet.object("Camera", {
  position: types.compound({ x: types.number(0), y: types.number(0), z: types.number(6) }),
  fov: types.number(35),
});
await project.ready;                                          // RT-035 (already resolved without Studio)

function renderAt(t) {                                        // PURE function of t
  const tt = Math.max(t, 0);                                  // setter already clamps to [0, length] (RT-037);
                                                              // public `sequence.length` is VERIFY (docs only show `sequence.pointer.length`)
  sheet.sequence.position = tt;                               // synchronous seek, pauses (RT-037)
  const v = cam.value;                                        // pull read (RT-038)
  threeCamera.position.set(v.position.x, v.position.y, v.position.z);
  threeCamera.fov = v.fov; threeCamera.updateProjectionMatrix();
  threeRenderer.render(scene, threeCamera);                   // render on demand, no rAF loop
}
// shot i: renderAt(shots[i].theatre.range[0] + (t - shots[i].t0))
```

Remotion variant (INFERENCE, no source integrates them): inside a component, `const frame = useCurrentFrame(); const { fps } = useVideoConfig();` then call `renderAt(frame / fps)` in `useLayoutEffect` keyed on `frame`; hold the first render until `project.ready` (Remotion's `delayRender` was not verified in this lane). Realtime preview, not render, is the only place to use `sheet.sequence.play({ range, rate })`.

### Sketch 3: GSAP/Lottie seek (for comparison; the HyperFrames-native route)

Built from RT-049, RT-050. `const tl = gsap.timeline({ paused: true });` build shot tweens at their `t0`; `window.__timelines["root"] = tl` after the build. Lottie: `lottie.loadAnimation({ container, renderer: "svg", loop: false, autoplay: false, path })` then `window.__hfLottie.push(anim)`.

---

## Open questions / not confirmed

1. **Rive `LinearAnimationInstance.time` as a seek.** The `.d.ts` declares a public `time` field ("Number of seconds the animation has advanced by"), and an old rive-js source had a setter, but no current doc says that assigning it (then `apply(1)`, `artboard.advance(0)`) renders that timestamp. Needs a one-off test before Rule 5's timeline-only shortcut is trusted.
2. **Does the web WASM honour "deterministic at fixed dt" bit-for-bit?** Only the C++ page says it (RT-023). Random/time-dependent behaviours in scripts, randomised exits ("Randomize Exit") and `Date`-like inputs are undocumented for seeding. Whether `Randomize Exit` uses a seedable RNG is unknown.
3. **Large-dt behaviour (issue #402).** Confirmed only as one user's report; Rive has not replied. The true limit, if any, is unknown. Rule 4 (1/fps steps) avoids it.
4. **Theatre + Remotion / HyperFrames integration** is untested and undocumented anywhere found; the sketches are INFERENCE. A rafDriver may be unnecessary for pull-reads, but R3F's `editable` components subscribe through `onValuesChange`; whether they update synchronously under a manual `tick` is not documented.
5. **Programmatic keyframes in Theatre.** `__experimental_sequenceProp`'s signature, current availability in 0.7.2 and whether `studio.transaction` works headlessly are unconfirmed; there is no documented headless way to author state. The state JSON schema stability is unpromised.
6. **Rive free-plan splash screen.** Docs say "Free exports play a Rive splash screen". Whether it renders in a user's own web runtime playback of a free-plan `.riv`, or only in editor-cloud exports, is not stated. Check before any client delivery.
7. **Rive Cloud Renderer, State Machine mode inputs.** It "renders a State Machine as it plays over time"; how inputs/data bindings are scripted for that render is undocumented. A vendor says input-driven machines stay in default state (RT-061, vendor).
8. **Low-level API gaps:** `SMIInput.name`, the class that owns `artboardByName`, how to create a `ViewModelInstance` and bind it in `canvas-advanced`, and the correct cleanup call for WebGL renderers (#368) were not visible in the extracted excerpts. Read the full `.d.ts` before coding.
9. **Rive Scripting maturity and determinism** (early-access label is a search snippet; no seeded-random or time-source documentation).
10. **Theatre audio coupling:** whether `attachAudio` ever drives or corrects sequence position (the DefaultPlaybackController read shows no audio code) is not confirmed; multi-track audio is unsupported (#495).
11. **`stringLiteral` sequencing in Theatre** (useful for discrete poses): issue #18 (closed) requested it; current support not verified. `hold` keyframes (RT-039) cover stepped numbers.
12. **HyperFrames custom adapter registration** (how to register a `FrameAdapter` for Rive/Theatre) is not documented on the concept page; the proxy-tween route (RT-052) is the only documented path.
13. **Remotion `@remotion/lottie`** and the Remotion-Rive effect chain (`effects`, `effectsOutputSize`) were not read in this lane.
14. **Licence interpretation** for GSAP in a video-rendering pipeline, and Theatre AGPL in a hosted authoring tool, is a legal question; the pages are silent (RT-055, RT-033).
