#!/usr/bin/python

import argparse
import jinja2

try:
    import errata_tool as et
    has_errata_tool = True
except ImportError:
    has_errata_tool = False


TEMPLATE = """
New builds are available:

{% if nb.rpms -%}
RPMs:
{%- for rpm in nb.rpms %}
{{ rpm }}
{%- endfor %}
{%- endif %}

{% if nb.containers -%}
Container Images:
{%- for cimg in nb.containers %}
{{ nb.container_prefix }}{{ cimg }}
{% endfor %}
{%- endif %}

{% if nb.bugs -%}
Fixes:
{% for bz in nb.bugs %}
{{ bz }}
{% endfor %}
{%- endif %}

Thank you.
"""

class NewBuild(object):
    def __init__(self, rpms, containers, bugs, container_prefix='', bz_format='{}'):
        self.rpms = set(rpms)
        self.containers = set(containers)
        self.bugs = set(
            bz_format.format(bz) for bz in bugs)
        self.container_prefix = container_prefix

    def __str__(self):
        return (
            'New Builds: rpms=%r, containers=%r, bugs=%s'
            % (self.rpms, self.containers, self.bugs))


def message_body(newbuild):
    return jinja2.Template(TEMPLATE).render(nb=newbuild)


def build_from_erratum(nb, errata_id):
    erratum = et.Erratum(errata_id=errata_id)
    if 'rpm' in erratum.content_types:
        for _, v in erratum.errata_builds.items():
            for build in v:
                nb.rpms.add(build)
    else:
        for _, v in erratum.errata_builds.items():
            for build in v:
                # convert last sections to "tag format"
                cimg = build.rsplit('-', 2)
                build = '{}:{}-{}'.format(*cimg)
                nb.containers.add(build)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--rpm', '-r', action='append')
    parser.add_argument('--container', '-c', action='append')
    parser.add_argument('--bug', '-b', action='append')
    parser.add_argument("--container-prefix")
    parser.add_argument("--bz-format",
        default='https://bugzilla.redhat.com/show_bug.cgi?id={}')
    parser.add_argument('--erratum', '-e', action='append')
    cli = parser.parse_args()

    nb = NewBuild(
        cli.rpm or [],
        cli.container or [],
        cli.bug or [],
        container_prefix=cli.container_prefix,
        bz_format=cli.bz_format,
    )
    for e in cli.erratum:
        build_from_erratum(nb, errata_id=e)
    print (message_body(nb))


if __name__ == '__main__':
    main()
