# Milan-shaped parser fixture - NOT REAL DATA

Every file in this directory was authored for this repository to exercise the
`uav_service_restoration_v0` Milan parser. None of it is a Telecom Italia record, none of
the activity values are measured, and no value here should ever appear in a result.

What each file is for:

- `grid_small.geojson` - four square cells with WGS84 longitude/latitude rings and a
  `cellId` property, shaped like the Milano Grid so the GeoJSON reader and the UTM
  projection can be tested.
- `activity_2013-11-01.txt` - a complete training day: 6 ten-minute intervals, 4 cells,
  two country codes per `(cell, interval)` so country-code summation is testable.
- `activity_2013-11-02.txt` - a test day with one **blank** activity field
  (cell 2, interval 1) and one **absent row** (cell 3, interval 4), so "empty field" and
  "missing row" can be shown to be recorded separately and neither becomes a zero.
- `preprocess_small.json` - the ingestion configuration for these files, with the two
  days assigned to disjoint splits by complete UTC date.

The real ingestion path is the same code; only the data differs. A real-sample validation
is a separate, explicitly reported step.
