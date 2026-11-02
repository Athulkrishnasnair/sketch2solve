# Phase A evaluation methodology

## Targets and scope

This evaluation concerns image-pixel structural joint centers and member centerlines in a selected truss region. It does not label loads, supports, dimensions, or units. The detector's endpoint clusters remain visual candidates; they are not asserted to be physical joints.

Only reference elements with `status: "confirmed"` enter calculations. `ambiguous` and `unobservable` annotations are retained for review but excluded. `test2.jpg` has no selected, trustworthy single graph and receives no metrics.

## Matching rules fixed before the reported metrics

- **Joint match:** one-to-one maximum-cardinality matching between predicted endpoint-cluster centroids and confirmed reference joints. A pair is eligible when Euclidean distance is at most `max(12 px, 0.75% of image diagonal)`. Matching is restricted to the hand-selected `evaluation_roi`. Each prediction and each reference can contribute to at most one true positive.
- **Joint precision/recall:** `TP / predicted candidate clusters in ROI` and `TP / confirmed reference joints`. This evaluates endpoint-cluster candidates; candidate clutter in the selected region counts as false positive.
- **Endpoint localization error:** mean and median Euclidean distance for the one-to-one matched joint pairs, in source-image pixels.
- **Member coverage recall:** a confirmed reference member is recovered if the union of candidate segments covers at least 80% of its centerline. Eligible candidate fragments must be within `max(12 px, 0.75% of image diagonal)` perpendicular distance and within 8 degrees of the reference orientation. Candidate projections are clipped to the reference segment and overlapping intervals are unioned, so multiple fragments cannot count the same reference member more than once.
- **Member precision:** unavailable for this detector. It emits ungrouped `CandidateLine` segments and does not predict member objects or member/non-member semantics. A future member precision/recall evaluation requires a separately specified, annotation-independent line-to-member grouping stage, then one-to-one matching of its member hypotheses to confirmed reference centerlines. Raw segment counts must not be presented as member precision.
- **Aggregate:** micro-average joint precision/recall and member coverage recall over images with confirmed graphs only. It is descriptive for this five-image set and is not an estimate of general performance.

The 12 px floor matches the detector's configured endpoint-clustering scale. The 0.75% diagonal term allows the matching corridor to grow for large source rasters. The 8-degree orientation and 80% coverage thresholds are fixed evaluation criteria, not detector tuning parameters.

## Annotation and uncertainty

Annotations are bound to source image SHA-256 and use original decoded pixels, top-left origin, x right, y down. Reference nodes and member centerlines were placed by visual review independently of detector output. Ambiguous X-brace crossing connectivity in `test5.png` is not made into a joint. Dotted construction geometry in `test1.jpg` is not included as a member. Text, supports, and load arrows are outside this reference target and can contribute candidate clutter when they fall inside the selected ROI.

All scores are exploratory. Annotation placement is approximate, especially on the photographed `test1.jpg` and compressed textbook `test5.png`; no expert adjudication or duplicate-annotator agreement is available.
