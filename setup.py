from pathlib import Path

from setuptools import find_packages, setup

# Path to the current file
here = Path(__file__).resolve().parent

# Get the long description from the README.md file
long_description = (here / "README.md").read_text(encoding="utf-8")

setup(
    name="ckanext-restricted",
    version="0.0.1",
    description="Eawag access restriction. Depends on ckanext-scheming and ckanext-repeating.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/eawag-rdm/ckanext-restricted",
    author="Christian Foerster",
    author_email="Christian.Foerster@eawag.ch",
    license="AGPL-3.0-or-later",
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
    ],
    keywords="CKAN Eawag dataset restriction custom",
    packages=find_packages(exclude=["contrib", "docs", "tests*"]),
    namespace_packages=["ckanext"],
    python_requires=">=3.9",
    install_requires=[
        # Dependencies should be listed in a `requirements.txt` file.
    ],
    include_package_data=True,
    package_data={},
    data_files=[],
    entry_points={
        "ckan.plugins": [
            "restricted=ckanext.restricted.plugin:RestrictedPlugin",
        ],
        "babel.extractors": [
            "ckan = ckan.lib.extract:extract_ckan",
        ],
    },
    message_extractors={
        "ckanext": [
            ("**.py", "python", None),
            ("**.js", "javascript", None),
            ("**/templates/**.html", "ckan", None),
        ],
    },
)
