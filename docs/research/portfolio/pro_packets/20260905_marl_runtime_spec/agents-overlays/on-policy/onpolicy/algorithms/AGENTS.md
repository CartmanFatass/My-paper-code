# Local HMASD navigation overlay

`r_mappo/` contains the recurrent/non-recurrent MAPPO policy and trainer used by the standard
shared and separated runners. `algorithms/utils/` contains tensor conversion, MLP/CNN, GRU, and
action-distribution layers. HAPPO/HATRPO/MAT are neighboring variants and are outside the core
MAPPO path summarized here. Source is read-only; this is local additive navigation.
