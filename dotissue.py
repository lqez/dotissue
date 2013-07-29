#!/usr/bin/python
import argparse
import ConfigParser


def cmd_list(args, config):
    print 'list command'


def cmd_config(args, config):
    for section in config.sections():
        for option in config.options(section):
            print section, option, config.get(section, option)


parser = argparse.ArgumentParser(prog='dotissue')
subparsers = parser.add_subparsers(help='sub-command help')

parser_list = subparsers.add_parser('list', help='list all issues')
parser_list.set_defaults(func=cmd_list)

parser_config = subparsers.add_parser('config', help='Get and set options')
parser_config.set_defaults(func=cmd_config)


def main():
    config = ConfigParser.RawConfigParser()
    config.read('.gitsue')

    args = parser.parse_args()
    args.func(args, config)


if __name__ == '__main__':
    main()
