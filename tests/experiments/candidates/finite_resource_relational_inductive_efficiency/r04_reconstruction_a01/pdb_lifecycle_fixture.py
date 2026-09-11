import sys
print("BODY_ENTERED", flush=True)
print("TRACE", sys.gettrace(), flush=True)
if sys.argv[1] == "exception":
    raise RuntimeError("BOUNDARY_TOY")
raise SystemExit(0)
