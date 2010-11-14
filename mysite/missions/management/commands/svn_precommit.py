from django.core.management import BaseCommand, CommandError
from mysite.missions.svn import controllers
import sys

class Command(BaseCommand):
    args = '<repo_path> <txn_id>'
    help = 'SVN pre-commit hook for mission repositories'

    def handle(self, *args, **options):
        # This management command is called from the mission svn repositories
        # as the pre-commit hook.  It receives the repository path and transaction
        # ID as arguments, and it receives a description of applicable lock
        # tokens on stdin.  Its environment and current directory are undefined.
        if len(args) != 2:
            raise CommandError, 'Exactly two arguments are expected.'
        repo_path, txn_id = args

        try:
            controllers.SvnCommitMission.pre_commit_hook(repo_path, txn_id)
        except controllers.IncorrectPatch, e:
            sys.stderr.write('\n    ' + str(e) + '\n\n')
            raise CommandError, 'The commit failed to validate.'
