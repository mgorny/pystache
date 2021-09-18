#!/usr/bin/env python
# coding: utf-8

"""
This script supports publishing Pystache to PyPI.

This docstring contains instructions to Pystache maintainers on how
to release a new version of Pystache.

(1) Prepare the release.

Make sure the code is finalized and merged to master.  Bump the version
number in setup.py, update the release date in the HISTORY file, etc.

Generate the reStructuredText long_description using--

    $ python setup.py prep

and be sure this new version is checked in.  You must have pandoc installed
to do this step:

    http://johnmacfarlane.net/pandoc/

It helps to review this auto-generated file on GitHub prior to uploading
because the long description will be sent to PyPI and appear there after
publishing.  PyPI attempts to convert this string to HTML before displaying
it on the PyPI project page.  If PyPI finds any issues, it will render it
instead as plain-text, which we do not want.

To check in advance that PyPI will accept and parse the reST file as HTML,
you can use the rst2html program installed by the docutils package
(http://docutils.sourceforge.net/).  To install docutils:

    $ pip install docutils

To check the file, run the following command and confirm that it reports
no warnings:

    $ python setup.py --long-description | rst2html.py -v --no-raw > out.html

See here for more information:

    http://docs.python.org/distutils/uploading.html#pypi-package-display

(2) Push to PyPI.  To release a new version of Pystache to PyPI--

    http://pypi.python.org/pypi/pystache

create a PyPI user account if you do not already have one.  The user account
will need permissions to push to PyPI.  A current "Package Index Owner" of
Pystache can grant you those permissions.

When you have permissions, run the following:

    python setup.py publish

If you get an error like the following--

    Upload failed (401): You must be identified to edit package information

then add a file called .pyirc to your home directory with the following
contents:

    [server-login]
    username: <PyPI username>
    password: <PyPI password>

as described here, for example:

    http://docs.python.org/release/2.5.2/dist/pypirc.html

(3) Tag the release on GitHub.  Here are some commands for tagging.

List current tags:

    git tag -l -n3

Create an annotated tag:

    git tag -a -m "Version 0.5.1" "v0.5.1"

Push a tag to GitHub:

    git push --tags defunkt v0.5.1

"""

import os
import shutil
import sys


py_version = sys.version_info

# distutils does not seem to support the following setup() arguments.
# It displays a UserWarning when setup() is passed those options:
#
#  * entry_points
#  * install_requires
#
# distribute works with Python 2.3.5 and above:
#
#   http://packages.python.org/distribute/setuptools.html#building-and-distributing-packages-with-distribute
#
if py_version < (2, 3, 5):
    # TODO: this might not work yet.
    import distutils as dist
    from distutils import core
    setup = core.setup
else:
    import setuptools as dist
    setup = dist.setup


VERSION = '0.5.4'  # Also change in pystache/__init__.py.

FILE_ENCODING = 'utf-8'

README_PATH = 'README.md'
HISTORY_PATH = 'HISTORY.md'
LICENSE_PATH = 'LICENSE'

RST_DESCRIPTION_PATH = 'setup_description.rst'

TEMP_EXTENSION = '.temp'

PREP_COMMAND = 'prep'

CLASSIFIERS = (
    'Development Status :: 4 - Beta',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2',
    'Programming Language :: Python :: 2.4',
    'Programming Language :: Python :: 2.5',
    'Programming Language :: Python :: 2.6',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.1',
    'Programming Language :: Python :: 3.2',
    'Programming Language :: Python :: 3.3',
    'Programming Language :: Python :: Implementation :: PyPy',
)

# Comments in reST begin with two dots.
RST_LONG_DESCRIPTION_INTRO = """\
.. Do not edit this file.  This file is auto-generated for PyPI by setup.py
.. using pandoc, so edits should go in the source files rather than here.
"""


def read(path):
    """
    Read and return the contents of a text file as a unicode string.

    """
    # This function implementation was chosen to be compatible across Python 2/3.
    f = open(path, 'rb')
    # We avoid use of the with keyword for Python 2.4 support.
    try:
        b = f.read()
    finally:
        f.close()

    return b.decode(FILE_ENCODING)


def write(u, path):
    """
    Write a unicode string to a file (as utf-8).

    """
    print(("writing to: %s" % path))
    # This function implementation was chosen to be compatible across Python 2/3.
    f = open(path, "wb")
    try:
        b = u.encode(FILE_ENCODING)
        f.write(b)
    finally:
        f.close()


def make_temp_path(path, new_ext=None):
    """
    Arguments:

      new_ext: the new file extension, including the leading dot.
        Defaults to preserving the existing file extension.

    """
    root, ext = os.path.splitext(path)
    if new_ext is None:
        new_ext = ext
    temp_path = root + TEMP_EXTENSION + new_ext
    return temp_path


def strip_html_comments(text):
    """Strip HTML comments from a unicode string."""
    lines = text.splitlines(True)  # preserve line endings.

    # Remove HTML comments (which we only allow to take a special form).
    new_lines = [line for line in lines if not line.startswith("<!--")]

    return "".join(new_lines)


