# Implemented chatbot improvements

The update addresses the review of commit 7ff1681 while preserving the supplied revised Figma home layout and the original 22 source records.

## Matching and grounding

The matcher now handles phrase-level names such as Course-Specific Scholarship and 50-TAG, common English/Tagalog aliases, named program abbreviations and close intent typos. It indexes answer terms as well as questions/keywords, chooses sources by topic and program, and can retrieve both sides of a comparison or multi-topic request. It no longer appends BSCS faculty/careers to a simple program-offering question.

Unsupported-detail checks remain in place for exact fees, deadlines, contacts, opening hours, unsupported program codes, delivery modes and other missing facts. Privacy handling covers the third-person/Tagalog cases identified in the review. Known false-fallback examples from the review now retrieve the expected sources. These fixes do not imply that every possible paraphrase is understood.

## Answer presentation and source review

FAQ summaries are extractive and generated without an AI API call. They use source-based program lists, scholarship discount bullets, named laboratory lists and readable career/faculty lists. Focused BSCS availability answers are under 180 characters in the regression test. Full original answers remain available in `details` and in the native View source and full details disclosure. Currency warnings and the official-name contradiction remain visible. Copy answer copies the displayed answer; source/currency information remains visible beside it.

The institution's actual current facts were not changed. See department-verification.md for the unresolved college-name discrepancy, time-sensitive details and missing official contact/admissions information.

## Follow-ups

The browser carries only selected BSCS/BSIT/BSEMC IDs and a whitelisted pending topic. A follow-up such as “What jobs can I get after this program?” is resolved to the selected program and retrieves fresh source records. If the program is absent or ambiguous, the chatbot asks which one; a short reply such as “BSIT” completes the pending question. New chat resets context. Refresh also resets it; no transcript, database, user account or cross-user server session was added. Arbitrary client facts/prompts are rejected.

## Explicit recovery

Failed requests show Retry and, when source information is available, Read FAQ answer instead. Retry preserves the original question/context, avoids duplicate user messages and leaves an unsent draft intact. An older retry cannot overwrite a newer program context. FAQ fallback is a one-request opt-in, labeled as not AI generated, and never calls a provider or changes the configured server mode. Source-free unknown answers also need no provider request. No silent automatic model/provider switching was added.

## Actual validation

- 230 automated tests passed.
- 14 existing browser scenarios passed across six viewport sizes.
- 6 new browser scenarios passed for source details/copy, follow-ups/reset/clarification, Retry, FAQ fallback, old-turn context and safe rendering of model/source text.
- 95 HTTP source-support/mode checks passed: 22 original FAQs, 33 review phrasing cases, 22 additional variations, 12 unsupported questions and 6 privacy cases.
- The 33 review phrasing cases changed from 8 expected-source matches to 33. These cases were used to guide implementation and are not a held-out estimate of general accuracy. Additional negative-detail and context tests are in the automated suite.

See evaluation-improved.json, screenshots/browser-results.json and screenshots/improvements/browser-results.json for executed evidence. Successful answers in browser tests came from the running FAQ-mode application. Provider failures and safety fixtures were deliberately simulated. There is no successful live AI-generation claim: this cloud checkout has no configured API key, and the user's earlier local tests reported 503 and 404 responses.
