# Parser design

## Configuration and determinism

`ParserConfig` controls the locale hint, default IANA timezone, default duration, 100,000-character input ceiling, and 50-event ceiling. Every parse call requires one aware `reference` datetime. Relative date calculation converts that one value to the candidate timezone; it never reads the system clock internally.

## Supported expressions

* Dates: `2026-10-22`, `2026年10月22日`, `9月24日`, `October 22, 2026`, and `22 October 2026`.
* Relative dates: `今日`, `明日`, `明後日`, `今週金曜日`, `来週の水曜日`, `today`, `tomorrow`, `this Friday`, and `next Wednesday`.
* Times: `午後3時`, `15時30分`, `3 PM`, `3:30 PM`, `noon`, and `midnight`.
* Ranges/durations: `14時から16時`, `from 2 PM to 4 PM`, `1時間半`, `30分`, and `for 90 minutes`.
* Timezones: `Asia/Tokyo`, `Asia/Bangkok`, `UTC`, `GMT`, `JST`, and numeric offsets such as `UTC-05:00`.
* Multiple events: newline/sentence-separated clauses with separate date markers become candidates with distinct source spans.

An end time at or before the start is interpreted as crossing midnight. Zone-aware datetimes retain their source timezone, so UTC is never silently relabeled as local time and `zoneinfo` applies applicable daylight-saving rules. When no timezone appears, the configured assumption is included in `ambiguity_warnings` and the preview.

## Extraction and safety

Parsing proceeds through bounded normalization, candidate segmentation, date/time/timezone extraction, title cleanup, validation, and exact-span de-duplication. Original candidate text is retained in both `description` and `source_text`. Invalid calendar dates, invalid clocks, missing fields, and ambiguous bare weekdays cannot auto-create an event. A default one-hour end is shown for editing but forces review. An explicit duration is considered user-provided.

## Limitations

The parser intentionally does not guess vague phrases such as “evening,” geographic timezone names, locations, recurrence, or dates without a recognizable marker. English numeric dates are omitted because day/month order is unsafe without a stronger locale contract. Month/day dates without a year infer the next non-past occurrence and require review. Natural-language clauses that contain several dates without sentence separators may need manual review. DST nonexistent or repeated wall times are represented according to `zoneinfo`; the preview should be checked at transition boundaries.
