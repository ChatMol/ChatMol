from setuptools import setup, find_packages

setup(
    name='chatmol',
    version='0.2.3',
    packages=find_packages(),
    install_requires=[
        'requests', 
        'openai>=1.3.9',
        'anthropic>=0.19.1',
        'streamlit>=1.35.0'
    ],
    author='The ChatMol Team',
    author_email='jinyuansun@chatmol.org',
    description='A package for ChatMol',
    keywords='chatmol',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown', 
    url='https://github.com/JinyuanSun/ChatMol/chatmol_pkg',
)
