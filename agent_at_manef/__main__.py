"""Brand-aligned CLI with the same versioned behavior as agent_ssot."""
import sys
from agent_ssot import __main__ as legacy_cli


def main(argv=None):
    return legacy_cli.main(argv)


if __name__ == "__main__":
    sys.exit(main())
