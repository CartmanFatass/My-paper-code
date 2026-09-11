"""Module entry point for the frozen FRRIE R08 role-column cut object."""

import sys

from experiments.candidates.finite_resource_relational_inductive_efficiency.b01_contact_r02 import main


if __name__ == "__main__":
    raise SystemExit(main([*sys.argv[1:], "--seed", "1", "--lr003", "--role-column-cut"]))
