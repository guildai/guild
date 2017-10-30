# Copyright 2017 TensorHub, Inc.
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

from guild import cli
from guild import pip_util
from guild import namespace
from guild import package

INTERNAL_PACKAGES = ["guildai"]

def list_packages(args):
    installed = pip_util.get_installed()
    filtered = _filter_packages(installed, args)
    pkgs = [_format_pkg(pkg) for pkg in filtered]
    cli.table(pkgs, cols=["name", "version"], sort=["name"])

def _filter_packages(pkgs, args):
    return [pkg for pkg in pkgs if _filter_pkg(pkg, args)]

def _filter_pkg(pkg, args):
    return (pkg.project_name not in INTERNAL_PACKAGES
            and (not args.terms or
                 any((term in pkg.project_name for term in args.terms)))
            and (args.all or package.is_gpkg(pkg.project_name)))

def _format_pkg(pkg):
    return {
        "name": namespace.apply_namespace(pkg.project_name),
        "version": pkg.version,
    }

def install_packages(args):
    for reqs, index_urls in _installs(args):
        pip_util.install(
            reqs,
            index_urls=index_urls,
            upgrade=args.upgrade,
            pre_releases=args.pre,
            no_cache=args.no_cache,
            reinstall=args.reinstall)

def _installs(args):
    index_urls = {}
    for pkg in args.packages:
        try:
            ns, req = namespace.split_name(pkg)
        except namespace.NamespaceError as e:
            terms = " ".join(pkg.split("/")[1:])
            cli.error(
                "unsupported namespace %s in '%s'\n"
                "Try 'guild search %s -a' to find matching packages."
                % (e.value, pkg, terms))
        else:
            info = ns.pip_info(req)
            urls_key = "\n".join(info.install_urls)
            index_urls.setdefault(urls_key, []).append(info.project_name)
    return [
        (reqs, urls_key.split("\n"))
        for urls_key, reqs in index_urls.items()
    ]

def uninstall_packages(args):
    for reqs, _ in _installs(args):
        try:
            pip_util.uninstall(reqs, dont_prompt=args.yes)
        except pip_util.NotInstalledError as e:
            pkg_name = namespace.apply_namespace(e.req)
            cli.error("package '%s' it not installed" % pkg_name)

def package_info(args):
    for i, (project, pkg) in enumerate(_iter_project_names(args.packages)):
        if i > 0:
            cli.out("---")
        exit_status = pip_util.print_package_info(
            project,
            verbose=args.verbose,
            show_files=args.files)
        if exit_status != 0:
            logging.warning("unknown package %s", pkg)

def _iter_project_names(pkgs):
    for pkg in pkgs:
        try:
            ns, name = namespace.split_name(pkg)
        except namespace.NamespaceError:
            logging.warning("unknown namespace in '%s', ignoring", pkg)
        else:
            yield ns.pip_info(name).project_name, pkg
