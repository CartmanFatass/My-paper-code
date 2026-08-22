# Assignment: <human title>

```toml hmasd-assignment
schema_version = 2
assignment_id = "asg_<stable-id>"
assignment_mode = "IMPLEMENTATION"
semantic_owner = "CM:<scope>"
executor_role = "hmasd-implementer"
return_to = "CM:<scope>"
strictness_profile = "R1_ROUTINE_ENGINEERING"
evidence_class = "B"
result_bearing = false
runtime_profile = ""
requirement_ids = []
nonrequirement_ids = []
recovery_owner = "CM:<scope>"
result_path = "docs/project/current-work/results/RESULT_<id>.md"
project_map_anchor = "<exact PROJECT_MAP heading>"
architecture_role = "ENTRYPOINT"
affected_files = ["<repo-relative path>"]
create_files = []
affected_symbols = ["<symbol>"]
search_roots = []
direct_consumers = ["<repo-relative consumer>"]
upstream_inputs = ["<repo-relative input>"]
state_owner = "<symbol or owner>"
non_target_surfaces = ["<explicit exclusion>"]
```

## Outcome

State one observable behavior and its direct consumer.

## Allowed actions

<bounded actions>

## Prohibited actions

<scope/authority exclusions>

## Local completion boundary

<what ends this assignment>
