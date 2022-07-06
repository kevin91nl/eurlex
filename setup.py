import setuptools
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setuptools.setup(
    name="eurlex",
    version="0.1.3",
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
    # Load the requirements.txt
    install_requires=[
        line.strip()
        for line in (this_directory / "requirements.txt").read_text().split("\n")
        if line.strip()
    ],
)
