import os
import sys

if not __package__:
    package_source_path = os.path.dirname(os.path.dirname(__file__))
    sys.path.insert(0, package_source_path)

def main():
    from termtask.cli import cli
    cli()

if __name__ == "__main__":
    main()
