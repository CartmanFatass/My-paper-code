# experiments/

Research candidates live at candidates/<direction-id>/<attempt>/; tests mirror that path
under tests/experiments/candidates/. Run entry is scripts/run_<prefix>_<attempt>.py;
new result artifacts use runs/<direction-id>/<tag>/ at repository root. Scratch may stay in
temp/directions/<direction-id>/; it is not the sole recoverable result store. Shared direction
helpers stay at the candidate root. Frozen runners retain their recorded entry/output paths,
including historical temp paths; record recoverable locations, never move bound artifacts
just to match the new layout.

Core packages must not import candidate code. Existing imports in
 envs/native/production_backend.py are recorded defects, not precedent. Research code
has no compatibility obligation between attempts; frozen inputs retain their version.
Native candidates may own a loader or reuse envs/native/cpp_extension_cache.py; first
use pays PyTorch JIT compilation. Check the object's device/numerical contract before
switching backend. The research-engineering skill owns scope, budgets and checks.
