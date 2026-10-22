// deck-v3 PPTX: one full-bleed Remotion clip per slide, its last frame as the poster,
// the approved speaker notes in the notes pane. Autoplay + fade are added afterwards by
// PowerPoint itself (postprocess-deck.ps1) — hand-written <p:timing> XML was refused as corrupt.
//   node build-pptx.js ar|en        (PPTX_NODE_MODULES points at a folder holding pptxgenjs)
const fs = require('fs');
const path = require('path');
const pptxgen = require(path.join(process.env.PPTX_NODE_MODULES || 'node_modules', 'pptxgenjs'));

const lang = process.argv[2];
if (!['ar', 'en'].includes(lang)) throw new Error('usage: node build-pptx.js ar|en');
const CODE = lang.toUpperCase();
const deck = JSON.parse(fs.readFileSync(path.join(__dirname, 'remotion', 'src', 'data', `${lang}.json`), 'utf8'));

const pres = new pptxgen();
pres.layout = 'LAYOUT_WIDE';
pres.title = deck.title;
pres.company = 'Ensera';
if (lang === 'ar') pres.rtlMode = true;

const notes = [deck.subtitle + ' · ' + deck.date, ...deck.slides.map((s) => s.note || '')];
notes.forEach((note, i) => {
  const id = `${CODE}-${String(i).padStart(2, '0')}`;
  const clip = path.join(__dirname, 'clips', id + '.mp4');
  const poster = path.join(__dirname, 'posters', id + '.png');
  if (!fs.existsSync(clip) || !fs.existsSync(poster)) throw new Error('missing ' + id);
  const s = pres.addSlide();
  s.background = { color: '0B1F2A' };
  s.addMedia({ type: 'video', path: clip, x: 0, y: 0, w: 13.333, h: 7.5,
    cover: 'data:image/png;base64,' + fs.readFileSync(poster).toString('base64') });
  if (note) s.addNotes(note);
});

const out = path.join(__dirname, 'out', `KAC-Recurrence-Map_deck_${CODE}.pptx`);
pres.writeFile({ fileName: out }).then(() => console.log('wrote', out, notes.length, 'slides'));
