# Phase A reference annotation format

Each `annotations/testN.json` file is a human-authored reference, stored separately from the detector baseline and overlays. Source images are read-only. `source_sha256` binds an annotation to the exact image bytes.

Coordinates are floating point pixel positions in the original decoded raster: origin at the top-left, x increases right, y increases down. `width` and `height` must match the decoded source. No EXIF rotation, scale conversion, physical coordinate, or unit conversion is applied. A member is a straight centerline segment between two annotated node IDs.

Each joint, member, ambiguous region, and unobservable region has a `status`:

- `confirmed`: clear enough in source pixels for the stated annotation scope.
- `ambiguous`: evidence exists but multiple structural readings remain plausible; `reason` is required.
- `unobservable`: the relevant content cannot be assessed from the raster; `reason` is required.

The schema only labels structural joint centers and member centerlines for the selected truss region. Loads, supports, dimensions, and units are out of scope even if drawn; this avoids treating visual/printed engineering annotations as model truth. `evaluation_roi` selects the reviewed diagram region and is `[x_min, y_min, x_max, y_max]` in the same image coordinates. Images without a trustworthy reference graph carry no confirmed joints or members and are excluded from numeric metrics.

Annotation references were placed by visual review of the source images, independently of detector output. Detector overlays are retained in the sibling `detector-baseline/` directory and were not used to create reference points.
