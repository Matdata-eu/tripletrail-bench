# SHACL validation suite

The ERA RINF shapes on RINF data, in three profiles (`suites/shacl/run_shacl.py`): `core` is SHACL Core only, `era-local` leaves out the shapes ERA marks as global, `era` is the shapes as published. Time is the whole command (median of 3 runs when under 300 s), validation is the engine's own validation time where it logs one. Same results compares the sorted result keys (focus node, path, constraint component, severity) with TopBraid's and with the majority's; results shows the distinct keys too when an engine gives several results with one key.
