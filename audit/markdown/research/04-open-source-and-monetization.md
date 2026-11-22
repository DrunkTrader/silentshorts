# 04 — Open-source and self-hosted landscape, and how "premium" gets monetized

Research date: 2026-11-22. Star counts, push dates and prices are as fetched that day; they move fast.
Method: GitHub search and REST API via `gh` (8 query variants plus targeted repo lookups), README reads
(raw, via `gh api .../readme`), Jina reader for pricing and licence pages, Exa search (rate-limited,
used for two queries only), Hacker News Algolia API, Reddit via agent-reach public-web search.
Every fetched page was treated as untrusted data. See "Data-handling notes" at the end.

Not legal advice. Section 4 lists questions for a lawyer, not conclusions.

---

## 1. Open-source alternatives

### 1.1 Overview table

| Project | Stars | Last push | Licence | Shape | Notes |
|---|---|---|---|---|---|
| mutonby/openshorts (upstream) | 9,698 | 2026-11-22 | MIT core + commercial `cloud/` | Docker web app + hosted Cloud | 299 commits in the last 12 weeks [1] |
| modelscope/FunClip | 6,622 | 2026-11-01 | MIT | Gradio app | Chinese-first ASR (Paraformer), text-driven clipping, LLM clipping secondary [2] |
| Anil-matcha/AI-Youtube-Shorts-Generator | 6,469 | 2026-11-21 | MIT | CLI + Python lib | Default mode routes through paid MuAPI; local mode optional [3] |
| FujiwaraChoki/supoclip | 4,058 | 2026-11-22 | SupoClip Noncommercial Source License 1.1 (not OSI) | Docker web app + hosted + iOS | 136 open issues [4] |
| ClipsAI/clipsai | 625 | 2024-01-17 | MIT | Python library | Abandoned (no commit since Jan 2024) [5] |
| ColinGPT9/clips-studio ("Clips Kitty") | 600 | 2026-11-22 | AGPL-3.0-or-later | Windows desktop app (Microsoft Store) | Local Gemma via Ollama; gaming/IRL focus [6] |
| artbyjazi/autoclip | 524 | 2026-08-01 | MIT | Local web app + CLI | Pre-1.0, `autoclip doctor` installer check [7] |
| RafaelGodoyEbert/ViralCutter | 519 | 2026-09-10 | GPL-3.0 | Local tool | Cited on r/selfhosted as the answer to "local Opus Clip" [8][20] |
| NaufalRizqullah/opensource-clipping | 516 | 2026-11-22 | MIT | Web Studio + CLI + Colab/Kaggle notebooks | Most effects-heavy (B-roll, BGM ducking, voice-over) [9] |
| xixihhhh/hotclip | 505 | 2026-11-20 | AGPL-3.0-only | Desktop app | Chinese live-commerce and live-stream slicing [10] |
| Shaarav4795/ClippedAI | 253 | 2026-09-04 | NOASSERTION (custom) | Local script | [11] |
| mehbul/chopify, sherlock-dev-ai/Clipify, Blueturboguy07/publikclip, osbytes/reelsaw, fralapo/clippyme, kleZ799/clipmint, GrepCut/OpenClipper | 24-124 each | Nov 2026 | MIT / AGPL / custom | Mostly new (created Jun-Oct 2026) | Long tail; a new "Opus Clip alternative" appears every few days [12] |

Adjacent, not direct competitors: harry0703/MoneyPrinterTurbo (145,080 stars, MIT) and
FujiwaraChoki/MoneyPrinter (14,238) generate faceless videos from a topic, not clips from a long
source [12]. mifi/lossless-cut (46,323, GPL-2.0) is a manual cutter, but relevant to monetization (2.3).

### 1.2 The five closest alternatives and what they lack

**1. FujiwaraChoki/supoclip — closest feature match, but not open source.**
- Features: YouTube/Twitch/Kick/upload ingest; LLM picks 3-7 clips (Gemini, GPT, Claude or Ollama);
  virality scores; face-tracked 9:16; word-synced captions with templates; hook titles; Pexels B-roll;
  built-in trim/split/merge editor; direct posting to YouTube/TikTok/Instagram; a "performance loop"
  that feeds post analytics back into clip selection; MCP server; REST API with keys [4].
