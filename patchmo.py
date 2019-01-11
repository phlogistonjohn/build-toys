#!/usr/bin/python
"""Helper tool for generating patches for RPM builds.
"""
#
# Copyright 2019  John Mulligan <jmulligan@redhat.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

import argparse
import logging
import os
import sys
import subprocess


log = logging.getLogger('patchmo')


class Error(Exception):
    hint = None
    def hint(self, value):
        self.hint = value
        return self


def git(*args):
    cmd = ['git'] + list(args)
    log.debug('Running cmd: %s', ' '.join(cmd))
    subprocess.check_call(cmd)


def git_output(*args):
    cmd = ['git'] + list(args)
    log.debug('Running cmd: %s', ' '.join(cmd))
    return subprocess.check_output(cmd)


def next_number(dpath):
    curr = 0
    for fn in os.listdir(dpath):
        if fn.endswith('.patch') and fn.split('-')[0].isdigit():
            n = int(fn.split('-')[0])
            if n > curr:
                curr = n
    return curr + 1


def pick_patches(cli):
    log.debug("Changing dir to '%s'", cli.SOURCE)
    os.chdir(cli.SOURCE)
    try:
        out = git_output('rev-parse', 'patchmo.START', '--')
        start_rev = out.decode('utf8').split()[0]
    except subprocess.CalledProcessError:
        raise Error('no revision found for patchmo.START').hint(
            "Ensure you have set the 'patchmo.START' tag")
    try:
        out = git_output('rev-parse', 'patchmo.END', '--')
        end_rev = out.decode('utf8').split()[0]
    except subprocess.CalledProcessError:
        raise Error('no revision found for patchmo.END').hint(
            "Ensure you have set the 'patchmo.END' tag")
    log.info("Found start=%s  end=%s", start_rev, end_rev)

    number = str(next_number(cli.DEST))
    log.info("Found initial number: %s", number)

    git('format-patch',
        '--no-numbered',
        '--start-number', number,
        '--output-directory', cli.DEST,
        "{}^..{}".format(start_rev, end_rev))


def spec_hints(cli):
    spec = ''
    patches = []
    for fn in os.listdir(cli.DEST):
        if fn.endswith('.patch') and fn.split('-')[0].isdigit():
            patches.append(fn)
        if fn.endswith('.spec'):
            spec = fn
    if not spec:
        raise Error('.spec file not found in dest')

    spec_patches = {}
    spec_prep_patch = {}
    with open(os.path.join(cli.DEST, spec)) as fh:
        for line in fh:
            l = line.strip()
            if l.startswith('Patch') and ':' in l:
                h, p = l.split()
                if h[5:-1] != p.split('-')[0]:
                    log.warning('Patch numbers do not match: %r', l)
                spec_patches[p] = l
            if l.startswith('%patch'):
                parts = l.split()
                h = parts[0]
                p = parts[3][1:]
                if h[6:] != p.split('-')[0]:
                    log.warning('Patch numbers do not match: %r', l)
                spec_prep_patch[p] = l
    print ('------------')
    for p in sorted(patches):
        n = p.split("-")[0]
        if p in spec_patches:
            log.debug('patch %s found in spec sources', p)
        else:
            print ('Patch{}:      {}'.format(n, p))
    print ('------------')
    for p in sorted(patches):
        n = p.split("-")[0]
        if p in spec_prep_patch:
            log.debug('patch %s found in spec prep', p)
        else:
            print ('%patch{} -p1 -b .{}'.format(n, p))
    return


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("SOURCE")
    parser.add_argument("DEST")
    cli = parser.parse_args()
    logging.basicConfig(
        format='%(levelname)s: %(message)s',
        level=logging.DEBUG if cli.debug else logging.INFO)
    try:
        pick_patches(cli)
        spec_hints(cli)
    except Error as err:
        sys.stderr.write("error: {}\n".format(err))
        if err.hint:
            sys.stderr.write("({})\n".format(err.hint))
        sys.exit(1)


if __name__ == '__main__':
    main()
