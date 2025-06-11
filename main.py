#!/usr/bin/env python3
import argparse
from scouts.vhs_berlin import VHSBerlinScout


def main():
    parser = argparse.ArgumentParser(description='Scout-Bot - Automated availability checker')
    subparsers = parser.add_subparsers(dest='command', required=True)

    # VHS Berlin command
    vhs_parser = subparsers.add_parser('vhs-berlin', help='Check VHS Berlin course availability')

    args = parser.parse_args()

    if args.command == 'vhs-berlin':
        scout = VHSBerlinScout()
        scout.run()


if __name__ == '__main__':
    main()