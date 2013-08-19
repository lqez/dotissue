import ConfigParser
import argparse
import os
import sys
import tempfile

from subprocess import call
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

    tree = Tree()
#    tree_issues = Tree()
#    tree_labels = Tree()

    blob = Blob.from_string("This is a branch for dotissue.\n")
    tree.add("README.md", 0100644, blob.id)
    object_store.add_object(blob)
#
#    blob = Blob.from_string("This is a directory for issues.\n")
#    tree_issues.add("README.md", 0100644, blob.id)
#    object_store.add_object(blob)
#
#    blob = Blob.from_string("This is a directory for labels.\n")
#    tree_labels.add("README.md", 0100644, blob.id)
#    object_store.add_object(blob)
#
#    tree.add(DI_ISSUES, 0040000, tree_issues.id)
#    tree.add(DI_LABELS, 0040000, tree_labels.id)
#
#    object_store.add_object(tree_issues)
#    object_store.add_object(tree_labels)
    object_store.add_object(tree)

    commit = repo.do_commit("Initial commit",
                            commit_timezone=-timezone,
                            tree=tree.id,
                            ref='refs/heads/%s' % DI_BRANCH)

    print 'Initialized by %s. :^D' % commit
    sys.exit(0)


def cmd_new(args, config):
    try:
        repo = Repo(args.path)
    except NotGitRepository:
        sys.exit('It does not look like a valid repository.')

    if DI_BRANCH not in get_branch_list(repo):
        sys.exit('Not initialized by dotissue. Use init first.')

    if not args.title:
        EDITOR = os.environ.get('EDITOR', 'vim')
        initial_message = "<Issue title here>"

        with tempfile.NamedTemporaryFile(suffix=".tmp") as msgfile:
            msgfile.write(initial_message)
            msgfile.flush()
            call([EDITOR, msgfile.name])

            with open(msgfile.name, 'r') as f:
                args.title = f.read()

    title = args.title.strip()
    object_store = repo.object_store
    tree = repo[repo['refs/heads/%s' % DI_BRANCH].tree]

    tree_issue = Tree()

    blob = Blob.from_string(title)
    tree_issue.add("_title", 0100644, blob.id)
    object_store.add_object(blob)

    tree.add(blob.id, 0040000, tree_issue.id)

    object_store.add_object(tree_issue)
    object_store.add_object(tree)

    msg = (title[:60] + '..') if len(title) > 60 else title
    commit = repo.do_commit("New issue: %s" % msg,
                            commit_timezone=-timezone,
                            tree=tree.id,
                            ref='refs/heads/%s' % DI_BRANCH)

    print 'Issue created : %s' % commit
    sys.exit(0)


def cmd_list(args, config):
    try:
        repo = Repo(args.path)
    except NotGitRepository:
        sys.exit('It does not look like a valid repository.')

    if DI_BRANCH not in get_branch_list(repo):
        sys.exit('Not initialized by dotissue. Use init first.')

    timemaps = {}

    c = repo['refs/heads/%s' % DI_BRANCH]
    while True:
        tree = repo[c.tree]

        for entry in tree.iteritems():
            obj = repo[entry.sha]

            if obj.type != 2:
                continue

            for item in obj.items():
                if item.path != '_title':
                    continue

            timemaps[item.sha] = c.commit_time


        try:
            c = repo[c.parents[0]]
        except IndexError:
            break


    tree = repo[repo['refs/heads/%s' % DI_BRANCH].tree]

    from datetime import datetime

    issues = []

    for entry in tree.iteritems():
        obj = repo[entry.sha]

        if obj.type != 2:
            continue

        for item in obj.items():
            if item.path != '_title':
                continue

            issues.append((item, timemaps[item.sha]))

    issues.sort(key=lambda x: x[1], reverse=True)

    for item, time in issues:
        print 'issue(%s) : %s at %s' % (item.sha[:7], repo[item.sha], datetime.fromtimestamp(time))



def cmd_reply(args, config):
    print 'reply command'


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
parser_new.add_argument('--path', default='.', metavar='path', type=str, help='Path of the working repository')
parser_new.add_argument('title', nargs='?', default='', metavar='title', type=str, help='Issue title')
parser_new.set_defaults(func=cmd_new)

parser_reply = subparsers.add_parser('reply', help='Reply to issue')
parser_reply.add_argument('--path', default='.', metavar='path', type=str, help='Path of the working repository')
parser_reply.add_argument('issue', metavar='issue', type=str, help='Hash for the issue')
parser_reply.add_argument('msg', nargs='?', default='', metavar='msg', type=str, help='Message')
parser_reply.set_defaults(func=cmd_reply)

parser_list = subparsers.add_parser('list', help='list all issues')
parser_list.add_argument('--path', default='.', metavar='path', type=str, help='Path of the working repository')
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