- Gaps: the licence forbids companies, agencies, freelancers working for clients, and teams without
  written permission. It needs an AssemblyAI key by default (local Whisper is a tutorial path, not the
  default). Self-hosting issues include Prisma build failures on fresh Windows Docker installs, jobs
  stuck at 50%, Apple-Silicon Docker builds hanging while pulling CUDA wheels, and AssemblyAI API
  deprecations breaking transcription [13]. Contributors grant a relicensing right (CLA-style) [4].
- What it tells us: SupoClip is the clearest case of the "source-available plus hosted plus app store"
  model in this niche.

**2. Anil-matcha/AI-Youtube-Shorts-Generator — most stars among pure clippers, thin product.**
- Features: CLI and Python library; ranked highlights with score, hook and reason; chunking for
  videos over 30 minutes; dedupe; OpenCV face crop; JSON output for automation [3].
- Gaps: no web UI, no editor, no layouts beyond the face crop, no publishing. The default `--mode api`
  sends everything to MuAPI, a paid API that the README promotes. Issues report YouTube bot-detection
  and 403 errors, MuAPI timeouts, broken CUDA fallback, and weak two-person podcast tracking [13].
- What it tells us: this is the "OSS repo as a funnel for a paid API" model.

**3. ColinGPT9/clips-studio (Clips Kitty) — best desktop UX, Windows-only.**
- Features: local Gemma (Ollama) chosen by VRAM tier; optional cloud through OpenRouter OAuth; webcam
  and game layout picker; word captions; titles, descriptions and hashtags; YouTube publishing;
  plugin API; MCP server; distributed through the Microsoft Store. Claims 38 clips from one video in
  19 minutes on an RTX 3060 [6].
- Gaps: in its own issue tracker, "nobody has ever run Clips Studio on a Mac". Minimum spec is an
  RTX 2060 6 GB, 16 GB RAM and about 20 GB of disk. Users report it running on the integrated GPU
  instead of the dedicated one, Intel GPUs not being detected, Windows file-lock render failures, and
  YouTube "confirm you're not a bot" download failures [6][13]. It has no hosted option and no
  multi-user support. It is explicitly "free, no paid tier", with AGPL on the core.

**4. modelscope/FunClip — strongest ASR stack, weakest "shorts" features.**
- Features: Paraformer, SenseVoice, Fun-ASR-Nano and MOSS backends; hotword customization; speaker
  ID (CAM++); SRT output; LLM clipping; Gradio UI; regular releases (v2.2.1, Sept 2026) [2].
- Gaps: Chinese-first; English needs a separate model flag. No 9:16 reframing, no face tracking, no
  animated captions, no hooks, no publishing. Its roadmap still lists "removing silence periods" [2].

**5. NaufalRizqullah/opensource-clipping — the most effects.**
- Features: faster-whisper large-v3; Gemini, NVIDIA NIM or vLLM curation; MediaPipe auto-framing;
  karaoke ASS captions; kinetic typography; Pexels B-roll; multi-hook intros; BGM ducking;
  thumbnails; a watermark engine; YouTube and Facebook Reels upload; Pyannote podcast split-screen
  and camera switch; AI voice-over [9].
- Gaps: its recommended path is Google Colab or Kaggle notebooks rather than a stable server.
  Split-screen needs a gated Hugging Face Pyannote token. It needs a CUDA GPU. There are no
  accounts, no multi-user support, and no hosted option.

