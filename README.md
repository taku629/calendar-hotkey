\# Calendar Hotkey



Turn copied schedule text into Google Calendar events with a single keyboard shortcut.



\*\*Copy → Ctrl + Alt + G → Google Calendar\*\*



Calendar Hotkey is a lightweight Windows automation tool that extracts dates, times, deadlines, and event information from Japanese and English text.



It started as a small Japanese-only prototype using Google Calendar Quick Add, then evolved through real-world use to support long-form messages, English competition deadlines, timezone conversion, duplicate detection, and selective confirmation.



No LLM API or paid AI service is required.



\---



\## Why I Built This



I frequently find schedules and deadlines in:



\- emails

\- competition pages

\- hackathon announcements

\- university messages

\- Slack or Discord messages

\- developer program pages



The normal workflow was:



```text

Find a deadline

&#x20;   ↓

Open Google Calendar

&#x20;   ↓

Create an event

&#x20;   ↓

Enter the title

&#x20;   ↓

Enter the date and time

&#x20;   ↓

Convert UTC / AoE to JST if necessary

&#x20;   ↓

Save

```



I wanted to reduce that to:



```text

Copy

&#x20;   ↓

Ctrl + Alt + G

&#x20;   ↓

Done

```



\---



\## Features



\- Japanese schedule parsing

\- English schedule parsing

\- Japanese relative dates

\- English relative dates

\- Competition deadline detection

\- UTC / GMT / JST support

\- AoE (Anywhere on Earth) support

\- Common US and European timezone abbreviations

\- Automatic conversion to JST

\- Duplicate detection

\- Automatic insertion for explicit events

\- Review UI for ambiguous events

\- Google Calendar OAuth authentication

\- No paid AI API

\- No LLM API key



\---



\## Example



Copy:



```text

NEDO Baggage-Loading Robot 2

Submission deadline: Oct 19, 2026 11:55 PM JST

```



Then press:



```text

Ctrl + Alt + G

```



Because the date, time, timezone, and event type are explicit, the event can be added automatically.



For ambiguous input such as:



```text

Final submission deadline: Oct 19, 2026

```



Calendar Hotkey opens a review window instead of silently guessing missing information.



\---



\## Japanese Examples



```text

9月24日 14時から15時 ミーティング

```



```text

明日の18時から面談

```



```text

来週の水曜日 14時から15時 打ち合わせ

```



\---



\## English Examples



```text

Meeting Sep 25 2:00 PM - 3:00 PM

```



```text

Submission deadline: Oct 19, 2026 11:55 PM JST

```



```text

Final submission due 19 Oct 2026, 11:59 PM AoE

```



```text

Final submission deadline: Oct 19, 2026 11:59 PM UTC

```



\---



\## Selective Confirmation



Calendar Hotkey uses a hybrid workflow.



```text

Copied text

&#x20;   ↓

Local parser

&#x20;   ↓

Is the event unambiguous?

&#x20;   ↓

&#x20;┌───────┴────────┐

&#x20;Yes              No

&#x20;↓                ↓

Auto-add       Review UI

&#x20;↓                ↓

Google Calendar

```



Clear input can be added automatically:



```text

Submission deadline: Oct 19, 2026 11:55 PM JST

```



Ambiguous input requires confirmation:



```text

Competition deadline: Oct 19, 2026 11:59 PM

```



The example above contains a date and time, but no timezone. For an international competition deadline, silently guessing the timezone could create a serious error.



\---



\## Why No LLM API?



An LLM would make arbitrary natural-language extraction easier.



However, this project is intentionally designed to work without paid AI APIs or additional AI API keys.



Instead, Calendar Hotkey uses deterministic local parsing.



Benefits:



\- no per-request AI cost

\- no LLM API key

\- schedule text is not sent to an AI provider

\- predictable parsing behavior

\- ambiguous cases are explicitly reviewed



The core design principle is:



> If the information is clear, automate it.

> If the information is ambiguous, ask the user.



\---



\## Architecture



```text

Clipboard

&#x20;   ↓

AutoHotkey v2

&#x20;   ↓

Python

&#x20;   ↓

Local date/time parser

&#x20;   ↓

Timezone normalization

&#x20;   ↓

Safety classification

&#x20;   ↓

Google Calendar API

```



See \[Architecture](docs/ARCHITECTURE.md) for more details.



\---



\## Requirements



\- Windows 10 or Windows 11

\- Python 3

\- AutoHotkey v2

\- Google account

\- Google Calendar API OAuth credentials



Install Python dependencies:



```powershell

py -m pip install -r requirements.txt

```



\---



\## Google Calendar Setup



1\. Create a Google Cloud project.

2\. Enable the Google Calendar API.

3\. Create an OAuth client using the `Desktop app` application type.

4\. Download the OAuth credentials.

5\. Save the downloaded file in the project directory as:



```text

credentials.json

```



6\. Authenticate:



```powershell

py .\\add\_calendar.py --auth

```



After successful authentication, the application creates:



```text

token.json

```



Both files contain authentication information and must not be committed to Git.



They are excluded by `.gitignore`.



\---



\## Usage



Start:



```text

calendar\_hotkey.ahk

```



Then:



```text

1\. Select schedule text

2\. Press Ctrl + C

3\. Press Ctrl + Alt + G

```



If the event is explicit enough, it is added automatically.



If important information is ambiguous, a review window appears.



\---



\## Security



The following files must never be committed:



```text

credentials.json

token.json

.env

```



The repository's `.gitignore` excludes them.



Never publish Google OAuth credentials or access tokens.



\---



\## Development Story



Calendar Hotkey was not designed with all of its current features from the beginning.



It started as a Japanese-only Quick Add prototype and evolved after problems were discovered through actual use.



See \[Development Story](docs/DEVELOPMENT.md).



\---



\## Project Status



Calendar Hotkey is currently a personal productivity project and is still evolving.



The parser is deterministic rather than a full natural-language understanding system, so unusual or highly ambiguous expressions may require manual review.
