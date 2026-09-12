# RCLE B07 reference failure — independent review

Reviewer /root/dm_a_mx_rcle_intake/review_a_h_rcle_b07, Astra/high, read-only.
No tests, native execution, model/RNG, remote query or edit by reviewer.

The traceback confirms the alignment failure, but there is no recorded lane,
tick or differing lengths. Source inspection finds no demonstrated mutation,
expired ctypes storage or caller/self snapshot divergence. NativeBatch retains
its current raw array and allocates fresh outputs; inspected native functions
read const snapshot pointers. Error JSON truncation ("alig" vs "align") has no
identified source rule and is insufficient to diagnose corruption.

Current20-line addition/7-line deletion source diff has no material finding.
True remains the legacy default throughout; B04's legacy reference call/output
remain, while only B07 opts into existing eager immutable tuple conversion.
Native raw storage/action kernel, RNG/comparator, learned path and update are
unchanged. Alignment rejection remains; failure context is more specific.
The focused tests cover representation/ownership, routing and output defaults.
DM reports8 initial passes, then2 after a fixture-only AST location repair.
No §4 machinery or material scope-budget concern is introduced.

Eager conversion is credible, not a proven cure. Native actions still use raw
snapshots; successful reference completion is not established. Invocation-budget
reconciliation remains with Root; this review creates no new invocation.

Diagnosis command-wall samples total1.7708398s
(.2319571,.2849649,.2825452,.2276738,.2482555,.2585298,.2369135).
Actual implemented-diff review command wall.3162084s. No other timing is invented.
