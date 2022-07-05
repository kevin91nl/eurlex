import setuptools
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setuptools.setup(
    name="eurlex",
    version="0.0.2",
    author="K.M.J. Jacobs",
    author_email="mail@kevinjacobs.nl",
    description="An EUR-Lex parser for Python.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kevin91nl/eurlex",
    packages=setuptools.find_packages(),
    include_package_data=True,
    classifiers=[],
    python_requires=">=3.6",
    install_requires=[],
)