Also worth tracking: artbyjazi/autoclip. Its pitch ("existing open-source clippers stop at 'works
on my machine'") and its `autoclip doctor` preflight check aim straight at the install-pain gap [7].
ClipsAI's reframing used Pyannote diarization, which needed an HF token. The library is now
unmaintained [5].

### 1.3 Where upstream OpenShorts already sits

Upstream already has local LLM support (`LLM_BASE_URL` for Ollama, LM Studio and vLLM), per-scene
TRACK, GENERAL, SPLIT and SCREENCAST layouts, ElevenLabs dubbing, MCP over HTTP and stdio, REST,
webhooks, NVENC, and Upload-Post publishing. Its Cloud runs Free (20 min/mo, watermarked), Starter
$12 (100 min), Creator $29 (300 min) and Pro $59 (750 min), plus one-time top-ups of $9 for 60 min
and $25 for 200 min [1][14]. On breadth it leads the OSS field. The gaps its peers fill better:
- **Desktop installer and app store distribution** (Clips Kitty, HotClip, ClipForge Studio on the
  Microsoft Store [21]). OpenShorts is Docker-only.
- **A preflight or doctor check** (autoclip, HotClip's desktop health check [7][10]).
- **A performance feedback loop** from post analytics into selection (SupoClip [4]).
- **Non-English ASR depth** (FunClip and HotClip for Chinese [2][10]). Our fork's Hindi path
  (`collabora/faster-whisper-small-hindi`) is a differentiator here.

### 1.4 Self-hosting pain points (recurring across trackers and threads)

From the GitHub issue trackers of openshorts, supoclip, AI-Youtube-Shorts-Generator, clips-studio
and clipsai [13], plus Reddit search results [20][21]:
1. **YouTube download breakage**: "Sign in to confirm you're not a bot", HTTP 403, and "Requested
   format is not available". This is the most common failure across every project.
2. **GPU setup**: CUDA not seen inside Docker (WSL2, NixOS, Debian), the integrated GPU chosen over
   the dedicated one, Intel/AMD GPUs unsupported, CPU-only PyTorch pulled by default, CUDA wheels
   downloaded on Apple Silicon.
3. **FFmpeg variants**: builds without libass (macOS Homebrew `ffmpeg` vs `ffmpeg-full`, and Windows
   "Essentials") silently fail to burn captions [7].
4. **Windows paths and permissions**: `mkdir C:\WINDOWS\system32\openshorts\output: Access is denied`
   (openshorts #163), WinError 32 file locks, Prisma build failures.
5. **Long jobs dying**: "No metadata file generated after 20-30 min" (openshorts #31). Users asked
   for checkpoint/resume (openshorts #90), and Reelsaw markets "resumable jobs" as a headline feature.
6. **API-key friction and churn**: users want a no-key local mode (openshorts #17 is the most
   commented issue; supoclip #40 and #36), and upstream API deprecations break pipelines
   (AssemblyAI).
7. **Quality on cheap local models**: autoclip's README warns that "a 7B model returns valid JSON
   full of mediocre picks" [7]. Local-first users accept that trade, but they notice it.

Community reach is thin. Hacker News stories for OpenShorts have 1-2 points and no comments [15],
and one OpenShorts post on r/selfhosted (2026-08-20) was removed by moderators [20]. Self-hosters
find these tools on GitHub and Reddit "looking for" threads, not through launch posts.

---

## 2. How open-source and self-hosted creator and media tools make money

| Model | Example | Concrete terms (as published) |
|---|---|---|
| **Hosted cloud of the same code** | Plausible | CE is AGPL and free. Cloud funds development. CE ships twice a year, lacks funnels, journeys and ecommerce revenue, and has community support only [16a]. Hosted from $9/mo [16b] |
| | Comfy Org (ComfyUI) | Comfy Cloud: Free (5 runs), Standard $20/mo, Creator $35/mo, Pro $100/mo, all credit-based; teams $200-2,500/mo; serverless GPU $1.75-11.23/h [17] |
| | OpenShorts upstream | Cloud $12/29/59 by source minutes, top-ups $9/$25 [14] |
| **Open core + paid self-hosted licence** | n8n (fair-code) | Sustainable Use License: internal business use allowed, resale/hosting for others not. `.ee` code under an Enterprise License. Cloud Starter $20/mo, Pro $50/mo. **Business $800/mo is self-hosted only** and adds SSO/LDAP, environments and Git version control [18a][18b] |
| | Cal.com | AGPL core plus Enterprise Edition. Free, Teams $12/user/mo, Organizations $28/user/mo (SAML SSO, SCIM), Enterprise on request [19] |
| | PhotoPrism | Community free. Essentials €2/mo, Plus from €6/mo, as a "Plus License" unlocking features in the same self-hosted binary [22] |
| | Sidekiq | Pro/Enterprise as paid self-hosted gems (page not readable on fetch, so no price cited) |
| **Paid licence, no feature gate (goodwill key)** | Immich | Lifetime keys: Server $100, Individual $25. Explicitly grants no extra features [23a][23b] |
| **Model packs / data subscription** | Frigate+ (Frigate NVR) | $50/yr. Models trained on user-submitted camera images, 12 fine-tunes a year, $5 per extra fine-tune. Models stay usable after cancelling [24] |
| **Convenience service subscription** | Nabu Casa (Home Assistant) | $6.50/mo or $65/yr for remote access, cloud backups, voice assistants and support [25] |
| | Plex Pass | $2.99/mo or $29.99/yr (proprietary, but the self-hosted-media benchmark) [26] |
| **Paid binaries / app store, free source** | LosslessCut | GPL on GitHub. Paid in the Mac App Store and Microsoft Store, sold as "secure and simple installation with automatic, stable updates" [27] |
| | Ardour | Source is free, but "you'll need to build this yourself… we can't support the end result". The ready-to-run builds are the product [28] |
| | Upscayl | Free OSS desktop app plus a paid "Upscayl Cloud" (batch, face enhancement, storage) [29] |
| **Usage-based commercial licence for embedders** | Remotion | Free for individuals and companies of up to 3 people. Creators $25/seat/mo. **Automators $0.01/render, $100/mo minimum.** Enterprise from $500/mo [30] |
| **Source-available, noncommercial** | SupoClip | Free for individual creators. Companies, agencies and teams need written permission. Hosted web and iOS app on top [4] |
| **OSS as an API funnel** | AI-Youtube-Shorts-Generator | Default mode uses MuAPI (paid). The README is partly an ad for the "AI Clipping API" [3] |
| **Sponsorship / donations** | LosslessCut, most clippers | GitHub Sponsors or donation buttons. No public evidence that these fund full-time work in this niche |

Patterns:
- **Self-hosters pay for convenience, data or rights, not for code.** Plausible, Nabu Casa,
  LosslessCut, Ardour and Frigate+ all keep the code free and sell what self-hosting cannot give:
  uptime, signed binaries, auto-updates, trained models, remote access.
- **Feature-gated self-hosted licences work when the buyer is a business** (n8n, Cal.com,
  PhotoPrism Plus). They sell SSO, SCIM, environments, Git and audit features that individuals do
  not miss.
- **Pure goodwill (Immich) needs a large, loyal user base.** That is plausible for a photo library,
  less so for a creator tool used weekly.

---

## 3. Which "premium" features self-hosters actually pay for

Ranked by how often a comparable product charges for the feature, and how often users report
pain without it:

1. **Zero-friction install and updates**: signed desktop builds, a store listing, a one-click
   GPU setup and a doctor check. Evidence: LosslessCut and Ardour sell this exact thing [27][28];
   Clips Kitty and HotClip lead with installers [6][10]; GPU, FFmpeg and Windows-path failures top
   the issue trackers (1.4).
2. **Cloud GPU bursts / hosted processing for users without a GPU.** Evidence: Comfy Cloud credits
   [17], Upscayl Cloud [29], and the CPU vs GPU speed table in upstream's own README (5-8 min vs about
   50 s per 8-min video) [1]. Clips Kitty's OpenRouter fallback shows users accept BYOK cloud when
   their PC is too slow [6].
3. **A working downloader that keeps working** (proxies, cookies, maintenance against YouTube
   bot checks). This is the most common failure (1.4). It is a service, not code, and a natural
   subscription. Note the CLAUDE.md proxy rules and the ToS risk; see section 4.
4. **Model packs / tuned selection**: better clip-picking prompts or fine-tuned local models,
   language packs (Hindi ASR plus Hinglish copy), and caption and hook template packs. Evidence:
   Frigate+ sells exactly "better models than the public ones" for $50/yr [24]. Users note that local
   7B picks are mediocre [7], so a tuned small model is real value.
5. **Publishing and automation**: scheduled multi-platform posting, Autopilot, and the analytics
   feedback loop. Evidence: upstream gates Autopilot to Cloud [14]; SupoClip's performance loop [4];
   Opus Clip gates multi-profile posting and team workspaces to higher tiers [31].
6. **Multi-user, teams, brand kits, SSO/audit**: only for agencies, but they are the segment that
   pays per seat (Cal.com $12-28/user [19], n8n Business $800/mo self-hosted [18a]). SupoClip's
   licence carves out companies and agencies as the paying segment [4].
7. **Priority support / SLA**: Plausible CE is explicitly "community supported only" [16a].
   Support sells only alongside one of the items above.

Weak sellers: watermark removal on self-hosted (every OSS rival promises "no watermark ever", so it
would read as a betrayal), unlimited minutes on self-hosted (same), and donations alone.

### Three best-fit models for a self-hosted clipping tool

1. **Free MIT core plus hosted Cloud, with GPU bursts from the self-hosted UI.** Self-hosters press
   "render on cloud" for one job and pay per source minute. Examples: Plausible [16a], Comfy Cloud
   credits [17], upstream OpenShorts Cloud and top-ups [14].
2. **Paid "Pro" convenience edition: signed desktop installer, auto-updates, doctor/GPU setup,
   maintained downloader.** The source stays open. Examples: LosslessCut store builds [27], Ardour
   binaries [28], Nabu Casa-style yearly convenience subscription [25].
3. **Model and preset packs as an annual subscription**: tuned clip-picker model, Hindi/Indic
   language pack, caption/hook template packs. Older packs stay usable after the subscription
   ends. Example: Frigate+ at $50/yr [24].

Option for later: an agency/team licence (SSO, seats, brand kits) on the n8n/Cal.com model [18][19],
only once there is evidence of agency demand.

---

## 4. Licensing considerations (flags for a lawyer, not legal advice)

**F1. Upstream `cloud/` is under the OpenShorts Commercial License, not MIT.** In this fork it lives
at `silentshorts/cloud/` (see `NOTICE`). The licence allows personal and internal self-hosting, but
forbids, without a written agreement: offering it or derivatives as a hosted, paid or white-label
service; selling or redistributing it for a fee; and removing billing or metering functionality
when providing access to third parties. Contributions to that folder grant the upstream holder
commercial rights. → **A paid hosted or premium edition cannot include or derive from `cloud/`**
without a licence from upstream. Questions for counsel: is a clean-room rewrite needed, and what
counts as "derivative" for code that has been read? Should `cloud/` be removed from distributions
entirely? Note also that upstream runs a competing hosted service, and the licence names
"competes with the hosted service at openshorts.app".

**F2. MIT core: attribution only.** Keep the MIT copyright notice in every distribution, including
desktop installers, Docker images and app-store builds. Low risk, easy to miss in binary builds.

**F3. Ultralytics YOLOv8 is AGPL-3.0, and this repo depends on it.** `requirements.txt` pins
`ultralytics==8.4.46` and the pipeline loads `yolov8n.pt` (`silentshorts/pipeline/main.py`).
Ultralytics states that AGPL fits only if "you are comfortable open-sourcing your entire project
under AGPL-3.0", and sells an Enterprise License for SaaS and embedded products [32]. → **This is
probably the biggest licensing flag for any closed or premium edition**, and it also affects the
"MIT" claim for the combined work. Options to discuss: an Ultralytics Enterprise License; replacing
YOLO with an Apache/MIT detector (MediaPipe is Apache-2.0 and already a dependency [33]); or
licensing the premium edition under AGPL. The AGPL network clause matters for hosted use.

**F4. `collabora/faster-whisper-small-hindi` is CC-BY-4.0** [34]. CC-BY permits commercial use and
redistribution with attribution: credit Collabora, link the licence, and indicate changes. Our
`docs/architecture/hindi.md` already records the attribution. Points for counsel:
- Attribution must appear wherever the model is redistributed: bundled in a desktop installer, a
  model pack or a Docker image. Today it is "fetched by repo id on first use", which is lower risk.
- The model card lists training data that includes **snow-mountain (CC BY-SA 4.0)** and **yodas
  (CC BY 3.0)** alongside CC BY 4.0, CC0 and Apache sets. Does share-alike on training data reach
  the weights? This is unsettled, so ask counsel [34].
- The card's "Intended Use" says it is "suitable for academic use". That is descriptive, not a
  restriction, but worth confirming.
- The base model, openai/whisper-small, is Apache-2.0 [34].

**F5. Gemma.** The repo's Hindi path targets Gemma 3 on Ollama (`docs/architecture/hindi.md`,
`tests/test_hindi_llm.py`). The Hugging Face card for Gemma 3 says `license: gemma` (gated) [35].
The Gemma Terms of Use require, for any Distribution, which includes making it available "as a
hosted service via API, web access, or any other electronic or remote means":
- passing the Prohibited Use Policy through as an enforceable term in your own ToS/EULA;
- giving recipients a copy of the terms;
- a NOTICE file ("Gemma is provided under and subject to the Gemma Terms of Use…") for non-hosted
  distributions;
- marking modified files.
Google may also "restrict (remotely or otherwise) usage" it believes violates the terms. Google
claims no rights in outputs [36]. → If a premium edition **bundles Gemma weights** (a model pack or
installer) or **serves Gemma from a hosted cloud**, the ToS and NOTICE pass-through apply. Note:
the Hugging Face cards for the **Gemma 4** family (e.g. `google/gemma-4-E4B-it`) list
**apache-2.0** [35]. If that holds, moving to Gemma 4 would remove most of these obligations.
Verify with counsel and on Google's own Gemma 4 page before relying on it.

**F6. Other dependencies to inventory before selling binaries.**
- FFmpeg: the Dockerfile installs the Debian package, which is a GPL build with x264.
  Distributing images or installers carries GPL source-offer duties.
- yt-dlp: Unlicense [33]. But **the YouTube ToS risk of a paid product built on downloading** is a
  business and legal question of its own, separate from code licensing.
- MediaPipe: Apache-2.0. faster-whisper: MIT [33].
- If CUDA runtime libraries are redistributed (osrender, the GPU image), the NVIDIA EULA
  redistribution terms apply.
- Third-party API terms for resale: Gemini (paid vs free-tier data use), ElevenLabs and Upload-Post.
  BYOK keeps the user as the API customer; bundling keys makes us the reseller.

**F7. Competitor licence choices to know.** SupoClip (noncommercial source-available) and Clips
Kitty and HotClip (AGPL) are copyleft or restrictive: their code cannot be pulled into an MIT or
proprietary edition. The MIT projects (Anil-matcha, autoclip, opensource-clipping, FunClip) can be
reused with attribution, subject to their own dependencies (several also use YOLO, Pyannote or
other gated models).

**F8. Public-repo hygiene** (CLAUDE.md): pricing experiments, revenue targets and customer data
for a premium edition must not land in this public repository.

---

## Data-handling notes

- Nothing was starred, forked, filed, posted or logged into. Reddit thread pages returned "blocked
  by network security", so only the search-result snippets (titles, post bodies, top-comment
  excerpts) were used, and those threads' comments are not quoted. Exa hit its free rate limit
  after the first batch.
- **Agent-directed content seen and not followed:** the HotClip README contains a block meant to be
  pasted into Claude Code or Codex to install it as a local skill (`git clone …`) [10]. Several
  READMEs (Clips Kitty, HotClip) ask readers to star the repo. The AI-Youtube-Shorts-Generator
  README is partly promotion for MuAPI's paid API [3]. All were treated as data.
- Gaps: no Sidekiq price (page not readable); LosslessCut store prices not fetched; Ardour's
  pay-what-you-want amounts not shown on the fetched page; GitHub Sponsors income is not public.
  Plausible's own comparison page quotes Starter at $19 for 100k pageviews; the $9 entry price is
  for 10k pageviews [16b].

## Sources

1. mutonby/openshorts, repo API and README — https://github.com/mutonby/openshorts
2. modelscope/FunClip README — https://github.com/modelscope/FunClip
3. Anil-matcha/AI-Youtube-Shorts-Generator README — https://github.com/Anil-matcha/AI-Youtube-Shorts-Generator
4. FujiwaraChoki/supoclip README and licence FAQ — https://github.com/FujiwaraChoki/supoclip
5. ClipsAI/clipsai README; last commit 2024-01-17 — https://github.com/ClipsAI/clipsai
6. ColinGPT9/clips-studio README (requirements, licence, store) — https://github.com/ColinGPT9/clips-studio
7. artbyjazi/autoclip README — https://github.com/artbyjazi/autoclip
8. RafaelGodoyEbert/ViralCutter — https://github.com/RafaelGodoyEbert/ViralCutter
9. NaufalRizqullah/opensource-clipping README — https://github.com/NaufalRizqullah/opensource-clipping
10. xixihhhh/hotclip README — https://github.com/xixihhhh/hotclip
11. Shaarav4795/ClippedAI — https://github.com/Shaarav4795/ClippedAI
12. GitHub search, `gh search repos` for "opus clip alternative", "youtube shorts generator", "ai video clipper", "opusclip", "video to shorts", "podcast clips", "auto clip video" (2026-11-22)
13. Issue trackers: openshorts #17 #18 #29 #31 #90 #92 #163; supoclip #5 #11 #36 #40 #58 #75 #425; AI-Youtube-Shorts-Generator #7 #55 #56 #60 #69 #81; clips-studio #62 #74 #112 #136 #223 #227
14. OpenShorts pricing — https://openshorts.app/pricing
15. Hacker News (Algolia) — https://news.ycombinator.com/item?id=50455209, https://news.ycombinator.com/item?id=47300951
16a. Plausible, self-hosted vs Cloud — https://plausible.io/self-hosted-web-analytics
16b. Plausible pricing references — https://plausible.io/plausible-umami-fathom-simple-analytics ; https://deployopen.com/comparisons/learning-and-marketing/plausible/plausible-community-edition-vs-plausible-cloud
17. Comfy Cloud pricing — https://comfy.org/pricing/
18a. n8n pricing — https://n8n.io/pricing/
18b. n8n Sustainable Use License — https://docs.n8n.io/sustainable-use-license/
19. Cal.com pricing — https://cal.com/pricing ; AGPL + EE — https://cal.com/blog/changing-to-agplv3-and-introducing-enterprise-edition
20. Reddit r/selfhosted search results (snippets only): /r/selfhosted/comments/1h8dzh6, /1pamfgd, /1lw8l6l, /1978hnq, /1w3vn9v, /1vtk53o (removed by moderator)
21. Reddit r/windowsapps ClipForge Studio (/1wd26yn); r/SideProject Reelsaw (/1x9yr1h), SupoClip launch (/1mc1snh); r/LocalLLaMA (/1q2ywzj)
22. PhotoPrism editions — https://www.photoprism.app/editions
23a. Buy Immich — https://buy.immich.app
23b. Immich product keys — https://immich.app/blog/immich-product-keys
24. Frigate+ — https://frigate.video/plus/ ; launch discussion with the $50/yr price — https://github.com/blakeblackshear/frigate/discussions/7932
25. Nabu Casa pricing — https://www.nabucasa.com/pricing/
26. Plex Pass — https://www.plex.tv/plex-pass/
27. LosslessCut README — https://github.com/mifi/lossless-cut
28. Ardour download — https://community.ardour.org/download
29. Upscayl — https://upscayl.org/
30. Remotion licence pricing — https://www.remotion.dev/docs/license/pricing
31. Opus Clip pricing — https://www.opus.pro/pricing
32. Ultralytics licence — https://www.ultralytics.com/license ; repo licence AGPL-3.0 — https://github.com/ultralytics/ultralytics
33. Licences via GitHub API: google-ai-edge/mediapipe (Apache-2.0), SYSTRAN/faster-whisper (MIT), yt-dlp/yt-dlp (Unlicense)
34. Hugging Face: collabora/faster-whisper-small-hindi, collabora/whisper-small-hindi (model card, dataset table), openai/whisper-small
35. Hugging Face API: google/gemma-3-12b-it (`license: gemma`, gated), google/gemma-4-E4B-it (`license: apache-2.0`)
36. Gemma Terms of Use — https://ai.google.dev/gemma/terms
