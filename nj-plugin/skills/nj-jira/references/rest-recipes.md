# Jira REST v2 recipes (Server/Data Center, Basic auth)

Base = `$JIRA_BASE_URL`. Header on every call: `Authorization: Basic <b64(user:pass)>`, `Accept: application/json`, `X-Atlassian-Token: no-check`. Build the header in code from env; never echo it, never put it on a command line that lands in history or logs. On 429 / 5xx retry with back-off (1.5 s x n, 4 tries).

| Goal | Call |
|---|---|
| read one | `GET /rest/api/2/issue/KEY?expand=renderedFields,changelog` (404/403 = not visible) |
| search (all pages) | `POST /rest/api/2/search` `{jql, fields:[...], startAt, maxResults}` (loop until `startAt >= total`) |
| download attachment | `GET <attachment.content URL>` with the same auth |
| create Bug | `POST /rest/api/2/issue` `{fields:{project:{key}, issuetype:{name:"Bug"}, summary, description (wiki markup), assignee:{name}, environment:"QA + Staging", labels:["env-qa","env-staging"], timetracking:{originalEstimate:"2h", remainingEstimate:"2h"}}}` |
| attach file | `POST /rest/api/2/issue/KEY/attachments` multipart field `file` (+ `X-Atlassian-Token: no-check`). Allowed evidence types are screenshots (.png .jpg .jpeg), videos (.mp4 .webm), .gif, .md and .pdf (official output letters), nothing else; .docx .txt .json .log are refused (owner, 2026-10-19); check the extension before the POST |
| link to Story | `POST /rest/api/2/issueLink` `{type:{name:"Relates"}, inwardIssue:{key:BUG}, outwardIssue:{key:STORY}}` |
| comment | `POST /rest/api/2/issue/KEY/comment` `{body}` |
| list transitions | `GET /rest/api/2/issue/KEY/transitions` (ids are workflow-specific) |
| transition | `POST /rest/api/2/issue/KEY/transitions` `{transition:{id:"<id>"}}` |
| required fields | if create answers 400, read `errors` and add exactly those fields (this project's workflow required the estimate) |

## Verify after filing (always)
GET the new issue: `reporter`, `assignee`, `issuelinks` (the Story), `attachment` count == files sent, `timetracking`. A filing without this read-back is not done.

## Description is wiki markup (v2)
`h3. Title`, `# numbered step`, `* bullet`, `{{mono}}`, `*bold*`. Arabic text goes in as-is (UTF-8); do not mix Markdown syntax.

## Pitfalls
- Create returns the key only; attach and link are separate calls: a crash in between leaves a bare Bug. Re-run is safe only if you GET first (idempotent).
- A shell that holds the password in an argument leaks it into process lists; use env + code.
- PowerShell and cmd mangle Arabic and quotes in inline JSON; write the JSON body to a file in the scratchpad and send that.
- Attachments over 25 MB and videos: list only, do not download.
- JQL text search (`summary ~`, `text ~`) rejects Lucene operators `[ ] ( ) : ·` …: strip them from the search phrase, then match the returned summary exactly (lesson 13, 2026-10-12; `nj_rank.py` does this, same rule for any JQL text search).
