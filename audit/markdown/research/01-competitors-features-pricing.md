# AI short-form clipping tools: features, pricing, and what counts as "premium"

Research date: 2026-11-22. Prices are US list prices in USD before tax, as shown on each vendor's page on that date unless a note says otherwise. Many vendors show regional prices, run A/B tests, or render prices with JavaScript, so a figure taken from a secondary source is labelled as such. Anything I could not confirm is marked **unverified**.

Method: I read official pricing pages through the Jina reader (`r.jina.ai`) and used Exa search for prices the pages render client-side (Vizard, Descript, Choppity), for help-centre pages, and for dated third-party snapshots. Every fetched page was treated as untrusted data. I saw no prompt-injection attempts. Two pages carried notices worth flagging, and I followed neither: Riverside's page said it was a "staging environment" copy, and Munch's page had "Ask AI for a summary" links that pre-fill a promotional ChatGPT prompt.

---

## 1. Per-competitor profiles

### OpusClip (opus.pro)
- **Plans** ([pricing](https://www.opus.pro/pricing)):
  - **Free** $0: 60 credits/mo.
  - **Starter** $15/mo, monthly billing only.
  - **Pro** $29/mo, or $14.50/mo billed yearly ($174). Sold "per pack" of 2 seats, up to 4.
  - **Business**: custom pricing.
  - Credit amounts and the annual price come from a dated secondary snapshot ([askgpu, 2026-10-31](https://askgpu.com/opus-clip-pricing/)): Starter 150 credits, Pro 300 credits. 1 credit = 1 minute of source video.
- **Free tier** ([pricing](https://www.opus.pro/pricing)):
  - Animated captions only "with watermark".
  - Export up to 1080p, files kept 3 days.
  - Uploads up to 10 GB.
  - No editing, virality score, B-roll or posting.
- **Headline features:** AI clipping with an "AI copilot" (pick a timeframe and clip length; Pro adds topic search and "prompt to clip"), virality score, auto hook, animated captions with auto emoji and keyword highlights, dynamic layout switch, screenshare and gameplay layouts, and genre-specific reframing ([pricing](https://www.opus.pro/pricing)).
- **Paywalled:**
  - Starter adds:
    - virality score;
    - reprompt clipping;
    - genre-specific reframing;
    - text and timeline editing;
    - 3 AI image and 3 stock B-roll clips a month;
    - AI voice-over (20/day);
    - filler and pause removal;
    - AI upscaling;
    - watermark-free exports;
    - a title, description and hashtag generator;
    - YouTube auto-import.
  - Pro adds:
    - topic search and "prompt to clip";
    - 30 GB uploads and public MP4 URL import;
    - custom fonts and auto-censoring;
    - 1:1 and 16:9 output and moving-object tracking;
    - AI video B-roll ("Agent Opus") and unlimited stock B-roll;
    - bad-take removal, eye-contact correction, **video dubbing** and AI sound effects;
    - a brand kit with up to 4 templates, intro and outro cards, and a brand vocabulary;
    - bulk export and Premiere Pro / DaVinci Resolve export;
    - posting to multiple profiles;
    - a team workspace;
    - a **Video Editing API, Scheduler API, MCP connector** and Zapier.
  - Business adds 4K schedule and download, clip analytics, real-time trend analysis, SSO, CMS integration and sub-teams ([pricing](https://www.opus.pro/pricing)).
  - The askgpu snapshot lists the API as "Limited (beta)" on Pro and 4K export "from 4K source" on Pro. This conflicts with the official table, where "4K schedule and download" is Business only.

### Vizard (vizard.ai)
- **Plans:**
  - **Free** $0: 60 credits/mo.
  - **Creator** from $29/mo for 600 credits, up to $295/mo for 6,200 credits, in 15 steps of 400 credits.
  - **Business** from $39/mo for 600 credits, up to $445/mo.
  - Yearly billing is 50% off, so Creator 600 is $14.50/mo ($174/yr).
  - 1 credit = 1 minute of upload. Unused credits roll over for 2 months.
  - The official page renders the prices with JavaScript, so the figures come from dated snapshots ([NoobClaw, 2026-11-21](https://noobclaw.com/blog/vizard-ai-pricing/); [What the tech, 2026-11-07](https://whathetech.net/ai-compare/tools/vizard)). The tier structure and limits are official ([pricing](https://vizard.ai/pricing)).
- **Free tier** ([pricing](https://vizard.ai/pricing)):
  - 720p export with a watermark ([What the tech](https://whathetech.net/ai-compare/tools/vizard)).
  - 60-minute, 1 GB uploads; exports up to 10 minutes; projects kept 3 days.
  - Agent on the "Flash" model only.
  - API limited to 1 call/min.
- **Headline features:** AI clipping, a "Vizard Agent" (a chat editor with Flash, Pro, Max and Ultra models), auto reframe and face tracking, auto emojis, keyword highlights, auto B-roll, upscaling, subtitle translation, a Clipping API and an **MCP connector** ([pricing](https://vizard.ai/pricing)).
- **Paywalled** ([pricing](https://vizard.ai/pricing)):
  - Creator adds:
    - watermark removal;
    - 4K upload and export;
    - 10-hour, 30 GB uploads;
    - all Agent models;
    - scheduling to 6 social accounts;
    - 100 GB storage;
    - SRT transcripts;
    - higher API rate limits.
  - Business adds:
    - seats (about $5–10/seat/mo; Vizard's sources conflict, per [What the tech](https://whathetech.net/ai-compare/tools/vizard));
    - a brand kit and custom fonts;
    - project sharing;
    - 20 social accounts;
    - unlimited storage;
    - an API limit of 10/min.
  - Which tier gets auto B-roll and auto emojis: **unverified** (the checkmarks did not render).

### Klap (klap.app)
- **Plans** ([pricing](https://klap.app/pricing)). Klap prices by clips generated, not minutes:
  - **Basic**: 100 clips/mo, $29/mo or $14.50/mo yearly ($174).
  - **Pro**: 300 clips/mo, $79/mo or $39.50/mo yearly ($474).
  - **Pro+**: 1,000 clips/mo, $189/mo or $94.50/mo yearly ($1,134).
  - Yearly billing is 50% off.
- **API** (self-serve): $0.44 per input video, $0.32 per short, $0.48 per export ([pricing](https://klap.app/pricing)).
- **Free tier:** a 1-video trial. You can preview and edit, but downloading and posting need a paid plan. Paid exports have no watermark ([pricing](https://klap.app/pricing)).
- **Headline features (all plans):** virality score, active-speaker reframing, animated captions, 99+ languages, scheduling and publishing to TikTok, YouTube, Instagram, LinkedIn and Facebook, unlimited social accounts, post analytics, an editor with B-roll and hook titles, and sources up to 3 hours ([pricing](https://klap.app/pricing)).
- **Paywalled:** Klap has no feature tiering; every paid plan has the same features and only the clip volume changes. The whole product sits behind the paywall, since the free trial cannot export.

### Submagic (submagic.co)
- **Plans** ([pricing](https://www.submagic.co/pricing); [help centre](https://care.submagic.co/en/article/how-much-does-it-cost-to-use-submagic-1xm83pa/)):
  - **Starter**: $19/mo or $12/mo yearly ($144), 45 credits.
  - **Pro**: $39/mo or $23/mo yearly ($276), 120 credits.
  - **Business**: $69/mo or $41/mo yearly ($492), 300 credits.
  - **Custom**: contact sales.
  - Prices are per member.
  - Credit costs: an upload is 3 credits, captions are free, other AI features cost 1–3 credits, and a Magic Clips run or an "Iris" edit costs 8.
- **API packs:** 250 min for $57/mo, down to $0.10/min at 5,000+ min ([pricing](https://www.submagic.co/pricing)).
- **Free tier:** a trial with 15 credits once. Exports carry a watermark ([help centre](https://care.submagic.co/en/article/how-much-does-it-cost-to-use-submagic-1xm83pa/)).
- **Headline features:** animated captions (the core product), "Magic Clips" long-to-short with sources up to 3 hours, "Iris" (an AI editor with chat revisions), B-roll and audio, text-based trimming, and an AI hook title ([pricing](https://www.submagic.co/pricing)).
- **Paywalled** ([pricing](https://www.submagic.co/pricing)):
  - Starter: 1080p/30fps and 2-minute videos.
  - Pro adds:
    - 5-minute videos and 2K export;
    - Pro caption templates;
    - removal of bad takes and silences;
    - AI audio cleanup;
    - publishing and social analytics;
    - Storyblocks B-roll;
    - a brand kit.
  - Business adds:
    - 30-minute videos and **4K/60fps** export;
    - 30 custom templates;
    - **API at 100 min/mo** (Starter and Pro get 10 min/mo);
    - multiple social accounts;
    - priority rendering;
    - a custom words dictionary.
  - AI eye-contact correction and the AI hook title appear as feature rows, but their tier is **unverified**.

### Captions.app (by Mirage, captions.ai)
- **Plans:**
  - **Free**: 60–200 credits once ([Marxx, 2026-11-03](https://marxx.ai/prices/captions-app-pricing); [StoryCut](https://www.storycut.com/alternatives/captions-ai)).
  - **Lite**: $4.99/mo, Android only.
  - **Basic**: $9.99/mo, 200 credits ([help centre](https://captions.ai/help/docs/subscriptions)).
  - **Max**: $24.99/mo, 500 credits, 2 seats.
  - **Frontier**: $69.99/mo, 1,400 credits, 3 seats ([pricing](https://captions.ai/pricing)).
  - **Frontier 2x/4x**: $139.99 and $279.99 ([billing help](https://captions.ai/help/mirage/account-management/mirage-billing)).
  - **Tesseract** (business): contact sales.
  - Yearly plans exist "at a discounted rate", but yearly prices for Max and Frontier are **unverified** (not published). Basic is $64.99/yr on iOS according to [StoryCut](https://www.storycut.com/alternatives/captions-ai).
  - Credits roll over, up to 3× the monthly allowance ([pricing](https://captions.ai/pricing)).
- **Free tier:** 1 caption template and basic editing (trim, transitions). No generative AI ([pricing](https://captions.ai/pricing)).
- **Headline features:**
  - AI Edit styles and a chat-based editor;
  - "Clips" (long to short);
  - AI Twin and digital avatars, AI Creator, AI Ads;
  - AI B-roll, music and SFX;
  - AI voiceover, voice clone, AI Translate and **AI Lipdub**;
  - Reddit-to-Reel;
  - AI denoise and AI censor;
  - captions in 100+ languages ([pricing](https://captions.ai/pricing)).
  - Hindi and Hinglish captions are listed in the help centre according to [Marxx](https://marxx.ai/prices/captions-app-pricing) (secondary source, so **unverified** against the original).
- **Paywalled:** "Clips" (long to short) starts at **Max** ($24.99), as do generative B-roll, the AI twin, translation and lip-dub ([help centre](https://captions.ai/help/docs/subscriptions); [pricing](https://captions.ai/pricing)).

### Munch → now "Munch Studio" (munchstudio.com)
- **Pivot:** getmunch.com now redirects to munchstudio.com. Munch repositioned as an "AI social media manager". Clipping is "one piece of the whole job" ([why-munch-studio](https://www.munchstudio.com/why-munch-studio)).
- **Plans** ([pricing](https://www.munchstudio.com/pricing)):
  - **Essential**: $68/mo or $38/mo yearly ($456), 500 min of video repurposing, 1 member.
  - **Premium**: $85/mo or $60/mo yearly ($720), 1,000 min, unlimited members.
  - **Studio**: $148 or $118/mo, up to 5 brands, 2,500 min.
  - **Scale**: $398 or $318/mo, up to 15 brands, 7,500 min.
  - Every plan has a 7-day trial. There is no free tier.
- **Headline features:** "Business deep learning" (trains on your site and brand), a content strategy, video scripts, generated videos, unlimited posters and carousels, a smart planner, publishing to 5 networks, and a performance dashboard ([pricing](https://www.munchstudio.com/pricing)).
- **Paywalled:** everything; tiers scale by brands, minutes and generated videos. Details of the old clip-level features (virality score, captions) on the current product: **unverified**.

### Choppity (choppity.com)
- **Plans:**
  - **Free** $0.
  - **Starter**: $24/mo or $16.80/mo yearly ($201.60).
  - **Creator**: $32/mo or $22.40/mo yearly.
  - **Team**: $48/mo or $33.60/mo yearly, from 3 seats.
  - **Enterprise**: custom.
  - Yearly billing is 30% off. Prices come from the Exa capture of the official page ([pricing](https://www.choppity.com/pricing/)) and match [SaaSHunter](https://saashunter.si/tools/choppity/pricing).
- **Limits by plan** ([pricing](https://www.choppity.com/pricing/)):
  - AI video analysis: Free 45 min (secondary sources say 1 h), Starter 3 h, Creator and Team 5+ h.
  - Storage: 2 / 40 / 100 / 200 GB.
  - Projects kept: 3 days on Free, 30 days on Starter, forever on Creator and Team.
- **Free tier:** no exports or downloads according to the official comparison table ("—"). A [secondary review](https://www.openshorts.app/alternatives/choppity) by the upstream OpenShorts team says exports carry "a small Choppity logo". The free-tier export rule is therefore **unverified**.
- **Paywalled** ([pricing](https://www.choppity.com/pricing/)):
  - Starter: 1080p and 4K export, scheduling to 1 social account.
  - Creator: custom fonts, 1 brand template, saved brand assets and **API access**.
  - Team: seats, roles, team billing and 5 brand templates.
  - Enterprise: sub-teams, an MSA and white-label.
- Choppity is unusual in putting **4K on its entry paid plan**.

### quso.ai (formerly vidyo.ai)
- **Two plan sets are live** (the help centre says "some accounts see monthly credit plans or one-time credit packs"):
  - **The public pricing page** sells credit plans billed yearly: 150 credits for $7/mo ($84/yr), 400 for $15/mo, 1,000 for $25/mo and 2,500 for $49/mo. "Every plan has all features", and yearly billing is 50% off. A Black Friday banner on the page offered 50% off yearly plans until Dec 1 ([pricing](https://quso.ai/pricing)).
  - **The help centre** lists **Free** (75 credits/mo), **Lite** $29/mo (100 credits), **Essential** $39/mo (300) and **Growth** $49/mo (600, up to 1,800) ([subscription plans](https://quso.ai/help/subscription-plans)).
  - 1 credit = 1 minute.
- **Free tier:** 75 credits/mo, 720p with a watermark, projects kept 7 days, TikTok publishing (25 posts/mo), and "CutMagic" on the first 3 videos ([help](https://quso.ai/help/subscription-plans); [llms-full](https://quso.ai/llms-full.txt)).
- **Headline features:**
  - AI clips from YouTube links or uploads;
  - caption styles;
  - a brand kit on every plan;
  - reframing to 9:16, 1:1 and 16:9;
  - subtitles in 99 languages (with dedicated Hindi, Urdu and Malayalam pages);
  - a scheduler, content planner and analytics;
  - filler-word removal, "Cutmagic", a B-roll library and a hook generator;
  - an **MCP server** ([pricing](https://quso.ai/pricing) product list).
- **Paywalled:** watermark removal and 1080p from Lite. Publishing beyond TikTok needs Essential or Growth ([help](https://quso.ai/help/subscription-plans)).

### 2short.ai
- **Plans** ([pricing](https://2short.ai/pricing)):
  - **Starter**: free, 30 min of analysis/mo. The page's own footer says 15 min, so the figure is inconsistent.
  - **Lite**: $9.90/mo, 5 h.
  - **Pro**: $19.90/mo, 15 h, unlimited fast exports.
  - **Premium**: $49.90/mo, 50 h, priority support and beta access.
  - Annual pricing: **unverified** (none shown).
- **Free tier:** "full access to all features". The marketing copy says exports are watermark-free and 1080p ([pricing](https://2short.ai/pricing)). Whether free exports are watermark-free is **unverified**.
- **Headline features:** face tracking, one-click animated subtitles, vertical, square and horizontal output, brand presets (logos and overlays), and Google Drive and URL import on Lite and above. YouTube videos need captions to be processed ([pricing](https://2short.ai/pricing)).
- **Paywalled:** only volume, fast server-side export, URL and Drive import, and ad removal. No API, scheduling or dubbing is advertised.

### SendShort (sendshort.ai)
- **Plans** ([pricing](https://sendshort.ai/pricing/)):
  - **Starter**: $15/mo or $12/mo yearly, 20 shorts, 90 s max.
  - **Professional**: $29/mo or $18/mo yearly, 50 shorts, 3 min.
  - **Business**: $59/mo or $35/mo yearly, unlimited (fair use), 10 min.
  - No free trial; refunds within 24 hours.
- **Headline features:** captions in 100+ languages, TikTok slideshows, faceless videos from a prompt, music videos, AI avatar and photo-to-video, a scheduler for TikTok and YouTube, a content calendar, unlimited social accounts, an "AI Agent for Claude, ChatGPT and Grok" plus an API, and "Automated Series" ([pricing](https://sendshort.ai/pricing/)).
- **Paywalled** ([pricing](https://sendshort.ai/pricing/)):
  - **Long-video-to-shorts itself starts at Professional**, as do:
    - the AI hook title, auto B-roll, and cutting silences with noise reduction;
    - AI voice-over and auto-translated captions;
    - your own fonts and media;
    - the API and AI agents;
    - 2K export.
  - Business adds:
    - **4K/60fps**;
    - aspect-ratio conversion;
    - unlimited themes;
    - green-screen export;
    - an analytics dashboard;
    - automatic publishing;
    - a priority queue.

### StreamLadder (streamladder.com)
- **Plans** ([pricing](https://www.streamladder.com/pricing)):
  - **Free** $0.
  - **Starter**: $15/mo or $150/yr.
  - **Creator**: $27/mo or $270/yr.
  - **Pro**: $39/mo or $390/yr.
  - Yearly billing gives "2 months free". Every paid plan has a 7-day trial (card required).
  - **No credits or minute caps**: ClipGPT is "unlimited within fair use".
- **Free tier:** the basic clip editor with default layouts, 720p/30fps, **no watermark on basic edits**. Using paid features (captions, stickers) adds a watermark. Uploads up to 200 MB ([pricing](https://www.streamladder.com/pricing)).
- **Headline features:** a gaming and streaming focus, with Twitch and Kick VOD import by link, facecam detection and framing, custom layouts, Twitch emotes, social reactions, text-to-speech, AI word censoring, an AI hook intro title, AI silence removal, a montage maker, and an emote maker and schedule maker ([pricing](https://www.streamladder.com/pricing)).
- **Paywalled** ([pricing](https://www.streamladder.com/pricing)):
  - Starter: the full editor (captions, effects), 1080p/60fps, and posting to TikTok, YouTube, Instagram and Facebook.
  - **Creator ($27): AI clipping (ClipGPT)**, up to 30 clips per stream, and Twitch and Kick import by link.
  - Pro: 4K/60fps, a team workspace (2 editors) and posting to X.
  - The tier of AI hook titles and silence removal: **unverified** (checkmarks did not render).

### Descript (descript.com)
- **Plans:**
  - **Free** $0: 1 media hour/mo and 100 AI credits once.
  - **Hobbyist**: $24/mo or $16/mo yearly, 10 h, 400 AI credits.
  - **Creator**: $35/mo or $24/mo yearly, 30 h, 800 credits.
  - **Business**: $65/mo or $50/mo yearly, 40 h, 1,500 credits.
  - Enterprise: custom.
  - Yearly billing saves "up to 35%". The yearly prices are on the official page ([pricing](https://www.descript.com/pricing)); the monthly prices come from [diffio, 2026-11-10](https://diffio.ai/descript-pricing/) and [I4U](https://i4u.business/en/cyber-monday/descript/).
- **Free tier:** watermarked, 720p export ([pricing](https://www.descript.com/pricing) comparison).
- **Headline features:** text-based editing, the Underlord AI co-editor, "Create Clips" (Underlord picks "viral-worthy moments"), Remove Filler Words, Edit for Clarity, Studio Sound, AI Speech with voice clones, detection of 8+ speakers, caption translation into 61 languages, and dubbing into 30 languages including Hindi ([pricing](https://www.descript.com/pricing)).
- **Paywalled** ([pricing](https://www.descript.com/pricing)):
  - Hobbyist: watermark-free 1080p.
  - Creator: **4K**, the stock library and generative video.
  - **Business: translation and dubbing**, a team-wide Brand Studio, custom avatars and an SLA.

### CapCut (capcut.com)
- **Plans** ([pricing](https://www.capcut.com/pricing)):
  - **Free** $0.
  - **Pro**: $19.99/mo, 1,200 AI credits, 1 TB.
  - **Ultra**: $79/mo, 8,645 credits.
  - **Teams**: $12.49/seat/mo, with a brand kit.
  - Pro yearly is $179.99/yr according to [Posteady, 2026-11-16](https://www.posteady.com/blog/capcut-long-video-to-shorts) (secondary).
  - 7-day Pro trial, varying by region ([pricing](https://www.capcut.com/pricing)).
- **Long video to shorts:** the AI picks moments from "changes in visuals, audio, and context", with clips up to 3 minutes and captions. The desktop app gives 60 free minutes/mo, and Pro adds 240. Sources must be under 3 h and 10 GB. In a US test on 2026-11-16 the web version was **region-blocked** ([Posteady](https://www.posteady.com/blog/capcut-long-video-to-shorts), secondary).
- **Paywalled:** premium templates, "premium Pro features", AI credits and the brand kit (Teams). The pricing page is generic, and the per-feature paywall is **unverified**.

### Riverside Magic Clips (riverside.com)
- **Plans** ([pricing](https://riverside.com/pricing)):
  - **Free** $0.
  - **Pro**: $35/mo or $24/mo yearly ($288).
  - **Grow**: $45/mo or $34/mo yearly ($408).
  - **Webinar**: $99/mo or $79/mo yearly ($948).
  - **Business**: contact sales.
  - The page itself carried a "staging environment" notice. A [Keymo snapshot](https://usekeymo.com/alternatives/riverside-magic-clips) saw monthly prices of $29 and $39 instead, so the monthly figures are **unverified**.
- **Free tier:** Magic Clips included, 720p, "Riverside watermark on all your things", and 2 h of multitrack recording ([pricing](https://riverside.com/pricing)).
- **Headline features:** a recording studio first. Clipping features are Magic Clips, Magic Hooks, Magic Segments, Magic Episode, the AI Co-Creator agent, filler and silence removal, eye contact, AI B-roll, animated clips, VideoDub, smart layouts and AI thumbnails ([pricing](https://riverside.com/pricing)). Magic Clips makes about 2 clips per 5 minutes of conversation, each 30–90 s ([Keymo](https://usekeymo.com/alternatives/riverside-magic-clips), citing the help centre).
- **Paywalled** ([pricing](https://riverside.com/pricing)):
  - Pro: no watermark, 4K, personalization of Magic Clips, and AI B-roll, eye contact and filler removal.
  - Grow: social scheduling, AI thumbnails and the **Riverside MCP**.
  - AI translation, AI B-roll, animated clips and VideoDub draw on AI credits (Pro starts with 400).
  - Magic Clips itself uses no credits.

---

## 2. Feature-by-competitor matrix

Legend:
- **F** = available on the free tier (often with a watermark);
- **P** = paid only (the lowest paid tier unless a tier is named);
- **H** = higher paid tier only (the tier is named);
- **—** = not offered or not advertised;
- **?** = unverified.

| Feature | OpusClip | Vizard | Klap | Submagic | Captions | Munch Studio | Choppity | quso | 2short | SendShort | StreamLadder | Descript | CapCut | Riverside |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Long-to-short AI clipping | F | F | P (trial preview) | P (5/mo Starter) | H (Max) | P | F | F | F | H (Professional) | H (Creator) | F (credits) | F (60 min) | F |
| Virality / score | P (Starter) | ? | P | ? | ? | ? | ? | ? | — | ? | — | — | — | — |
| Animated captions | F (watermark) | F | P | P | F (1 template) | ? | F | F | F | P | P (Starter) | F | F | F |
| Auto emoji / keyword highlight | F | ? | ? | ? | ? | ? | ? | ? | ? | ? | ? | ? | ? | ? |
| Auto reframe / face tracking | F | F | P | ? | ? | ? | F | F | F | ? | H (Creator, facecam) | ? | F | F (smart layouts) |
| Multi-speaker / dynamic layout / screenshare | F | ? | P (active speaker) | ? | ? | ? | ? | ? | F (centre speaker) | ? | F (layouts) | P (8+ speaker detection) | ? | F |
| Hook generation (title/intro) | F (auto hook) | ? | P | ? (AI hook title) | ? | ? | ? | P (generator) | — | H (Professional) | ? | — | — | P (Magic Hooks) |
| AI B-roll | P (stock/image); H Pro (AI video) | ? | P | H (Pro, Storyblocks) | H (Max) | — | ? | ? | — | H (Professional) | — | H (Creator, gen video) | P (credits) | P (credits) |
| Filler / silence removal | P (Starter) | ? | ? | H (Pro) | ? | — | ? | ? | — | H (Professional) | ? | P | ? | P (Pro) |
| AI voiceover / TTS | P (20/day) | ? | ? | ? | H (Max) | ? | ? | ? | — | H (Professional) | ? | P | P | P |
| Dubbing / translation | H (Pro, dubbing) | P (subtitle translation) | ? | ? | H (Max, + lipdub) | ? | ? | ? | — | H (Professional, captions) | — | H (Business, dubbing) | ? | P (credits) |
| Brand kit / templates | F (1 template) | H (Business) | ? | H (Pro) | ? | P | H (Creator) | F | F (brand presets) | H (Professional, fonts) | — | H (Business, Brand Studio) | H (Teams) | — (custom branding: Business) |
| Scheduling / auto-post | P (posting); ? scheduler | P (Creator, 6 accounts) | P | H (Pro) | — | P | P (Starter) | F (TikTok only) | — | P | P (Starter) | ? | ? | H (Grow) |
| Analytics | H (Business) | — | P | H (Pro) | — | P | H (Team, usage) | P | — | H (Business) | — | — | — | P (podcast) |
| Team seats | H (Pro, 2–4) | H (Business, per seat) | H (Pro+) | per member | P (2–3 seats) | H (Premium) | H (Team) | H (Growth) | — | H (Business) | H (Pro, 2 editors) | H (Creator/Business) | H (Teams) | P |
| API | H (Pro) | F (rate-limited) | P (separate pay-per-use) | H (Business 100 min; others 10 min) | — | — | H (Creator) | ? | — | H (Professional) | — | ? | — | H (Business) |
| MCP / AI-agent connector | H (Pro) | F (listed) | — | ? | — | — | — | F/P (?) | — | H (Professional) | — | — | — | H (Grow) |
| Long uploads (≥3 h) | P (10–30 GB) | P (10 h) | P (3 h) | F (3 h source) | ? | ? | ? | ? | ? | ? | F (VODs, fair use) | ? | F (<3 h) | ? |
| 4K export | H (Business) | P (Creator) | ? | H (Business) | ? | — | P (Starter) | — (1080p max) | — (1080p) | H (Business) | H (Pro) | H (Creator) | ? | P (Pro) |
| Watermark-free export | P | P | P | P | P | P | P | P | F? | P | F (basic edits) | P | ? | P |

Sources for the matrix are the vendor pages cited in section 1. The "?" cells reflect checkmark icons that did not render in the text extraction, or features the vendor does not mention.

---

## 3. Features commonly paid-only

Ranked by how often I found a feature behind a paywall across the 14 tools.

1. **Watermark-free export.** It is paid on 12 of 14 tools. The exceptions are StreamLadder (basic edits only) and possibly 2short ([StreamLadder](https://www.streamladder.com/pricing), [2short](https://2short.ai/pricing)). Removing the watermark is the single most universal upgrade trigger.
2. **4K export.** It sits on the top or second-top tier at OpusClip (Business), Submagic, SendShort and StreamLadder, and on Descript Creator. Only Vizard and Choppity give 4K on their entry paid tier ([Vizard](https://vizard.ai/pricing), [Choppity](https://www.choppity.com/pricing/)).
3. **Scheduling and auto-posting to social.** It is paid everywhere it exists, and the number of connected accounts is a lever between tiers (Vizard 6→20, Choppity 1→3→6). quso is the exception, with free TikTok posting ([quso help](https://quso.ai/help/subscription-plans)).
4. **AI B-roll.** It is a mid or upper tier feature. Generative or "AI video" B-roll sits even higher (OpusClip Pro, Descript Creator, Captions Max, Riverside credits).
5. **Dubbing and translation.** It is usually the top self-serve tier or metered by credits: Descript Business, OpusClip Pro, Captions Max (with lip-dub) and Riverside credits.
6. **Brand kit, custom fonts and templates.** These are mid or upper tier at Vizard Business, Submagic Pro, Choppity Creator, OpusClip Pro (4 templates) and Descript Business.
7. **API and MCP access.** These are mid or upper tier at OpusClip Pro, Choppity Creator, SendShort Professional, Submagic Business (100 min) and Riverside Grow (MCP). They are increasingly marketed as "AI agent" connectors for Claude and ChatGPT.
8. **Filler-word and silence removal, bad-take removal, eye contact.** These are "Pro" editing features at OpusClip, Submagic, SendShort and Riverside.
9. **Team seats and workspaces.** These are always the top self-serve tier.
10. **Analytics.** These are usually top tier (OpusClip Business, SendShort Business, Submagic Pro). Klap includes analytics on every plan.
11. **Virality score.** It is paid at OpusClip (Starter+) and included in every Klap plan. Most other vendors don't feature it on their pricing pages.
12. **Clipping itself.** At SendShort (Professional), StreamLadder (Creator), Captions (Max) and Klap (any paid plan), **long-to-short clipping is the premium feature**, while captioning and editing are the cheaper base.

## 4. Unusual or differentiating features

- **Klap prices per clip, not per minute.** Source length is free up to 3 h, every plan has the same features, and it sells a separate pay-per-use API at $0.32 per short ([Klap](https://klap.app/pricing)).
- **StreamLadder has no credits.** Clipping is "unlimited within fair use", and the product is built around Twitch and Kick VODs, facecam detection, Twitch emotes, an emote maker and a schedule maker ([StreamLadder](https://www.streamladder.com/pricing)).
- **OpusClip offers a "genre-specific reframing model"** and **prompt-to-clip / topic search**, plus Premiere Pro and DaVinci export and auto-import from a verified YouTube channel ([OpusClip](https://www.opus.pro/pricing)).
- **Agent-style editors.** Vizard Agent with selectable model tiers, Submagic "Iris", Descript Underlord, Captions' chat editor and Riverside Co-Creator all sell chat-driven editing, with the model tier as a pricing lever (Vizard: Flash free; Pro, Max and Ultra paid) ([Vizard](https://vizard.ai/pricing)).
- **MCP connectors are now a premium checkbox:** OpusClip Pro, Vizard, quso, Riverside Grow, and SendShort's "AI Agent for Claude, ChatGPT and Grok" ([OpusClip](https://www.opus.pro/pricing), [quso](https://quso.ai/pricing), [Riverside](https://riverside.com/pricing), [SendShort](https://sendshort.ai/pricing/)).
- **Captions offers AI Lipdub, AI twins and Reddit-to-Reel,** pushing toward generated content rather than clipping ([Captions](https://captions.ai/pricing)).
- **SendShort mixes clipping with "faceless" content generation:** prompt videos, TikTok slideshows, music videos and "Automated Series" ([SendShort](https://sendshort.ai/pricing/)).
- **Munch pivoted away from pure clipping** into an AI social-media manager that trains on your business, priced $38–$318/mo ([Munch Studio](https://www.munchstudio.com/why-munch-studio)). The pivot is a signal that standalone clipping is commoditising.
- **Riverside makes clipping a by-product of recording.** Magic Clips uses no credits. Magic Hooks and Magic Segments are bundled with recording, hosting and webinars ([Riverside](https://riverside.com/pricing)).
- **Indian-language support:** quso has dedicated Hindi, Urdu and Malayalam subtitle pages ([quso](https://quso.ai/pricing)), Descript dubs into Hindi ([Descript](https://www.descript.com/pricing)), and Captions reportedly lists Hinglish (**unverified**, secondary: [Marxx](https://marxx.ai/prices/captions-app-pricing)). None of these advertises Hinglish copy or hook generation.
- **Not seen in any competitor** (absence is **unverified**, judged from pricing pages only):
  - a self-hosted or open-source edition;
  - local-LLM moment picking;
  - a Telegram bot interface;
  - zero-cost operation.

## 5. Pricing patterns

- **Billing units:**
  - Minutes of source video ("credits"): OpusClip, Vizard, quso, Descript (media hours), 2short (analysis hours), Choppity (analysis hours) and Munch (repurposing minutes).
  - Output clips: Klap (clips) and SendShort (shorts).
  - A mixed credit pool: Submagic (upload 3, Magic Clips 8) and Captions (credits for generative AI).
  - Unmetered: StreamLadder (fair use).
- **Tier count:** a free tier or trial, then 2–3 self-serve paid tiers, then custom or enterprise. Tier names converge on Starter, Pro (Creator) and Business (Team).
- **Typical price points (monthly billing, entry → top self-serve):**
  - Entry: **$10–$29/mo**. Examples: 2short $9.90, Captions Basic $9.99, OpusClip, SendShort and StreamLadder $15, Submagic $19, CapCut $19.99, Descript and Choppity $24, Klap and Vizard $29.
  - Mid tier ("Pro"): **$27–$45/mo**.
  - Top self-serve tier: **$49–$99/mo**, or $189–$445 for volume tiers (Klap Pro+, Vizard 6,200 credits). Munch Studio's multi-brand plans reach $398.
- **Annual discount:** usually **30–50%**. Vizard, Klap and OpusClip Pro are 50% off; Submagic up to 41%; SendShort up to 40%; Descript up to 35%; Choppity 30%; StreamLadder about 17% ("2 months free"). Headline prices are usually shown as the annual-billed monthly equivalent.
- **Effective cost per source hour** is roughly $0.80–$4.30. Examples: Descript Creator yearly $0.80/h ([diffio](https://diffio.ai/descript-pricing/)), Vizard $1.43–$4.31/h ([NoobClaw](https://noobclaw.com/blog/vizard-ai-pricing/)), OpusClip about 5–10¢/min ([askgpu](https://askgpu.com/opus-clip-pricing/)).
- **Free tiers** are trials in practice: 15–75 minutes or credits, a watermark, 720p, and 3–7 day storage. Klap and Choppity don't allow exports on free; Submagic's credits are one-time.
- **APIs** sell per minute or per item: Submagic about $0.10–$0.23/min, and Klap $0.32 per short plus $0.44 per input video.

---

## Sources

Official pricing and help pages, read 2026-11-22 unless noted:
- https://www.opus.pro/pricing
- https://vizard.ai/pricing
- https://klap.app/pricing
- https://www.submagic.co/pricing
- https://care.submagic.co/en/article/how-much-does-it-cost-to-use-submagic-1xm83pa/
- https://captions.ai/pricing
- https://captions.ai/help/docs/subscriptions
- https://captions.ai/help/mirage/account-management/mirage-billing
- https://www.munchstudio.com/pricing (redirected from getmunch.com/pricing)
- https://www.munchstudio.com/why-munch-studio
- https://www.choppity.com/pricing/
- https://quso.ai/pricing
- https://quso.ai/help/subscription-plans
- https://quso.ai/llms-full.txt
- https://2short.ai/pricing
- https://sendshort.ai/pricing/
- https://www.streamladder.com/pricing
- https://www.descript.com/pricing
- https://www.capcut.com/pricing
- https://riverside.com/pricing

Dated third-party snapshots, used where official pages render prices with JavaScript or omit them:
- https://askgpu.com/opus-clip-pricing/ (2026-10-31)
- https://noobclaw.com/blog/vizard-ai-pricing/ (2026-11-21)
- https://whathetech.net/ai-compare/tools/vizard (2026-11-07)
- https://diffio.ai/descript-pricing/ (checked 2026-11-10)
- https://i4u.business/en/cyber-monday/descript/ (2026-11-21)
- https://saashunter.si/tools/choppity/pricing
- https://www.openshorts.app/alternatives/choppity (2026-10-30; written by the upstream OpenShorts team, so not independent)
- https://marxx.ai/prices/captions-app-pricing (2026-11-03)
- https://www.storycut.com/alternatives/captions-ai (2026-10-03)
- https://www.posteady.com/blog/capcut-long-video-to-shorts (2026-11-16)
- https://usekeymo.com/alternatives/riverside-magic-clips (2026-10-11)
