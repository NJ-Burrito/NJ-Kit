# Standards these points touch

Open this before quoting a statute, directive, WCAG criterion or RFC in a client-facing report — cited per point, with URLs. Referenced from SKILL.md § The report.

## Standards these points touch

Cited so a finding can be argued rather than asserted. Read the article before
quoting it in a client-facing report.

| Point | Standard | URL |
| --- | --- | --- |
| 4 — consent before storage | ePrivacy Directive 2002/58/EC, Art. 5(3) | <https://eur-lex.europa.eu/eli/dir/2002/58/oj> |
| 4, 6 — what consent must be | GDPR Art. 7; EDPB Guidelines 05/2020 on consent (no pre-ticked boxes) | <https://gdpr-info.eu/art-7-gdpr/> · <https://www.edpb.europa.eu/our-work-tools/our-documents/guidelines/guidelines-052020-consent-under-regulation-2016679_en> |
| 1–3, 5 — telling people what you do | GDPR Art. 13, information to be provided | <https://gdpr-info.eu/art-13-gdpr/> |
| 7 — data minimisation | GDPR Art. 5(1)(c) | <https://gdpr-info.eu/art-5-gdpr/> |
| 7 — minimisation as the default | GDPR Art. 25, data protection by design and by default | <https://gdpr-info.eu/art-25-gdpr/> |
| 8, 9 — third parties receiving data | GDPR Art. 13(1)(e), recipients; Art. 28, processors | <https://gdpr-info.eu/art-28-gdpr/> |
| 10–14 — accessibility | WCAG 2.2 — 1.1.1, 1.4.3, 2.1.1, 2.1.2, 2.4.3, 2.4.4, 2.4.7, 4.1.2 | <https://www.w3.org/TR/WCAG22/> |
| 15, 16 — fake reviews, unsupported claims | Directive 2005/29/EC on unfair commercial practices, as amended by (EU) 2019/2161 | <https://eur-lex.europa.eu/eli/dir/2005/29/oj> · <https://eur-lex.europa.eu/eli/dir/2019/2161/oj> |
| 17 — business details | E-Commerce Directive 2000/31/EC, Art. 5 | <https://eur-lex.europa.eu/eli/dir/2000/31/oj> |
| 18 — image copyright | Berne Convention | <https://www.wipo.int/treaties/en/ip/berne/> |
| 19 — local law | jurisdiction-specific; for Jordan, Personal Data Protection Law No. 24 of 2023 — confirm the current text with counsel | — |

### Group D — and how little of it is a standard

The honest column. Two rows cite something real; the rest are conventions, and
the report says so in the row rather than leaving the reader to assume.

| Point | Standard, or the honest absence of one | URL |
| --- | --- | --- |
| H1, H16, H20 — reflow, resize text, target size | WCAG 2.2 — 1.4.10, 1.4.4, 2.5.8 | <https://www.w3.org/TR/WCAG22/> |
| H3, H11, H12, H13, H17 — the delegated halves | WCAG 2.2 — 2.1.1, 2.4.4, 3.3.1, 3.3.3, 4.1.2, 4.1.3 | <https://www.w3.org/TR/WCAG22/> |
| H8 — a 404 must return 404 | HTTP Semantics, RFC 9110 §15.5.5 — this is what makes a soft-404 wrong rather than untidy | <https://www.rfc-editor.org/rfc/rfc9110#section-15.5.5> |
| H2, H7, H15 — broken and dead links | **Convention.** No standard requires a link to work. | — |
| H4, H5, H6 — favicon, title, meta description | **Convention** — browser and search-engine practice. `<title>` is required by HTML but says nothing about its content. | — |
| H9 — copyright year | **Convention, and not even a strong one.** Copyright subsists without a notice under Berne; a stale year is a credibility signal. | <https://www.wipo.int/treaties/en/ip/berne/> |
| H10 — image weight | **Convention.** A performance practice, not a rule. | — |
| H14 — placeholder text | **Convention** — except where the placeholder is a business detail, which returns it to point 17 and the E-Commerce Directive. | — |
| H18, H19 — clickable phone and email | **Convention** for the link; the *mismatch* case is a misleading-action problem, closer to 15/16 in kind than to anything here. | — |

### Groups E and F — one real standard, one browser rule, and a lot of guidance

Group E is Group A's standards again, applied to the policy's text rather than
its existence, so nothing new is cited. Group F cites almost nothing, and that
is the finding rather than an omission.

| Point | Standard, or the honest absence of one | URL |
| --- | --- | --- |
| L1 to L4 — the policy and its contents | GDPR Arts. 12–14 (what must be told, and plainly); PDPL in Jordan and Saudi Arabia | <https://gdpr-info.eu/art-13-gdpr/> |
| L3 — AI disclosure specifically | **Moving, and jurisdictional.** No single instrument to cite. Report presence; never report compliance. | — |
| L5 — deletion honoured | GDPR Art. 17, right to erasure | <https://gdpr-info.eu/art-17-gdpr/> |
| L8, L9 — cancellation friction and silent renewal | Unfair Commercial Practices Directive 2005/29/EC; FTC negative-option rules | <https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=celex%3A32005L0029> |
| L7 — fake testimonials | Point 15 again, unchanged | — |
| L10 — AI safety response | **No standard to cite here, and that is the point.** Delegate to people who do this work. | — |
| S16 — HTTPS and mixed content | **Convention plus a browser rule.** Browsers block active mixed content themselves; no law requires TLS in general. | <https://developer.mozilla.org/en-US/docs/Web/Security/Mixed_content> |
| S15 — CORS | **A browser rule, not a legal one.** Fetch Standard. | <https://fetch.spec.whatwg.org/#http-cors-protocol> |
| S17, S18 — security headers and cookie flags | **OWASP guidance**, plus RFC 6265bis for the cookie attributes. Guidance, never *required*. | <https://owasp.org/www-project-secure-headers/> |
| S1, S3 — keys reaching the browser or the history | **Not a law. Provider terms, and the cost of a rotated key.** | — |
| S6 to S9 — active testing | OWASP ASVS, for whoever runs it. **This skill does not.** | <https://owasp.org/www-project-application-security-verification-standard/> |
| S10, S12, S20 — DB rules, spend cap, production settings | **Not the deployed site.** Nothing to cite because there is nothing on the page. | — |

**Not one of reel 4's twenty maps to a statute**, and a report that lets a
reader think otherwise has done more harm than one that omitted the section.
The legal surface is Groups A, C and E. Keep it there.

