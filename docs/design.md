# Figma implementation notes

The uploaded **CSELEC CCIT Chatbot.fig** is a ZIP archive containing `canvas.fig`, six images, a thumbnail and metadata. Its SHA-256 is `902271576988c2cb31a2b3df70e4c382c910ae4e2cd5c6f28df33e461a29b987`; the repeated uploads are identical.

The binary scene graph was decoded using kiwi-schema 0.5.0 with raw-deflate and Zstandard decompression. This exposed 121 nodes across one design page and an internal canvas. The page contains a hidden **Original** frame (1:2, sidebar layout) and a visible **Revised Version** frame (34:2, top-bar layout). The revised frame is the implemented design. No Figma connector or authenticated Figma API was available; inspection was performed directly on the uploaded archive.

## Inspected measurements and assets

- Desktop frame: 1440 × 1024; top bar: 80 pixels high, red `#c91b17` to dark red `#7b120f`.
- Header content: approximately 1328 pixels wide; brand and profile tiles approximately 264 × 53, with 10-pixel corners.
- Font: Inter Medium and Semi Bold; 48-pixel welcome heading, 20-pixel subtitle, 26-pixel wordmark, 15-pixel card headings and 13-pixel descriptions.
- Message field: approximately 910 × 84 at x=265, y=516, with 10-pixel corners; send circle approximately 43 pixels.
- Cards: approximately 287 × 129 with 24-pixel gaps, starting near y=622. Exact labels are Programs & Academics, Student Services and Department Directory.
- Exported original plus, send and bulb outlines from their geometry blobs. The hidden brain/CCIT controls in the source remain hidden.
- Reused the transparent FACTS logo and sample portrait supplied in the archive. These are design assets, not a claim that the portrait is the visitor or that this logo has been independently confirmed as official department branding.
- Self-hosted Inter 400, 500 and 600 from Fontsource Inter 4.5.15 (Google Fonts Inter v12). Its SIL Open Font License is included with the files. No external font/CDN requests are required at runtime.

[design-reference.json](design-reference.json) records selected original node dimensions and typography. The [reference rendering](screenshots/figma-reference.png) was reconstructed from source geometry and text glyph outlines; it is not an official Figma-rendered export, and its portrait crop may differ slightly. The application itself is responsive HTML/CSS/JavaScript, not an image of the source.

## Interactive states and adaptations

The supplied file has no visible conversation, error, loading, dialog or mobile screens, and no working prototype interactions. Those states use the same red/white palette, Inter typography and rounded surfaces.

The sample person's name/email are replaced by Guest and an optional preferred name stored only in sessionStorage for the current tab. The profile chip opens this small personalization dialog; there are no accounts or authentication claims. The plus control starts a new chat, with confirmation before clearing messages. Source-document question choices appear when a topic card is opened. Missing enrollment forms, detailed requirements, contact information and office locations are stated explicitly instead of inferred from the design's marketing descriptions.

The send control is disabled for empty input or while a response is pending. FAQ disclosures and source-currency notices are additions needed to accurately describe the current retrieval-only mode. Conversation messages, source labels and errors are rendered as text. Layout switches to stacked cards and an avatar-sized profile button on small screens, while preserving keyboard access and a 44-pixel send target. Reduced-motion settings are respected.

## Actual screenshots

[Desktop](screenshots/desktop.png) · [Tablet](screenshots/tablet.png) · [Mobile](screenshots/mobile.png) · [Conversation](screenshots/conversation.png) · [Mobile conversation](screenshots/mobile-conversation.png) · [Loading](screenshots/loading.png)

These are Chromium captures of the running application in explicitly labeled FAQ mode. No screenshots show or claim a successful live AI response. Browser checks are recorded in [browser-results.json](screenshots/browser-results.json).

## Conversation improvements

The home/header retain the inspected Figma dimensions. Conversation states now include focused lists, a visible source-currency warning, native expandable original-source details, Copy answer, and Retry/Read FAQ answer instead controls. These extend states missing from the source frame using the existing font, colors and rounded surfaces. Current focused-answer and follow-up screenshots are under screenshots/improvements/.
