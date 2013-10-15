from setuptools import setup, find_packages
import sys, os

version = '1.0dev'
shortdesc = 'Example Appengine Pyramid App'
longdesc = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read()
longdesc += open(os.path.join(os.path.dirname(__file__), 'LICENSE.rst')).read()

setup(name='example_app',
      version=version,
      description=shortdesc,
      long_description=longdesc,
      classifiers=[
            'Operating System :: OS Independent',
            'Programming Language :: Python', 
      ],
      author='Jens W. Klein',
      author_email='jk@kleinundpartner.at',
      url=u'http://kleinundpartner.at',
      packages=find_packages('src'),
      package_dir = {'': 'src'},
      namespace_packages=[],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
      ],
      message_extractors={
          '.': [
              ('**.py', 'lingua_python', None),
              ('**.pt', 'lingua_xml', None),
              ('**.html', 'jinja2.ext.babel_extract', dict(encoding='utf-8')),
              ('**.jinja2', 'jinja2.ext.babel_extract', dict(encoding='utf-8')),
          ]
      },
      extras_require = dict(
          test=[
              'interlude',
              'ipython',
              'plone.testing',
              'WebTest',
          ]
      ),
)
