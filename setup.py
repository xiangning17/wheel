# -*- coding: utf-8 -*-

import setuptools

# with open("README.md", "r") as fh:
#     long_description = fh.read()

long_desc = """
# wheel 自用python工具库
===============

"""

def read_install_requires():
    reqs = []
    return reqs

setuptools.setup(
    name="xn-wheel",
    version="0.0.1",
    author="Xiang Ning",
    author_email="xiangning17@foxmail.com",
    description="自用python工具库",
    long_description=long_desc,
    long_description_content_type="text/markdown",
    url="https://github.com/xiangning17/wheel",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    keywords=('wheel', 'xiangning', '向宁'),
    install_requires=read_install_requires(),
)
