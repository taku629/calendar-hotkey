\# Changelog



All notable changes to Calendar Hotkey will be documented in this file.



The project went through several prototype iterations before its first public Git repository commit.



Those iterations are recorded below as development milestones rather than published releases.



\---



\## Unreleased



\### Added



\- Windows global hotkey using AutoHotkey v2

\- `Ctrl + Alt + G` clipboard-to-calendar workflow

\- Google Calendar OAuth authentication

\- Structured event creation using the Google Calendar API

\- Japanese date parsing

\- English date parsing

\- Japanese relative date support

\- English relative date support

\- Competition deadline detection

\- UTC and JST handling

\- AoE (Anywhere on Earth) support

\- Common US and European timezone abbreviations

\- Automatic conversion to JST

\- Duplicate event detection

\- Tkinter review UI

\- Selective confirmation

\- Automatic insertion for explicit events

\- Review fallback for ambiguous input

\- Local deterministic parsing without an LLM API



\---



\## Pre-Publication Development Milestones



\### Initial Prototype



The first prototype connected:



```text

Clipboard

→ AutoHotkey

→ Python

→ Google Calendar Quick Add

```



The goal was to validate whether Calendar event creation could be reduced to a single keyboard shortcut.



\### Local Structured Parsing



Quick Add was replaced with local parsing after testing the prototype with long-form Japanese messages.



The application began extracting structured event information before calling Google Calendar.



\### Review UI



A confirmation window was added so parsed event information could be inspected and edited before insertion.



\### English Support



The parser was expanded from Japanese-only input to English after competition, hackathon, and international program deadlines became important use cases.



\### International Deadline Support



Timezone parsing and conversion were added for international competition deadlines, including UTC and AoE.



\### Selective Confirmation



Mandatory confirmation for every event was replaced with a hybrid model:



```text

explicit event → auto-add

ambiguous event → review

```



This restored the speed of the original prototype while preserving the safety checks introduced in later iterations.
