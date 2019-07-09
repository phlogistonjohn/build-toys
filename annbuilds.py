#!/usr/bin/python

import argparse
import jinja2


TEMPLATE = """
New builds are available:

{% if nb.rpms -%}
RPMs:
{% for rpm in nb.rpms %}
{{ rpm }}
{%- endfor %}
{%- endif %}

{% if nb.containers -%}
Container Images:
{% for cimg in nb.containers %}
{{ cimg }}
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
        self.rpms = rpms
        self.containers = [
            '{}{}'.format(container_prefix, c) for c in containers]
        self.bugs = [
            bz_format.format(bz) for bz in bugs]

    def __str__(self):
        return (
            'New Builds: rpms=%r, containers=%r, bugs=%s'
            % (self.rpms, self.containers, self.bugs))


def message_body(newbuild):
    return jinja2.Template(TEMPLATE).render(nb=newbuild)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--rpm', '-r', action='append')
    parser.add_argument('--container', '-c', action='append')
    parser.add_argument('--bug', '-b', action='append')
    parser.add_argument("--container-prefix")
    parser.add_argument("--bz-format",
        default='https://bugzilla.redhat.com/show_bug.cgi?id={}')
    cli = parser.parse_args()

    nb = NewBuild(
        cli.rpm or [],
        cli.container or [],
        cli.bug or [],
        container_prefix=cli.container_prefix,
        bz_format=cli.bz_format,
    )
    print (message_body(nb))


if __name__ == '__main__':
    main()
