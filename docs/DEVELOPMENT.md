\# Development Story



Calendar Hotkey started as a very small personal automation project.



The original goal was simple:



> Copy schedule text, press `Ctrl + Alt + G`, and create a Google Calendar event.



The project was intentionally built as a small prototype first instead of trying to design a complete scheduling system from the beginning.



\---



\## Stage 1 — Japanese-Only Prototype



The original plan was to support Japanese only.



Most schedules I encountered in everyday life were written in Japanese, so expressions such as:



```text

9月24日 14時から15時

```



```text

明日の18時

```



```text

来週の水曜日

```



seemed sufficient for the first prototype.



The first workflow was:



```text

Clipboard

&#x20;   ↓

Ctrl + Alt + G

&#x20;   ↓

AutoHotkey

&#x20;   ↓

Python

&#x20;   ↓

Google Calendar Quick Add

```



The goal was not sophisticated parsing.



The goal was to test whether calendar creation could be made meaningfully faster with a keyboard shortcut.



The prototype worked and validated the basic idea.



\---



\## Stage 2 — Problems with Real Messages



The prototype worked well for short input such as:



```text

9月24日 14:00-15:00 ミーティング

```



However, real messages were often much longer:



```text

お世話になっております。



次回のお打ち合わせですが、

9月24日の14時から15時でお願いいたします。



場所は新宿オフィスです。

よろしくお願いいたします。

```



Passing an entire message directly to Google Calendar Quick Add did not always produce predictable structured events.



This revealed an important design problem:



> The application should understand the structure of the event before writing it to the calendar.



Parsing was therefore moved into the local Python application.



The application began extracting:



```text

title

date

start time

end time

location

description

```



before creating the Google Calendar event.



\---



\## Stage 3 — Adding a Review UI



Once Calendar Hotkey started interpreting text itself, incorrect parsing became more important.



Automatically inserting a wrongly interpreted event into the calendar would be inconvenient.



A review window was therefore added.



The workflow became:



```text

Copy

&#x20;   ↓

Ctrl + Alt + G

&#x20;   ↓

Parse

&#x20;   ↓

Review

&#x20;   ↓

Add

```



The user could inspect and edit:



\- title

\- date

\- start time

\- end time

\- location

\- description



before insertion.



This improved safety.



\---



\## Stage 4 — The Japanese-Only Assumption Broke



At first, I intended to keep the project Japanese-only.



That assumption changed when I considered the schedules I actually wanted to capture.



Many important deadlines came from:



\- programming competitions

\- hackathons

\- Kaggle-style competitions

\- international developer programs

\- global technical events



These were frequently written in English.



For example:



```text

Submission deadline: Oct 19, 2026 11:55 PM JST

```



or:



```text

Final submission due 19 Oct 2026, 11:59 PM AoE

```



At that point, a Japanese-only parser no longer matched the real use case.



English support was added.



\---



\## Stage 5 — Bilingual Date Parsing



The parser was expanded to understand formats such as:



```text

October 19, 2026

Oct 19, 2026

19 Oct 2026

2026-10-19

10月19日

```



Japanese relative dates were also supported:



```text

今日

明日

明後日

来週の水曜日

再来週の金曜日

```



English relative expressions were added as well:



```text

today

tomorrow

day after tomorrow

next Friday

this Wednesday

```



The project had evolved from a Japanese utility into a bilingual scheduling tool.



\---



\## Stage 6 — International Time Zones



English competition support introduced another problem: timezone conversion.



For example:



```text

Oct 19, 2026 11:59 PM UTC

```



must not be stored as:



```text

Oct 19 23:59 JST

```



It needs to become:



```text

Oct 20 08:59 JST

```



Competition platforms may also use:



```text

AoE

```



which means:



```text

Anywhere on Earth

UTC-12

```



Timezone support was therefore added for explicit formats such as:



```text

JST

UTC

GMT

AoE

PST

PDT

MST

MDT

CST

CDT

EST

EDT

CET

CEST

BST

```



Times are normalized to JST before insertion.



The original source text remains in the event description so the source can be checked later.



\---



\## Stage 7 — Avoiding Silent Timezone Guessing



Consider:



```text

Submission deadline: Oct 19, 2026 11:59 PM

```



The date and time are explicit.



The timezone is not.



Automatically assuming JST, UTC, or AoE could cause a serious deadline error.



For competition deadlines, missing timezone information is therefore treated as ambiguous.



The application asks for confirmation rather than silently guessing.



This follows a general rule:



> Missing information that can materially change a deadline should not be silently guessed.



\---



\## Stage 8 — The Confirmation Problem



The review UI improved safety, but requiring confirmation for every event became annoying.



For example:



```text

NEDO Baggage-Loading Robot 2

Submission deadline: Oct 19, 2026 11:55 PM JST

```



already contains:



```text

event context

date

time

timezone

deadline type

```



Requiring another click for every clearly formatted event worked against the original goal of reducing repetitive work.



\---



\## Stage 9 — Selective Confirmation



The final design uses a hybrid approach.



Explicit events are automatically added.



For example:



```text

Submission deadline: Oct 19, 2026 11:55 PM JST

```



can go directly to Google Calendar.



Ambiguous input still opens the review window.



For example:



```text

Submission deadline: Oct 19, 2026

```



has no time.



```text

Submission deadline: Oct 19, 2026 11:59 PM

```



has no timezone.



```text

Meeting next Friday evening

```



contains an imprecise time.



The final flow is:



```text

Copied text

&#x20;   ↓

Local parser

&#x20;   ↓

Safe to auto-add?

&#x20;  /            \\

&#x20;Yes            No

&#x20; ↓              ↓

Auto-add      Review UI

&#x20;  \\            /

&#x20;   \\          /

&#x20;    Google Calendar

```



This restores the speed of the original prototype while keeping the safety improvements added later.



\---



\## Stage 10 — No LLM API



Using an LLM for event extraction was considered.



It would make arbitrary natural-language parsing easier.



However, the project has a deliberate constraint:



> It should not require a paid AI API or an additional AI API key.



The final parser therefore runs locally using deterministic rules.



Advantages:



\- zero per-request LLM cost

\- no LLM API key

\- predictable parsing behavior

\- no schedule text sent to an AI provider

\- easier debugging

\- explicit handling of ambiguous input



The limitation is that the parser cannot understand arbitrary natural language as well as an LLM.



Instead of pretending otherwise, Calendar Hotkey falls back to manual review when necessary.



\---



\## Development Summary



The project evolved roughly like this:



```text

Japanese-only idea

&#x20;       ↓

Quick Add prototype

&#x20;       ↓

Real-world testing

&#x20;       ↓

Long-form parsing problem

&#x20;       ↓

Structured local parser

&#x20;       ↓

Review UI

&#x20;       ↓

English competition use case

&#x20;       ↓

Bilingual parsing

&#x20;       ↓

UTC / AoE support

&#x20;       ↓

Timezone safety rules

&#x20;       ↓

Mandatory confirmation became inconvenient

&#x20;       ↓

Selective confirmation

```



The final design was not fully planned in advance.



It emerged through repeated use, identifying friction, and improving the workflow.



\---



\## Current Design Principle



Calendar Hotkey follows one simple rule:



> If the information is clear, automate it.

> If the information is ambiguous, ask the user.
