# Copyright 2017-2019 TensorHub, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import
from __future__ import division

import logging
import re
import os
import subprocess


class Scheme(object):
    def __init__(
        self,
        name,
        sentinel,
        commit_cmd,
        commit_pattern,
        commit_ok_errors,
        status_cmd,
        status_pattern,
        status_ok_errors,
    ):
        self.name = name
        self.sentinel = sentinel
        self.commit_cmd = commit_cmd
        self.commit_pattern = commit_pattern
        self.commit_ok_errors = commit_ok_errors
        self.status_cmd = status_cmd
        self.status_pattern = status_pattern
        self.status_ok_errors = status_ok_errors


SCHEMES = [
    Scheme(
        "git",
        ".git",
        ["git", "--work-tree", "{repo}", "log", "-1"],
        re.compile(r"commit ([a-f0-9]+)"),
        [128],
        ["git", "-C", "{repo}", "status", "-s"],
        re.compile(r"(.)"),
        [],
    )
]

log = logging.getLogger("guild")


class NoCommit(Exception):
    pass


class CommitReadError(Exception):
    pass


def commit_for_dir(dir):
    """Returns a tuple of commit and workspace status.

    Raises NoCommit if a commit is not available.
    """
    dir = os.path.abspath(dir)
    cur = dir
    last = None
    while cur != last:
        for scheme in SCHEMES:
            if os.path.exists(os.path.join(cur, scheme.sentinel)):
                commit = _apply_scheme(
                    cur,
                    scheme.commit_cmd,
                    scheme.commit_pattern,
                    scheme.commit_ok_errors,
                )
                if commit is None:
                    raise NoCommit(cur)
                status = _apply_scheme(
                    cur,
                    scheme.status_cmd,
                    scheme.status_pattern,
                    scheme.status_ok_errors,
                )
                return _format_commit(commit, scheme), _format_status(status)
        last = cur
        cur = os.path.dirname(cur)
    raise NoCommit(dir)


def _apply_scheme(repo_dir, cmd_template, pattern, ok_errors):
    cmd = [arg.format(repo=repo_dir) for arg in cmd_template]
    log.debug("vcs scheme cmd for repo %s: %s", repo_dir, cmd)
    try:
        out = subprocess.check_output(
            cmd, cwd=repo_dir, env=os.environ, stderr=subprocess.STDOUT
        )
    except OSError as e:
        if e.errno == 2:
            return None
        raise CommitReadError(e)
    except subprocess.CalledProcessError as e:
        if e.returncode in ok_errors:
            return None
        raise CommitReadError(e, e.output)
    else:
        out = out.decode("ascii", errors="replace")
        log.debug("vcs scheme result: %s", out)
        m = pattern.match(out)
        if not m:
            return None
        return m.group(1)


def _format_commit(commit, scheme):
    return "%s:%s" % (scheme.name, commit)


def _format_status(status):
    return bool(status)