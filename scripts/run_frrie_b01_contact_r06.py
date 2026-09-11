"""Module entry point for the frozen FRRIE contact-active R128 LR003 R06 object."""

import sys

from experiments.candidates.finite_resource_relational_inductive_efficiency.b01_contact_r02 import main


if __name__ == "__main__":
    raise SystemExit(main(["--lr003", *sys.argv[1:]]))
