# Test-first verification

The baseline was mstack `c0e658d`. A fresh Codex agent received the Notes
search bug and the working-tree delivery skill, with no expected fix, reference
test, or grading criteria. The disposable fixture was at `fbdca68`.

| Observation | Result |
| --- | --- |
| Test-first ordering | The agent added repository tests, confirmed an empty product diff, and ran the suite. Two assertions failed on the original CLI and two preservation cases passed. |
| Candidate | The same four tests passed after changing the query and title comparison. The agent used native unittest discovery. |
| Independent replay | A separate checkout at `3397847` reproduced both failures with the original CLI and all four passes with the candidate CLI. The scripted grader independently recorded the named mixed-case assertion failing and passing, then ran the native suite. |
| Design only | A second fresh agent received a storage-change design request with unavailable staging access. It referenced the existing search test, specified a partial-write assertion and an on-demand staging case, and left the inspected fixture unchanged. |

The task workspaces were isolated temporary directories. The original test
output was retained under
`$TMPDIR/mstack-notes-delivery-ahe2uqqx/artifacts/`. The replay repository was
`$TMPDIR/mstack-notes-replay-aqioi7h7/submission`. The enduring grader and
fixture can be rerun without either temporary directory:

```sh
python3 -m unittest discover -s tests -p test_notes_verification.py -v
```

Delivery used skill digests `ebe96e81122b` (deliver), `96427d23f249` (plan),
and `9e4efd484bcd` (implement). The design instructions were shortened after
that trial. The separate design-only trial used `6002bd45bc92`.
These are individual behavioral trials. Model identifiers were not exposed.

Two initial Method tests failed on the old controller because it accepted
unrelated CLI output and completed implementation without a baseline. Review
also reproduced skipped or misidentified cases, replay of a saved TAP transcript,
misattributed JUnit source, missing candidate test files, stale baseline evidence,
and Git text normalization. Regression tests exercise those paths through the
controller and its runner adapters. A native Node test run produced JUnit
evidence for the same named assertion failing on the baseline and passing
on the candidate. The independent retests used disposable
tasks and an isolated verifier checkout. A local dashboard smoke test rendered
the selected test and evidence links from an actual task fixture.
