# EUR-Lex Parser

<p>
    <a href="https://github.com/kevin91nl/eurlex/actions/workflows/building.yaml"><img src="https://github.com/kevin91nl/eurlex/actions/workflows/building.yaml/badge.svg" alt="Building" height="18"></a>
    <a href="https://badge.fury.io/py/eurlex"><img src="https://badge.fury.io/py/eurlex.svg" alt="PyPI version" height="18"></a>
    <a href=https://github.com/ambv/black><img src="https://img.shields.io/badge/code%20style-black-000000.svg" height="18"></a>
</p>

An EUR-Lex parser for Python.

## Usage

You can install this package as follows:

```bash
pip install -U eurlex
```

After installing this package, you can download and parse any document from EUR-Lex. For example, the [32019R0947 regulation](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32019R0947):

```python
from eurlex import get_html_by_celex_id, parse_html

# Retrieve and parse the document with CELEX ID "32019R0947" into a Pandas DataFrame
celex_id = "32019R0947"
html = get_html_by_celex_id(celex_id)
df = parse_html(html)

# Get the first line of Article 1
df_article_1 = df[df.article == "1"]
df_article_1_line_1 = df_article_1.iloc[0]

# Display the subtitle of Article 1
print(df_article_1_line_1.article_subtitle)
>>> "Subject matter"

# Display the corresponding text
print(df_article_1_line_1.text)
>>> "This Regulation lays down detailed provisions for the operation of unmanned aircraft systems as well as for personnel, including remote pilots and organisations involved in those operations."
```

Every document on EUR-Lex displays a CELEX number at the top of the page. More information on CELEX numbers can be found on the [EUR-Lex website](https://eur-lex.europa.eu/content/tools/eur-lex-celex-infographic-A3.pdf).

For more information about the methods in this package, see the [unit tests](https://github.com/kevin91nl/eurlex/tree/main/tests) and [doctests](https://github.com/kevin91nl/eurlex/blob/main/eurlex/__init__.py).

### Data Structure

The following columns are available in the parsed dataframe:

- `text`: The text
- `type`: The type of the data
- `document`: The document in which the text is found
- `article`: The article in which the text is found
- `article_subtitle`: The subtitle of the article (when available)
- `ref`: The indentation level of the text within the article (e.g. `["(1)", "(a)"]` when the text is found under paragraph `(1)`, subparagraph `(a)`)

In some cases, additional fields are available. For example, the `group` field which contains the bold text under which a text is found.

## Code Contribution

Feel free to send any issues, ideas or pull requests.