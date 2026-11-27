# <PROJECT> <RELEASE>: <PIECES> contract (<DATE>)

Owner's request: "<OWNER REQUEST>".
This file is the contract between the crews (who restyle and animate) and everything cut to them (sound, captions,
tests). Crews may change anything not listed under FIXED.

## FIXED (may not move)
- Beat times: all times in milliseconds from the moment the piece is first on screen, per variant (tables below).
- Canvas or slide size: <SIZE>.
- Public API and entry points: <API>.
- Elements that must stay honest: <E.G. the progress or result text>.

## Budget
- Animated layers: no blur or shadow effects; cache static groups; animate transforms and opacity only.
- Element budget: <N>. Frame rate: <FPS>.
- Language and toolchain: <E.G. C# 5 for a .NET Framework csc build; ES2020; Python 3.10>.
- House rules of the project: <FONTS, COLOURS, DIRECTORIES, ENCODING, NAMING>.

## Which variant plays
| Piece | Variant 0 | Variant 1 | Variant 2 | Variant 3 |
|---|---|---|---|---|
| <PIECE> | <NAME: CONDITION> | <NAME: CONDITION> | <NAME: CONDITION> | <NAME: CONDITION> |

## Beats per variant
### <PIECE>-<N> <NAME>, <LENGTH> ms
| ms | beat | sound or cue |
|---|---|---|
| <MS> | <WHAT HAPPENS> | <CUE OR none> |
