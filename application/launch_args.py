import sys

args = sys.argv

IS_WINDOWS = '--windows' in args
IS_LOCAL = '--local'  in args
IS_DEBUG = '--debug' in args
SHOULD_LOG_SQL = '--log-sql' in args