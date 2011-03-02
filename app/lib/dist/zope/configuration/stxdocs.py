##############################################################################
#
# Copyright (c) 2004 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""STX Configuration Documentation Renderer

Usage: stxdocs.py [options]
Options:
    -h / --help
        Print this message and exit.

    -f <path>
        Specifies the root ZCML meta directives file, relative to the current
        location. All included files will be considered as well

    -o <dir>
        Specifies a directory, relative to the current location in which the
        documentation is stored. Note that this tool will create
        sub-directories with files in them. 

$Id: stxdocs.py 110550 2010-04-06 06:50:36Z tseaver $
"""
import sys, os, getopt
import zope.configuration
from zope.schema import getFieldsInOrder 
from zope.configuration import config, xmlconfig
from zope.configuration.docutils import wrap, makeDocStructures

def usage(code, msg=''):
    # Python 2.1 required
    print >> sys.stderr, __doc__
    if msg:
        print >> sys.stderr, msg
    sys.exit(code)

def _directiveDocs(name, schema, handler, info, indent_offset=0):
    """Generate the documentation for one directive."""

    # Write out the name of the directive
    text  = ' '*indent_offset
    text +=  '%s\n\n' %name

    # Specify the file and location it has been declared
    if isinstance(info, xmlconfig.ParserInfo):
        # We do not want to specify the whole path; starting at the 'zope'
        # package is enough.
        base_dir = os.path.dirname(os.path.dirname(
            zope.configuration.__file__))[:-4]
        file = info.file.replace(base_dir, '')

        info_text = 'File %s, lines %i - %i.' %(file, info.line, info.eline)
        text += wrap(info_text, 78, indent_offset+2)

    elif isinstance(info, (str, unicode)) and info:
        text += wrap(info, 78, indent_offset+2)

    # Insert Handler information
    if handler is not None:
        handler_path = handler.__module__ + '.' + handler.__name__
        text += wrap('Handler: %s' %handler_path, 78, indent_offset+2)

    # Use the schema documentation string as main documentation text for the
    # directive.
    text += wrap(schema.getDoc(), 78, indent_offset+2)
    text += ' '*indent_offset + '  Attributes\n\n'

    # Create directive attribute documentation
    for name, field in getFieldsInOrder(schema):
        name = name.strip('_')
        if field.required:
            opt = 'required'
        else:
            opt = 'optional, default=%s' %repr(field.default)
        text += ' '*indent_offset
        text += '    %s -- %s (%s)\n\n' %(name, field.__class__.__name__, opt)

        text += wrap(field.title, 78, indent_offset+6)
        text += wrap(field.description, 78, indent_offset+6)

    return text

def _subDirectiveDocs(subdirs, namespace, name):
    """Appends a list of sub-directives and their full specification."""
    if subdirs.has_key((namespace, name)):
        text = '\n  Subdirectives\n\n'
        sub_dirs = []
        # Simply walk through all sub-directives here.
        subs = subdirs[(namespace, name)]
        for sd_ns, sd_name, sd_schema, sd_handler, sd_info in subs:
            sub_dirs.append(_directiveDocs(
                sd_name, sd_schema, sd_handler, sd_info, 4))

        return text + '\n\n'.join(sub_dirs)
    return ''

def makedocs(target_dir, zcml_file):
    """Generate the documentation tree.

    All we need for this is a starting ZCML file and a directory in which to
    put the documentation.
    """
    context = xmlconfig.file(zcml_file, execute=False)
    namespaces, subdirs = makeDocStructures(context)

    for namespace, directives in namespaces.items():
        ns_dir = os.path.join(target_dir, namespace.split('/')[-1])
        # Create a directory for the namespace, if necessary
        if not os.path.exists(ns_dir):
            os.mkdir(ns_dir)

        # Create a file for each directive
        for name, (schema, handler, info) in directives.items():
            dir_file = os.path.join(ns_dir, name+'.stx')
            text = _directiveDocs(name, schema, handler, info)
            text += _subDirectiveDocs(subdirs, namespace, name)
            open(dir_file, 'w').write(text)

def _makeabs(path):
    """Make an absolute path from the possibly relative path."""
    if not path == os.path.abspath(path):
        cwd = os.getcwd()
        # This is for symlinks.
        if os.environ.has_key('PWD'):
            cwd = os.environ['PWD']
        path = os.path.normpath(os.path.join(cwd, path))    
    return path

def main(argv=sys.argv):
    try:
        opts, args = getopt.getopt(
            sys.argv[1:],
            'h:f:o:',
            ['help'])
    except getopt.error, msg:
        usage(1, msg)

    zcml_file = None
    output_dir = None
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage(0)
        elif opt in ('-o', ):
            output_dir = arg
        elif opt in ('-f', ):
            zcml_file = _makeabs(arg)
            if not os.path.exists(zcml_file):
                usage(1, 'The specified zcml file does not exist.')

    if zcml_file is None or output_dir is None:
        usage(0, "Both, the '-f' and '-o' option are required")

    # Generate the docs
    makedocs(output_dir, zcml_file)

if __name__ == '__main__':
    main()
