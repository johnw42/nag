#! /usr/bin/python
import argparse
import logging
import os
import re
import subprocess
import sys
import xdg.BaseDirectory as xdgbase
import time


APP_NAME = 'nag'


def main():
  App().Run()


class App(object):

  def __init__(self):
    self.key_sequence = KeySequence()
    self.nag_interval = 300
    self.nag_header = '\nReminders:'
    self.use_git = True

    os.environ.pop('GIT_DIR', None)

    # for path in xdgbase.load_config_paths(APP_NAME, 'config.py'):
    #   with file(path) as stream:
    #     exec stream in self.__dict__

    self.nag_home = xdgbase.save_config_path(APP_NAME)
    self.nag_file_dir = xdgbase.save_config_path(APP_NAME, 'files')
    self.runtime = os.path.join(xdgbase.get_runtime_dir(), APP_NAME)
    self.timestamp = os.path.join(self.runtime, 'timestamp')

  def Run(self):
    parser = argparse.ArgumentParser(description='')
    parser.add_argument(
        '--debug', action='store_true',
        help=argparse.SUPPRESS)

    subparsers = parser.add_subparsers()

    for name in ['push', 'me']:
      parser_push = subparsers.add_parser(
          name, description='Adds a new reminder.')
      parser_push.add_argument('message', nargs=argparse.REMAINDER)
      parser_push.set_defaults(func=self.DoPush)

    for name in ['show', 'list']:
      parser_show = subparsers.add_parser(
          name, description='Show existing reminders.')
      parser_show.add_argument('key', nargs='*')
      parser_show.set_defaults(func=self.DoShow)

    for name in ['maybe', 'ps1']:
      parser_maybe = subparsers.add_parser(
          name, description='Show reminders (maybe).')
      parser_maybe.add_argument('key', nargs='?')
      parser_maybe.set_defaults(func=self.DoMaybe)

    parser_rm = subparsers.add_parser(
        'rm', description='Delete a reminder.')
    parser_rm.add_argument('key', nargs='+')
    parser_rm.set_defaults(func=self.DoRm)

    parser_log = subparsers.add_parser(
        'log', description='Show a change log.')
    parser_log.set_defaults(func=self.DoLog)

    parser_git = subparsers.add_parser(
        'git', description='Run a git command.')
    parser_git.add_argument('command', nargs=argparse.REMAINDER)
    parser_git.set_defaults(func=self.DoGit)

    parser_help = subparsers.add_parser(
        'help', description='Show help.')
    parser_help.set_defaults(func=self.DoHelp)

    args = parser.parse_args()
    if args.debug:
      logging.basicConfig(level=logging.DEBUG)
      logging.debug('debug logging enabled')

    args.func(args)

  def DoPush(self, args):
    keys = self._SortedNagKeys()
    if not keys:
      next_key = self.key_sequence.First()
    else:
      last_key = keys[-1]
      next_key = self.key_sequence.Next(keys[-1])
    self._SetNag(next_key, ' '.join(args.message))
    self._GitCommit('added reminder: ' + next_key)
    print 'reminder saved as', next_key

  def DoShow(self, args):
    if args.key:
      map(self._ShowNag, args.key)
    else:
      self._ShowAllNags()

  def DoMaybe(self, args):
    if os.path.isfile(self.timestamp):
      now = time.time()
      then = os.path.getmtime(self.timestamp)
      if (now - then) < self.nag_interval:
        return
    keys = self._SortedNagKeys()
    if keys:
      print self.nag_header
      for key in keys:
        self._ShowNag(key)
    self._UpdateTimestamp()

  def DoRm(self, args):
    for key in args.key:
      filename = self._NagFile(key)
      if os.path.isfile(filename):
        os.unlink(filename)
    self._GitCommit('deleted reminders: ' + ' '.join(args.key))

  def DoHelp(self, args):
    print """\
Add the following to your .bashrc:

  PROMPT_COMMAND='nag ps1'

Create a new reminder:

  nag me My free text reminder.

Clear the remidner with

  nag rm X"""

  def DoLog(self, args):
    self._GitPopen('log').wait()

  def DoGit(self, args):
    p = self._GitPopen(*args.command)
    p.wait()

  def _GitCheckCall(self, *command):
    self._Git(subprocess.check_call, command)

  def _GitCheckOutput(self, *command):
    self._Git(subprocess.check_output, command)

  def _GitPopen(self, *command, **kwargs):
    return self._Git(subprocess.Popen, command, **kwargs)

  def _Git(self, func, command, **kwargs):
    if not self.use_git: return None
    return func(('git',) + command, cwd=self.nag_home, **kwargs)

  def _GitCommit(self, message):
    if not os.path.isdir(os.path.join(self.nag_home, '.git')):
      self._GitCheckCall('init')
    self._GitCheckCall('add', '--all')
    self._GitCheckCall('commit', '-q', '-m', message)

  def _SetNag(self, key, content):
    filename = self._NagFile(key)
    with open(filename, 'w') as stream:
      stream.write(content)

  def _ShowNag(self, key):
    nag_file = self._NagFile(key)
    if os.path.isfile(nag_file):
      print '%s: %s' % (key, open(nag_file).read().rstrip())

  def _ShowAllNags(self):
    keys = self._SortedNagKeys()
    for key in keys:
      self._ShowNag(key)
    self._UpdateTimestamp()
    if not keys:
      print 'no reminders set'

  def _NagFile(self, key):
    return os.path.join(self.nag_file_dir, key)

  def _SortedNagKeys(self):
    names = os.listdir(self.nag_file_dir)
    self.key_sequence.Sort(names)
    return names

  def _UpdateTimestamp(self):
    open(self.timestamp, 'w').close()


class KeySequence(object):

  def SortKey(self, name):
    assert self.IsValid(name)
    if IsNumberString(name):
      return (1, int(name))
    else:
      return (0, name)

  def Sort(self, seq):
    seq.sort(key=self.SortKey)

  def IsValid(self, name):
    return bool(re.match(r'^(?:[a-z]|[1-9]\d*)$', name))

  def First(self):
    return 'a'

  def Next(self, name):
    assert self.IsValid(name)
    if name == 'z':
      return '1'
    elif IsNumberString(name):
      return str(int(name) + 1)
    else:
      return chr(ord(name) + 1)


def IsNumberString(s):
  return bool(re.match(r'\d+', s))


if __name__ == '__main__': main()
