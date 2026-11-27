# Off-screen renderers: how a crew sees its own work

A crew without eyes guesses. Whatever the stack, the renderer must: (a) show nothing on anyone's screen and make no
sound, (b) write real frames to a directory the caller names, (c) write one contact sheet (a grid of the frames) so a
whole variant is judged in one look, (d) take the variant as an argument, (e) exit by itself, (f) refuse anything it does
not recognise. Sample frames across the fixed beats (for example 8 evenly spaced across the variant) plus one frame
after the result has landed, so the settled state is checked too. Compute the sample times from the contract, never
type them.

Put the render switch first in the command line and make the program do nothing for unknown arguments.

## WPF / WinForms (.NET desktop)

- Create the window as normal but never activate it: position it far off screen (for example Left = -32000),
  `ShowActivated = false`, `Topmost = false`, and give the root an opaque backdrop so frames read.
- Drive the animation with the real timer; in the tick, take a frame when the clock passes each sample time.
- WPF: `RenderTargetBitmap(width, height, 96, 96, PixelFormats.Pbgra32)`, `bmp.Render(element)`, `Freeze()`, encode with
  `PngBitmapEncoder`. WinForms: `Control.DrawToBitmap`.
- Skip sound in render mode. Close the window when the last frame is saved.
- Build the contact sheet with a `DrawingVisual` into a second `RenderTargetBitmap` (3x3 for 9 frames).
- A second entry (`/render-ui <screen> <dir>`) is worth adding for panels and widgets: render the whole panel with
  live or fixture data, the hover state, and a 200% version for detail.
- Build and run from PowerShell, not from bash through `cmd /c` (see failure-modes.md).

## Web (headless Playwright)

- Headless Chromium, fixed viewport and `deviceScaleFactor`.
- Do not sleep and hope. Make the animation seekable: a paused timeline (GSAP `timeline.pause().seek(t)`), or Web
  Animations (`document.getAnimations().forEach(a => { a.pause(); a.currentTime = t })`), then `page.screenshot()` at
  each sample time. This also makes frames repeatable.
- Assert the page is ready before the first shot (an element that exists only after boot). A shot taken before boot
  proves nothing.
- Contact sheet: stitch the PNGs with Pillow, or a second page that lays them in a grid.
- Close the browser in a `finally`, and name the browser profile after the run so a stray one can be found.

## Video frames (HTML-to-video, Remotion, ffmpeg)

- Render frames at chosen times, not the whole film: Remotion `renderStill` per frame number; the HTML renderer's
  seek-and-capture mode; or `ffmpeg -ss <t> -i in.mp4 -frames:v 1 frame-%02d.png`.
- Contact strip: `ffmpeg -i in.mp4 -vf "fps=2,scale=320:-1,tile=4x3" sheet.png`, or the engine's equivalent.
- Sound cannot be seen. The crew states which cues it cut to the picture; sync is checked by ear or with an
  audio-analysis tool, and reported as not verified until someone has.

## Static images and SVG

- SVG: render with a headless browser or `resvg` / `rsvg-convert` at 1x and 2x. For icons also check 16, 32 and 64 px,
  because most icon faults show only small.
- Raster: the file is the frame. Make a contact sheet of the variants side by side on a light and a dark ground.
- Check file weight and node count against the budget in the contract.

## Gate for the renderer itself

Before briefing crews, run the renderer once per variant and confirm the number of frames, that the sheet exists and
that it is not blank (more than one distinct pixel value). A renderer that writes empty frames gives crews false
confidence.
