# AIUC-1 -> OWASP ASI: v1 (expert hand-crafted) vs v2 (pipeline) comparison

v1 is the 119-pair hand-crafted crosswalk shipped with the upstream AIUC-2 repository. v2 is the current production output of the multi-signal hybrid mapping engine. This report diffs the two at pair-level, tier-level, and signal-level, and documents the gaps.

## Summary counts

| metric | value |
|---|---:|
| v1 pairs | 119 |
| v2 pairs | 109 |
| preserved (in both) | 57 (47.9%) |
| tier preserved too | 57 |
| tier changed | 0 |
| lost from v1 | 62 (52.1%) |
| new in v2 | 52 |

## Tier distribution

| tier | v1 | v2 |
|---|---:|---:|
| Direct | 55 | 98 |
| Related | 64 | 11 |

## Tier changes (preserved pairs whose tier moved)

_None._

## Lost pairs (in v1 expert set, not produced by v2)

| control | risk | v1 tier | v1 rationale |
|---|---|---|---|
| A003 | ASI09 | Related | SCOPE |
| A004 | ASI01 | Related | SCOPE |
| A004 | ASI02 | Related | SCOPE |
| A004 | ASI03 | Related | SCOPE |
| A004 | ASI04 | Related | SCOPE |
| A005 | ASI06 | Direct | ISOLATE |
| A006 | ASI06 | Related | ISOLATE |
| A007 | ASI02 | Related | SCOPE |
| A007 | ASI03 | Related | SCOPE |
| A007 | ASI04 | Related | SCOPE |
| B001 | ASI05 | Related | VALID |
| B001 | ASI06 | Direct | VALID |
| B001 | ASI10 | Related | VALID |
| B003 | ASI03 | Related | PREV |
| B003 | ASI10 | Related | PREV |
| B004 | ASI09 | Related | PREV |
| B005 | ASI08 | Related | PREV |
| B006 | ASI06 | Related | SCOPE |
| B006 | ASI08 | Related | SCOPE |
| B007 | ASI09 | Related | SCOPE |
| B007 | ASI10 | Related | SCOPE |
| B009 | ASI06 | Related | SCOPE |
| B009 | ASI09 | Related | SCOPE |
| B009 | ASI10 | Related | SCOPE |
| C002 | ASI01 | Related | VALID |
| C002 | ASI05 | Related | VALID |
| C003 | ASI01 | Related | PREV |
| C003 | ASI08 | Related | PREV |
| C004 | ASI01 | Related | PREV |
| C005 | ASI09 | Related | PREV |
| C006 | ASI01 | Related | PREV |
| C006 | ASI09 | Related | PREV |
| C007 | ASI08 | Related | GATE |
| C007 | ASI10 | Related | GATE |
| C008 | ASI10 | Related | DETECT |
| C009 | ASI02 | Related | GATE |
| C009 | ASI08 | Related | GATE |
| C009 | ASI10 | Related | GATE |
| C010 | ASI09 | Direct | VALID |
| C011 | ASI01 | Related | VALID |

_(+22 more in JSON)_

## New pairs (produced by v2, not in v1 expert set)

| control | risk | v2 tier | v2 score |
|---|---|---|---:|
| A003 | ASI01 | Related | 0.566 |
| A003 | ASI03 | Related | 0.529 |
| A003.1 | ASI02 | Direct | 0.251 |
| A003.1 | ASI06 | Direct | 0.295 |
| A004 | ASI07 | Related | 0.575 |
| A004.3 | ASI07 | Direct | 0.336 |
| A005 | ASI03 | Direct | 0.326 |
| A005 | ASI04 | Direct | 0.258 |
| A005 | ASI07 | Direct | 0.560 |
| A005.2 | ASI07 | Direct | 0.315 |
| A005.3 | ASI07 | Direct | 0.304 |
| A006 | ASI03 | Direct | 0.325 |
| A006 | ASI05 | Direct | 0.292 |
| A006 | ASI07 | Direct | 0.376 |
| A006 | ASI10 | Direct | 0.287 |
| B001.1 | ASI07 | Direct | 0.279 |
| B002.1 | ASI07 | Direct | 0.269 |
| B002.2 | ASI07 | Direct | 0.266 |
| B002.3 | ASI07 | Direct | 0.283 |
| B002.4 | ASI07 | Direct | 0.317 |
| B005.4 | ASI01 | Direct | 0.315 |
| B008.3 | ASI03 | Direct | 0.251 |
| B008.3 | ASI04 | Direct | 0.287 |
| B008.3 | ASI07 | Direct | 0.269 |
| C003 | ASI05 | Related | 0.589 |
| C003.3 | ASI07 | Direct | 0.283 |
| C005.2 | ASI01 | Direct | 0.319 |
| C005.3 | ASI01 | Direct | 0.291 |
| C006.3 | ASI07 | Direct | 0.259 |
| C007 | ASI01 | Direct | 0.309 |
| C007.3 | ASI01 | Direct | 0.278 |
| C008 | ASI02 | Direct | 0.253 |
| C009.1 | ASI01 | Direct | 0.273 |
| D001.1 | ASI01 | Direct | 0.315 |
| D002.1 | ASI08 | Direct | 0.364 |
| D002.1 | ASI09 | Direct | 0.327 |
| D003.3 | ASI02 | Direct | 0.330 |
| D004.1 | ASI02 | Direct | 0.339 |
| D004.1 | ASI05 | Direct | 0.317 |
| E001.2 | ASI04 | Direct | 0.257 |

_(+12 more in JSON)_

## Verdict

v2 preserves 47.9% of the v1 expert pairs, loses 62 (52.1%), adds 52 new candidates, and changes tier on 0 of the preserved pairs. By the session 11 rule (regression on >5% flags manual review), this is a **regression**.

The loss set is concentrated on AIUC controls that do not appear in v2's mapped set at all, which typically reflects composite scores below the needs-review band rather than explicit rejection. These are the natural queue for the next active-learning round.

