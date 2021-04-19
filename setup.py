from setuptools import setup

setup(name='rdf_fixer',
      version='1.04b',
      description='chemical rdf fixer for reaxys and scifinder exports',
      #url='',
      author='Alexander Minidis, DocMinus',
      author_email='alex@pharmakarma.org',
      license='MIT',
      packages=['rdfmodule'],
      install_requires=[
          #'rdkit', #not available through git but conda
          'pandas'
      ],
      zip_safe=False,
      )