import argparse

from . import run


def setup_parser():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    for module in [run, ]:
        name = module.__name__.split('.')[-1]
        module_parser = subparsers.add_parser(
            name, description=module.__doc__)
        module.init_parser(module_parser)
        module_parser.set_defaults(main=module.main)

    return parser


def main():
    parser = setup_parser()
    args = parser.parse_args()
    args.main(args)