# We write the converted file to a temp file to simplify debugging and
# to avoid removing a valid pre-existing file on failure.
def convert_md_to_rst(md_path, rst_temp_path):
    """
    Convert the contents of a file from Markdown to reStructuredText.

    Returns the converted text as a Unicode string.

    Arguments:

      md_path: a path to a UTF-8 encoded Markdown file to convert.

      rst_temp_path: a temporary path to which to write the converted contents.

    """
    # Pandoc uses the UTF-8 character encoding for both input and output.
    command = "pandoc --write=rst --output=%s %s" % (rst_temp_path, md_path)
    print(("converting with pandoc: %s to %s\n-->%s" % (md_path, rst_temp_path,
                                                       command)))

    if os.path.exists(rst_temp_path):
        os.remove(rst_temp_path)

    os.system(command)

    if not os.path.exists(rst_temp_path):
        s = ("Error running: %s\n"
             "  Did you install pandoc per the %s docstring?" % (command,
                                                                 __file__))
        sys.exit(s)

    return read(rst_temp_path)


# The long_description needs to be formatted as reStructuredText.
# See the following for more information:
#
#   http://docs.python.org/distutils/setupscript.html#additional-meta-data
#   http://docs.python.org/distutils/uploading.html#pypi-package-display
#
def make_long_description():
    """
    Generate the reST long_description for setup() from source files.

    Returns the generated long_description as a unicode string.

    """
    readme_path = README_PATH

    # Remove our HTML comments because PyPI does not allow it.
    # See the setup.py docstring for more info on this.
    readme_md = strip_html_comments(read(readme_path))
    history_md = strip_html_comments(read(HISTORY_PATH))
    license_md = """\
License
=======

""" + read(LICENSE_PATH)

    sections = [readme_md, history_md, license_md]
    md_description = '\n\n'.join(sections)

    # Write the combined Markdown file to a temp path.
    md_ext = os.path.splitext(readme_path)[1]
    md_description_path = make_temp_path(RST_DESCRIPTION_PATH, new_ext=md_ext)
    write(md_description, md_description_path)

    rst_temp_path = make_temp_path(RST_DESCRIPTION_PATH)
    long_description = convert_md_to_rst(md_path=md_description_path,
                                         rst_temp_path=rst_temp_path)

    return "\n".join([RST_LONG_DESCRIPTION_INTRO, long_description])


def prep():
    """Update the reST long_description file."""
    long_description = make_long_description()
    write(long_description, RST_DESCRIPTION_PATH)


def publish():
    """Publish this package to PyPI (aka "the Cheeseshop")."""
    long_description = make_long_description()

    if long_description != read(RST_DESCRIPTION_PATH):
        print(("""\
Description file not up-to-date: %s
Run the following command and commit the changes--

    python setup.py %s
""" % (RST_DESCRIPTION_PATH, PREP_COMMAND)))
        sys.exit()

    print(("Description up-to-date: %s" % RST_DESCRIPTION_PATH))

    answer = input("Are you sure you want to publish to PyPI (yes/no)?")

    if answer != "yes":
        exit("Aborted: nothing published")

    os.system('python setup.py sdist upload')


# We use the package simplejson for older Python versions since Python
# does not contain the module json before 2.6:
#
#   http://docs.python.org/library/json.html
#
# Moreover, simplejson stopped officially support for Python 2.4 in version 2.1.0:
#
#   https://github.com/simplejson/simplejson/blob/master/CHANGES.txt
#
requires = []
if py_version < (2, 5):
    requires.append('simplejson<2.1')
elif py_version < (2, 6):
    requires.append('simplejson')

INSTALL_REQUIRES = requires

# TODO: decide whether to use find_packages() instead.  I'm not sure that
#   find_packages() is available with distutils, for example.
PACKAGES = [
    'pystache',
    'pystache.commands',
    # The following packages are only for testing.
    'pystache.tests',
    'pystache.tests.data',
    'pystache.tests.data.locator',
    'pystache.tests.examples',
]


# The purpose of this function is to follow the guidance suggested here:
#
#   http://packages.python.org/distribute/python3.html#note-on-compatibility-with-setuptools
#
# The guidance is for better compatibility when using setuptools (e.g. with
# earlier versions of Python 2) instead of Distribute, because of new
# keyword arguments to setup() that setuptools may not recognize.
def get_extra_args():
    """
    Return a dictionary of extra args to pass to setup().

    """
    extra = {}
    return extra


def main(sys_argv):

    # TODO: use the logging module instead of printing.
    # TODO: include the following in a verbose mode.
    sys.stderr.write("pystache: using: version %s of %s\n" % (repr(dist.__version__), repr(dist)))

    command = sys_argv[-1]

    if command == 'publish':
        publish()
        sys.exit()
    elif command == PREP_COMMAND:
        prep()
        sys.exit()

    long_description = read(RST_DESCRIPTION_PATH)
    template_files = ['*.mustache', '*.txt']
    extra_args = get_extra_args()

    setup(name='pystache',
          version=VERSION,
          license='MIT',
          description='Mustache for Python',
          long_description=long_description,
          author='Chris Wanstrath',
          author_email='chris@ozmm.org',
          maintainer='Chris Jerdonek',
          maintainer_email='chris.jerdonek@gmail.com',
          url='http://github.com/defunkt/pystache',
          install_requires=INSTALL_REQUIRES,
          packages=PACKAGES,
          package_data = {
              # Include template files so tests can be run.
              'pystache.tests.data': template_files,
              'pystache.tests.data.locator': template_files,
              'pystache.tests.examples': template_files,
          },
          entry_points = {
            'console_scripts': [
                'pystache=pystache.commands.render:main',
                'pystache-test=pystache.commands.test:main',
            ],
          },
          classifiers = CLASSIFIERS,
          **extra_args
    )


if __name__=='__main__':
    main(sys.argv)
