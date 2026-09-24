from pathlib import Path

from setuptools import find_packages, setup

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="django-react-templatetags",
    version="0.1.0",
    description="This django library allows you to add React components into your django templates.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Fröjd Interactive",
    author_email="contact@frojd.se",
    maintainer="buswedg",
    maintainer_email="buswedg@djangomango.com",
    url="https://github.com/djangomango/django-react-templatetags",
    packages=find_packages(exclude=("tests*", "example_django_react_templatetags")),
    include_package_data=True,
    install_requires=[
        "Django>=4.2",
    ],
    extras_require={
        "ssr": ["requests"],
        "hypernova": ["hypernova"],
    },
    license="MIT",
    zip_safe=False,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Framework :: Django",
        "Topic :: Utilities",
        "Programming Language :: JavaScript",
    ],
    python_requires=">=3.10",
)
