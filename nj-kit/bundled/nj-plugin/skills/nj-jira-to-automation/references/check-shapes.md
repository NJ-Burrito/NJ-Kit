# jira-checks.ts skeleton

Reference implementation: `Improvement Delivery/Automation Tests/services/مديرية الاجهزة الطبية و المستلزمات/طلب الموافقة على تعديل مستلزم طبي/jira-checks.ts` (form checks on a second page of the signed-in context).

```ts
// Header: which Bugs, which harvest date, which environment (ids and dates, no secrets).
import { Page, expect } from '@playwright/test';
import { jiraCheck, jiraSkipped } from '../../../lib/jira';
import type { StageHooks } from '../../../lib/journey';
import { openForm } from '../../../lib/service';

export const noteEnv = {} as Record<string, 'qa'>;      // since 2026-10-12 customs runs on staging; leave empty. Example for a future QA-only note: { 'PROJ-1234 N3': 'qa' }

async function formChecks(page: Page) {
  const p = await page.context().newPage();             // second page: the filing page is never touched
  await openForm(p, '<route>');
  try {
    await jiraCheck('PROJ-1234 N1', '<short title>', 'PROJ-1234 · 2026-10-11 · <author>', async () => {
      // assert the verbatim "fixed" shape; return a short detail, or throw
      expect(await p.getByText('<exact text>').count(), '<what is wrong>').toBeGreaterThan(0);
    });
  } finally { await p.close(); }
}

jiraSkipped(['PROJ-1234 N7: لا يمكن فحصه آلياً: <reason>']);

export const hooks: StageHooks = {
  onForm: formChecks,                                   // no filed request needed
  // onSent / onDesk / onFinal / afterPress: notes seen only after «إرسال» or at a desk
};
```

## Rules
- One `jiraCheck` per note id, id format `<KEY> N<n>` (the per-note test title is derived from id + title; keep titles unique).
- Buttons by caption, keyboard first (focus + Space/Enter), never forced clicks, never press «التوقيع الرقمي», never reject/cancel/return unless the step is an explicit reject test.
- A check that needs a value from the portal's validated data takes it from the suite's test-data file; no value = «محجوب لنقص البيانات», never invented.
- The generator reads `jira-checks.ts` as text (`parseNotes`): keep `jiraCheck('<id>', '<title>', ...)` on one line start, and hook names only where they are used.
- explain.json entry per id: `{ "plain": "...", "notReflected": "...", "fix": "..." }` in plain Arabic for developers, written from the Jira text + the latest detail line.
