# Arabic faults that need reading

The scanner in `scripts/scan.py` has already taken the mechanical faults. What
is left is decided by the sentence, not by the character, which is why it is
here and not in the script.

Ordered by how often they appear in formal Jordanian government and regulatory
prose — SRS documents, ministry submissions, request forms, manuals.

## Contents

1. [Taa marbuta vs heh — ة / ه](#1-taa-marbuta-vs-heh--ة--ه)
2. [Alef maksura vs yeh — ى / ي](#2-alef-maksura-vs-yeh--ى--ي)
3. [Hamza forms — أ إ آ ا ء ؤ ئ](#3-hamza-forms--أ-إ-آ-ا-ء-ؤ-ئ)
4. [أن vs إن](#4-أن-vs-إن)
5. [Number–noun agreement](#5-numbernoun-agreement)
6. [Formal register](#6-formal-register)
7. [Punctuation and layout](#7-punctuation-and-layout)

---

## 1. Taa marbuta vs heh — ة / ه

The most common Arabic typo in existence, and invisible to every spellchecker.

The test is pronunciation when the word is followed by something: if the sound
is *-at-*, it is **ة**; if it is *-ah/-h*, it is **ه**.

| Wrong | Right | Why |
| --- | --- | --- |
| الخدمه | الخدمــة | feminine noun |
| المؤسسه | المؤسســة | feminine noun |
| وثيقه | وثيقــة | feminine noun |
| مديرية الاغذيه | مديرية الأغذيــة | feminine noun |

**But `ه` is right** as a masculine possessive suffix: «طلبه» (*his request*),
«موقعه» (*its site*). «طلبة» is a different word (*students*). So this cannot
be a find-and-replace — it changes meaning.

## 2. Alef maksura vs yeh — ى / ي

Both are correct in their places; the error is using one for the other.

**ى is correct** at the end of: على، إلى، حتى، لدى، متى، يرجى، مستوى، معنى،
مبنى، أعلى، أولى، مستشفى — and in any word whose final vowel is a long *ā*
written this way.

**ي is correct** in: علي (the name), and wherever the final sound is *-ī*:
«الطبي»، «الدوائي»، «الفني».

The pair that actually bites in these documents:

- «على» = *on/upon* (preposition) — always ى
- «علي» = *Ali* (name), or *on me* — ي

A sentence-level decision, which is why the scanner deliberately does not
flag final ى. It would cry wolf on «يرجى» and «مستوى» and be switched off.

## 3. Hamza forms — أ إ آ ا ء ؤ ئ

Frequently dropped altogether in fast typing: «الاغذيه» for «الأغذية».

Initial hamza:

- **أ** when the vowel is *a* or *u*: أحمد، أن، أول، الأغذية، الأدوية
- **إ** when the vowel is *i*: إن، إلى، إجازة، إدارة
- **آ** for long *ā*: آخر، القرآن، الآن
- **ا** bare, no hamza: اسم، ابن، اثنان، امرأة (hamzat al-wasl)

Medial and final hamza sit on a seat chosen by the surrounding vowels —
مسؤول، مسائل، شيء، هيئة. If a word looks wrong and you cannot derive the
seat with confidence, flag it rather than guessing; a wrong seat is a visible
error to an Arabic reader and no better than the original.

## 4. أن vs إن

Different words, constantly swapped, and the difference is grammatical.

- **أن** introduces a subordinate clause — *that*: «يجب أن يقدم الطلب»
- **إن** is emphatic, or opens a conditional — *indeed / if*: «إن الطلب مكتمل»
- **أنّ** after «حيث» or a verb of saying: «ذكر أنّ الوثيقة مرفقة»

In an SRS, the overwhelmingly common correct form is **أن**, because the
document is full of "the system shall … that …" constructions. A stray «إن»
in that position is almost always an error.

## 5. Number–noun agreement

Arabic number agreement is where careful documents give themselves away, and
it is genuinely intricate.

- **3–10**: the counted noun is **plural**, and the number takes the *opposite*
  gender to it — «ثلاث وثائق» (وثيقة is feminine → number is masculine-form),
  «خمسة طلبات».
- **11–99**: the counted noun is **singular accusative** — «خمسة عشر طلبًا»,
  never «خمسة عشر طلبات».
- **100, 1000**: singular genitive — «مئة طلب».

If a document mixes digits and words inconsistently — «5 طلبات» in one line
and «خمسة طلبات» in the next — that is a house-style question, not an error.
Raise it once rather than correcting every instance silently.

## 6. Formal register

Ministry and regulatory documents have conventions. Breaking them is not a
grammatical error but reads as unprofessional to the intended audience.

- **No dialect.** «بدنا» → «نريد»، «هلأ» → «الآن»، «مبسوط» → «راضٍ».
- **Passive and impersonal for procedure**: «يتم تقديم الطلب» rather than
  «أنت تقدم الطلب». Direct second-person address is for user manuals, not
  regulatory text — and in a *manual* the second person is correct, so match
  the document type rather than applying one rule everywhere.
- **Verbal nouns over verb chains**: «عند تقديم الطلب» rather than
  «عندما يقوم المستخدم بتقديم الطلب». The «يقوم بـ» construction is a
  well-known padding pattern; it is not wrong, but a document full of it
  reads as translated.
- **Terminology consistency.** Fix «المستحضر» / «المنتج» / «الصنف» drifting
  within one document — but ask before standardising, because the client's
  own regulation may fix the term.

## 7. Punctuation and layout

The scanner catches the mechanical half. What it cannot judge:

- **Arabic comma «،» spacing**: attaches to the preceding word, one space
  after — «الأول، الثاني، الثالث».
- **Brackets and quotes in RTL** render with their mirror image; `(` opens on
  the right visually. Do not "fix" what looks reversed in a plain-text editor
  — check the rendered output before changing anything.
- **Latin runs inside Arabic** need directional isolates. Without them,
  «استخدم API.» renders with the full stop at the wrong end. This is a
  rendering fault, not a spelling one, and it is invisible in a plain editor.
- **Arabic-Indic vs Western numerals** — either is correct; consistency is the
  requirement. Jordanian government documents commonly use Western digits even
  in otherwise Arabic text, so do not "correct" Western digits to ٠١٢ without
  asking.
