import argparse
import sys
import ConfigParser
from time import timezone

from dulwich.errors import NotGitRepository
from dulwich.repo import Repo
from dulwich.objects import Blob, Tree


DI_BRANCH = 'dotissue'
DI_ISSUES = 'issues'
DI_LABELS = 'labels'


def get_branch_list(repo):
    return [repo[len('refs/heads/'):] for repo in repo.get_refs().iterkeys() if repo.startswith('refs/heads/')]


def cmd_init(args, config):
    try:
        repo = Repo(args.path)
    except NotGitRepository:
        sys.exit('It does not look like a valid repository.')

    if DI_BRANCH in get_branch_list(repo):
        sys.exit('Already initialized.')

    object_store = repo.object_store

    # Initialize with README.md
    tree = Tree()

    blob = Blob.from_string("This is a branch for dotissue.\n")
    tree.add("README.md", 0100644, blob.id)
    object_store.add_object(blob)

    blob = Blob.from_string("This is a directory for issues.\n")
    tree.add("%s/README.md" % DI_ISSUES, 0100644, blob.id)
    object_store.add_object(blob)

    blob = Blob.from_string("This is a directory for labels.\n")
    tree.add("%s/README.md" % DI_LABELS, 0100644, blob.id)
    object_store.add_object(blob)

    object_store.add_object(tree)
    commit = repo.do_commit("Initial commit",
                            commit_timezone=-timezone,
                            tree=tree.id,
                            ref='refs/heads/%s' % DI_BRANCH)

    print 'Initialized by %s. :^D' % commit
    sys.exit(0)


def cmd_new(args, config):
    print 'new command'


def cmd_list(args, config):
    print 'list command'


def cmd_help(args, config):
    print 'help command'


def cmd_config(args, config):
    for section in config.sections():
        for option in config.options(section):
            print section, option, config.get(section, option)

parser = argparse.ArgumentParser(prog='dotissue')
subparsers = parser.add_subparsers(help='sub-command help')

parser_init = subparsers.add_parser('init', help='Initialize dotissue on exist repo')
parser_init.add_argument('--path', default='.', metavar='path', type=str, help='Path of the repository to be initialized')
parser_init.set_defaults(func=cmd_init)

parser_new = subparsers.add_parser('new', help='Create new issue')
parser_new.set_defaults(func=cmd_new)

parser_list = subparsers.add_parser('list', help='list all issues')
parser_list.set_defaults(func=cmd_list)

parser_help = subparsers.add_parser('help', help='Show help')
parser_help.set_defaults(func=cmd_help)

parser_config = subparsers.add_parser('config', help='Get and set options')
parser_config.set_defaults(func=cmd_config)


def main():
    config = ConfigParser.RawConfigParser()
    config.read('.issue')

    args = parser.parse_args()
    args.func(args, config)


if __name__ == '__main__':
    main()
