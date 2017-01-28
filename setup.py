# -*- coding: utf-8 -*-
from os import path
from setuptools import setup, find_packages
from setup_requirements import install_requires, extras_require, dependency_links

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."



if __name__ == '__main__':
    # Get the version number
    aiida_folder = path.split(path.abspath(__file__))[0]
    fname = path.join(aiida_folder, 'aiida', '__init__.py')
    with open(fname) as aiida_init:
        ns = {}
        exec(aiida_init.read(), ns)
        aiida_version = ns['__version__']

    bin_folder = path.join(aiida_folder, 'bin')
    setup(
        name='aiida',
        url='http://www.aiida.net/',
        license='MIT License',
        author="The AiiDA team",
        author_email='developers@aiida.net',
        include_package_data=True, # puts non-code files into the distribution, reads list from MANIFEST.in
        classifiers=[
            'License :: OSI Approved :: MIT License',
            'Programming Language :: Python',
            'Programming Language :: Python :: 2',
        ],
        version=aiida_version,
        install_requires=install_requires,
        extras_require=extras_require,
        dependency_links=dependency_links,
        packages=find_packages(),
        entry_points={
            'console_scripts': [
                'verdi=aiida.cmdline.verdilib:run',
                'verdic = aiida.cmdline.verdic:verdic'
            ],
            # following are AiiDA plugin entry points:
            'aiida.calculations': [],
            'aiida.parsers': [],
            'aiida.cmdline': [],
            'aiida.cmdline.verdi': [
                'run = aiida.cmdline.commands2.run:run',
                'setup = aiida.cmdline.commands2.setup:setup',
                'quicksetup = aiida.cmdline.commands2.quicksetup:quicksetup',
                'code = aiida.cmdline.commands2.code:code'
            ],
            'aiida.schedulers': [],
            'aiida.transports': [],
            'aiida.workflows': [],
        },
        scripts=['bin/runaiida'],
        long_description=open(path.join(aiida_folder, 'README.rst')).read(),
    )
