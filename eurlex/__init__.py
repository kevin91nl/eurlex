import re
import rdflib
import requests
from SPARQLWrapper import SPARQLWrapper, JSON
import pandas as pd
import datetime
from xml.etree import ElementTree as ETree


def get_prefixes() -> dict:
    """Get a mapping from prefixes to URLs.

    Returns
    -------
    dict
        A mapping from prefixes to URLs.
    """
    return {
        "cdm": "http://publications.europa.eu/ontology/cdm#",
        "celex": "http://publications.europa.eu/resource/celex/",
        "owl": "http://www.w3.org/2002/07/owl#",
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "cellar": "http://publications.europa.eu/resource/cellar/",
        "skos": "http://www.w3.org/2004/02/skos/core#",
    }


def parse_article_paragraphs(article: str) -> dict:
    """Convert an article found on EUR-Lex to paragraphs.

    Parameters
    ----------
    article : str
        The article to parse.

    Returns
    -------
    dict
        Mapping from paragraph identifier to paragraph.

    Examples
    --------
    The following example parses an article into paragraphs. Make sure to use newlines instead of the 5 spaces which
    are used in the example.
    >>> parse_article_paragraphs("This is a test with a few paragraphs:     1. The first one     2. The second one")
    {None: 'This is a test with a few paragraphs:', '1.': 'The first one', '2.': 'The second one'}
    >>> parse_article_paragraphs("This is a test with a few paragraphs:     (1) The first one     (2) The second one")
    {None: 'This is a test with a few paragraphs:', '(1)': 'The first one', '(2)': 'The second one'}
    """
    paragraphs = dict()
    paragraph = None
    article = article.replace("     ", "\n")
    for line in article.split("\n"):
        match = re.match(r"^([0-9]+)[.]", line)
        if match:
            paragraph = match.group(0)
            line = ".".join(line.split(".")[1:]).strip()
        else:
            match = re.match(r"^[(]([0-9]+)[)]", line)
            if match:
                paragraph = match.group(0)
                line = ")".join(line.split(")")[1:]).strip()
        if paragraph not in paragraphs:
            paragraphs[paragraph] = []
        paragraphs[paragraph].append(line)
    paragraphs = {
        paragraph: "\n".join(paragraphs[paragraph]).strip() for paragraph in paragraphs
    }
    return paragraphs


def prepend_prefixes(query: str) -> str:
    """Prepend a query with prefixes.

    Parameters
    ----------
    query : str
        The query to prepend.

    Returns
    -------
    str
        Query prepended with the prefixes.

    Examples
    --------
    >>> 'prefix rdf' in prepend_prefixes("SELECT ?name WHERE { ?person rdf:name ?name }")
    True
    """
    return (
        "\n".join(
            [
                "prefix {}: <{}>".format(prefix, url)
                for prefix, url in get_prefixes().items()
            ]
        )
        + " "
        + query
    )


def run_query(query: str) -> dict:
    """Run the SPARQL query on EUR-Lex.

    Parameters
    ----------
    query : str
        The SPARQL query to run.

    Returns
    -------
    dict
        A dictionary containing the results.
    """
    sparql = SPARQLWrapper(
        "http://publications.europa.eu/webapi/rdf/sparql"
    )  # pragma: no cover
    sparql.setQuery(query)  # pragma: no cover
    sparql.setReturnFormat(JSON)  # pragma: no cover
    results = sparql.query().convert()  # pragma: no cover
    return results  # pragma: no cover


def convert_sparql_output_to_dataframe(sparql_results: dict) -> pd.DataFrame:
    """Convert SPARQL output to a DataFrame.

    Parameters
    ----------
    sparql_results : dict
        A dictionary containing the SPARQL results.

    Returns
    -------
    pd.DataFrame
        The DataFrame representation of the SPARQL results.

    Examples
    --------
    >>> convert_sparql_output_to_dataframe({'results': {'bindings': [{'subject': {'value': 'cdm:test'}}]}}).to_dict()
    {'subject': {0: 'cdm:test'}}
    """
    items = [
        {key: simplify_iri(item[key]["value"]) for key in item.keys()}
        for item in sparql_results["results"]["bindings"]
    ]
    return pd.DataFrame(items)


def get_celex_dataframe(celex_id: str) -> pd.DataFrame:
    """Get CELEX data delivered in a DataFrame.

    Parameters
    ----------
    celex_id : str
        The CELEX ID to get the data for.

    Returns
    -------
    pd.DataFrame
        A DataFrame containing the results.
    """
    graph = rdflib.Graph()  # pragma: no cover
    results = graph.parse(
        f"http://publications.europa.eu/resource/" f"celex/{str(celex_id)}?language=eng"
    )  # pragma: no cover
    items = [
        {key: simplify_iri(item[key]) for key in range(len(item))} for item in results
    ]  # pragma: no cover
    df = pd.DataFrame(items)  # pragma: no cover
    df.columns = ["s", "o", "p"]  # pragma: no cover
    return df  # pragma: no cover


def get_celex_id(
    slash_notation: str, document_type: str = "R", sector_id: str = "3"
) -> str:
    """Derive the CELEX ID from a slash notation like 2019/947.

    Parameters
    ----------
    slash_notation : str
        The slash notation of the document (like 2019/947).
    document_type : str
        The type of the document (e.g. "R" for regulations).
    sector_id : str
        The sector ID (e.g. 3).

    Returns
    -------
    str
        The CELEX ID

    Examples
    --------
    >>> get_celex_id('2019/947')
    '32019R0947'
    >>> get_celex_id('947/2019')
    '32019R0947'
    """
    term1, term2 = slash_notation.split("/")
    current_year = datetime.datetime.now().year
    term1 = int(term1)
    term2 = int(term2)
    term1_is_year = 1800 <= term1 <= current_year
    term2_is_year = 1800 <= term2 <= current_year
    year = term2
    document_id = term1
    if term1_is_year and not term2_is_year:
        year = term1
        document_id = term2
    if term2_is_year and not term1_is_year:
        year = term2
        document_id = term1
    return "{}{}{}{}".format(
        str(sector_id), year, document_type, str(document_id).zfill(4)
    )


def get_possible_celex_ids(
    slash_notation: str, document_type: str = None, sector_id: str = None
) -> list:
    """Get a list of possible CELEX IDs (given a slash notation like 2019/947).

    Parameters
    ----------
    slash_notation : str
        The slash notation of the document (like 2019/947).
    document_type : str
        The type of the document (e.g. "R" for regulations).
    sector_id : str
        The sector ID (e.g. 3).

    Returns
    -------
    list
        A list of possible CELEX IDs.

    Examples
    --------
    >>> '32019R0947' in get_possible_celex_ids("2019/947")
    True
    """
    sector_ids = (
        [str(i) for i in range(10)] + ["C", "E"]
        if sector_id is None
        else [str(sector_id)]
    )
    document_types = (
        ["L", "R", "E", "PC", "DC", "SC", "JC", "CJ", "CC", "CO"]
        if document_type is None
        else [document_type]
    )
    possible_ids = []
    for sector_id in sector_ids:
        for document_type in document_types:
            guess = get_celex_id(slash_notation, document_type, sector_id)
            possible_ids.append(guess)
    return possible_ids


def guess_celex_ids_via_eurlex(
    slash_notation: str, document_type: str = None, sector_id: str = None
) -> list:
    """Guess CELEX IDs for a slash notation by looking it up via EUR-Lex.

    Parameters
    ----------
    slash_notation : str
        The slash notation of the document (like 2019/947).
    document_type : str
        The type of the document (e.g. "R" for regulations).
    sector_id : str
        The sector ID (e.g. 3).

    Returns
    -------
    list
        A list of possible CELEX IDs.
    """
    slash_notation = "/".join(slash_notation.split("/")[:2])  # pragma: no cover
    queries = [
        "{ ?s owl:sameAs celex:" + celex_id + " . ?s owl:sameAs ?o }"
        for celex_id in get_possible_celex_ids(slash_notation, document_type, sector_id)
    ]  # pragma: no cover
    query = "SELECT * WHERE {" + " UNION ".join(queries) + "}"  # pragma: no cover
    query = prepend_prefixes(query)  # pragma: no cover
    results = run_query(query.strip())  # pragma: no cover
    celex_ids = []  # pragma: no cover
    for binding in results["results"]["bindings"]:  # pragma: no cover
        if "/celex/" in binding["o"]["value"]:  # pragma: no cover
            celex_id = binding["o"]["value"].split("/")[-1]  # pragma: no cover
            celex_ids.append(celex_id)  # pragma: no cover
    celex_ids = list(set(celex_ids))  # pragma: no cover
    return celex_ids  # pragma: no cover


def simplify_iri(iri: str) -> str:
    """Simplify prefixes in an IRI.

    Parameters
    ----------
    iri : str
        IRI to simplify.

    Returns
    -------
    str
        Simplified version where all prefixes are replaced by their shortcuts.

    Examples
    --------
    >>> simplify_iri("http://publications.europa.eu/ontology/cdm#test")
    'cdm:test'
    >>> simplify_iri("cdm:test")
    'cdm:test'
    """
    for prefix, url in get_prefixes().items():
        if iri.startswith(url):
            return prefix + ":" + iri[len(url) :]
    return iri


def get_html_by_cellar_id(cellar_id: str) -> str:
    """Retrieve HTML by CELLAR ID.

    Parameters
    ----------
    cellar_id : str
        The CELLAR ID to find HTML for.

    Returns
    -------
    str
        HTML found using the CELLAR ID.
    """
    url = "http://publications.europa.eu/resource/cellar/" + str(  # pragma: no cover
        cellar_id.split(":")[1] if ":" in cellar_id else cellar_id  # pragma: no cover
    )  # pragma: no cover
    response = requests.get(
        url,
        allow_redirects=True,
        headers={  # pragma: no cover
            "Accept": "text/html,application/xhtml+xml,application/xml",  # pragma: no cover
            "Accept-Language": "en",  # pragma: no cover
        },
    )  # pragma: no cover
    html = response.content.decode("utf-8")  # pragma: no cover
    return html  # pragma: no cover


def get_html_by_celex_id(celex_id: str) -> str:
    """Retrieve HTML by CELEX ID.

    Parameters
    ----------
    celex_id : str
        The CELEX ID to find HTML for.

    Returns
    -------
    str
        HTML found using the CELEX ID.
    """
    url = "http://publications.europa.eu/resource/celex/" + str(
        celex_id
    )  # pragma: no cover
    response = requests.get(
        url,
        allow_redirects=True,
        headers={  # pragma: no cover
            "Accept": "text/html,application/xhtml+xml,application/xml",  # pragma: no cover
            "Accept-Language": "en",  # pragma: no cover
        },
    )  # pragma: no cover
    html = response.content.decode("utf-8")  # pragma: no cover
    return html  # pragma: no cover


def get_tag_name(raw_tag_name: str) -> str:
    """Get the tag name.

    Parameters
    ----------
    raw_tag_name : str
        The original tag name.

    Returns
    -------
    str
        The parsed tag name.

    Examples
    --------
    >>> get_tag_name('tag}test')
    'test'
    """
    return raw_tag_name.split("}")[1] if "}" in raw_tag_name else raw_tag_name


def parse_modifiers(
    child: ETree.Element, ref: list = None, context: dict = None
) -> list:
    """Parse modifiers.

    Parameters
    ----------
    child : xml.etree.ElementTree.Element
        XML tree.
    ref : list
        References.
    context : dict
        Context.

    Returns
    -------
    list
        Results.

    Examples
    --------
    >>> parse_modifiers(ETree.fromstring('<p class="italic">Text</p>'))
    [{'text': 'Text', 'type': 'text', 'modifier': 'italic', 'ref': [], 'context': {}}]
    >>> parse_modifiers(ETree.fromstring('<p class="signatory">Text</p>'))
    [{'text': 'Text', 'type': 'text', 'modifier': 'signatory', 'ref': [], 'context': {}}]
    >>> parse_modifiers(ETree.fromstring('<p class="note">Text</p>'))
    [{'text': 'Text', 'type': 'text', 'modifier': 'note', 'ref': [], 'context': {}}]
    >>> parse_modifiers(ETree.fromstring('<p class="separator"></p>'))
    []
    """
    ref = [] if ref is None else ref
    context = {} if context is None else context
    output = []
    new_context = context.copy()
    if child.attrib["class"] == "italic":
        output.append(
            {
                "text": _get_text(child),
                "type": "text",
                "modifier": "italic",
                "ref": ref,
                "context": new_context.copy(),
            }
        )
    elif child.attrib["class"] == "signatory":
        output.append(
            {
                "text": _get_text(child),
                "type": "text",
                "modifier": "signatory",
                "ref": ref,
                "context": new_context.copy(),
            }
        )
    elif child.attrib["class"] == "note":
        output.append(
            {
                "text": _get_text(child),
                "type": "text",
                "modifier": "note",
                "ref": ref,
                "context": new_context.copy(),
            }
        )
    return output


def _get_text(child: ETree.Element) -> str:
    """Get text.

    Parameters
    ----------
    child : xml.etree.ElementTree.Element
        XML tree.

    Returns
    -------
    str
        Text.

    Examples
    --------
    >>> _get_text(ETree.fromstring('<p>Text</p>'))
    'Text'
    >>> _get_text(ETree.fromstring('<p><span>Text</span></p>'))
    'Text'
    """
    if len(child) == 1:
        return _get_text(child[0])
    if child.text is not None:
        return child.text.strip()


def parse_span(child: ETree.Element, ref: list = None, context: dict = None) -> list:
    """Parse a <span> or <p> tag.

    Parameters
    ----------
    child : xml.etree.ElementTree.Element
        XML tree.
    ref : list
        References.
    context : dict
        Context.

    Returns
    -------
    list
        Results.

    Examples
    --------
    >>> parse_span(ETree.fromstring('<p class="doc-ti">Text</p>'))
    [{'text': 'Text', 'type': 'doc-title', 'ref': [], 'context': {'document': 'Text'}}]
    >>> parse_span(ETree.fromstring('<p class="sti-art">Text</p>'))
    [{'text': 'Text', 'type': 'art-subtitle', 'ref': [], 'context': {'article_subtitle': 'Text'}}]
    >>> parse_span(ETree.fromstring('<p class="ti-art">Text</p>'))
    [{'text': 'Text', 'type': 'art-title', 'ref': [], 'context': {'article': 'Text'}}]
    >>> parse_span(ETree.fromstring('<p class="ti-grseq-1">Text</p>'))
    [{'text': 'Text', 'type': 'group-title', 'ref': [], 'context': {}}]
    >>> parse_span(ETree.fromstring('<p class="ti-grseq-1"><span class="bold">Text</span></p>'))
    [{'text': 'Text', 'type': 'group-title', 'ref': [], 'context': {}}]
    >>> parse_span(ETree.fromstring('<p class="ti-section-1">Text</p>'))
    [{'text': 'Text', 'type': 'section-title', 'ref': [], 'context': {}}]
    >>> parse_span(ETree.fromstring('<p class="normal">1. Text</p>'))
    [{'text': 'Text', 'type': 'text', 'ref': [], 'context': {'paragraph': '1'}}]
    >>> parse_span(ETree.fromstring('<p class="italic">Text</p>'))
    [{'text': 'Text', 'type': 'text', 'modifier': 'italic', 'ref': [], 'context': {}}]
    >>> parse_span(ETree.fromstring('<p>Text</p>'))
    []
    """
    ref = [] if ref is None else ref
    context = {} if context is None else context
    output = []
    if "class" not in child.attrib:
        return output
    if child.attrib["class"] == "doc-ti":
        if "document" not in context:
            context["document"] = ""
        context["document"] += _get_text(child)
        output.append(
            {
                "text": _get_text(child),
                "type": "doc-title",
                "ref": ref,
                "context": context.copy(),
            }
        )
    elif child.attrib["class"] == "sti-art":
        context["article_subtitle"] = _get_text(child)
        output.append(
            {
                "text": _get_text(child),
                "type": "art-subtitle",
                "ref": ref,
                "context": context.copy(),
            }
        )
    elif child.attrib["class"] == "ti-art":
        context["article"] = _get_text(child).replace("Article", "").strip()
        output.append(
            {
                "text": _get_text(child),
                "type": "art-title",
                "ref": ref,
                "context": context.copy(),
            }
        )
    elif child.attrib["class"].startswith("ti-grseq-"):
        output.append(
            {
                "text": _get_text(child),
                "type": "group-title",
                "ref": ref,
                "context": context.copy(),
            }
        )
        context["group"] = _get_text(child)
    elif child.attrib["class"].startswith("ti-section-"):
        output.append(
            {
                "text": _get_text(child),
                "type": "section-title",
                "ref": ref,
                "context": context.copy(),
            }
        )
        context["section"] = _get_text(child)
    elif child.attrib["class"] == "normal":
        text = _get_text(child)
        if re.match("^[0-9]+[.]", text):
            context["paragraph"] = text.split(".")[0]
            text = ".".join(text.split(".")[1:]).strip()
        output.append(
            {"text": text, "type": "text", "ref": ref, "context": context.copy()}
        )
    else:
        output.extend(parse_modifiers(child, ref, context))
    return output


def parse_article(tree: ETree.Element, ref: list = None, context: dict = None) -> list:
    """Parse an article.

    Parameters
    ----------
    tree : xml.etree.ElementTree.Element
        XML tree.
    ref : list
        References.
    context : dict
        Context.

    Returns
    -------
    list
        Results.

    Examples
    --------
    >>> parse_article(ETree.fromstring('<html><a>Link</a></html>'))
    [{'text': 'Link', 'type': 'link', 'ref': [], 'context': {}}]
    >>> parse_article(ETree.fromstring('<html><p class="doc-ti">Text</p></html>'))
    [{'text': 'Text', 'type': 'doc-title', 'ref': [], 'context': {'document': 'Text'}}]
    >>> parse_article(ETree.fromstring('<p><table><tbody><tr><td><p>1</p></td><td>2</td></tr></tbody></table></p>'))
    []
    >>> parse_article(ETree.fromstring('<html><div>Text</div></html>'))
    []
    >>> parse_article(ETree.fromstring('<html><head>Text</head></html>'))
    []
    >>> parse_article(ETree.fromstring('<html><body>Text</body></html>'))
    []
    """
    namespaces = {"html": "http://www.w3.org/1999/xhtml"}
    ref = [] if ref is None else ref
    context = {} if context is None else context
    output = []
    new_context = context.copy()
    for child in tree:
        if get_tag_name(child.tag) in ["a"]:
            output.append(
                {
                    "text": _get_text(child),
                    "type": "link",
                    "ref": ref,
                    "context": new_context.copy(),
                }
            )
        elif get_tag_name(child.tag) in ["p", "span"]:
            output.extend(parse_span(child, ref, new_context))
        elif get_tag_name(child.tag) == "table":
            results = child.findall(
                "html:tbody/html:tr/html:td", namespaces=namespaces
            ) + child.findall("tbody/tr/td", namespaces=namespaces)
            if (
                len(results) == 2
                and len(results[0]) == 1
                and get_tag_name(results[0][0].tag) == "p"
            ):
                key = None
                for subchild in results[0]:
                    key = _get_text(subchild)
                output.extend(parse_article(results[1], ref + [key], new_context))
            else:
                pass
        elif get_tag_name(child.tag) == "div":
            output.extend(parse_article(child, ref, new_context))
        elif get_tag_name(child.tag) in ["head", "hr"]:
            pass
        elif get_tag_name(child.tag) == "body":
            output.extend(parse_article(child, ref, context))
    return output


def parse_html(html: str) -> pd.DataFrame:
    """Parse EUR-Lex HTML into a DataFrame.

    Parameters
    ----------
    html : str
        The HTML to parse.

    Returns
    -------
    pd.DataFrame
        The parsed DataFrame

    Examples
    --------
    >>> parse_html('<html><body><p class="normal">Text</p></body></html>').to_dict(orient='records')
    [{'text': 'Text', 'type': 'text', 'ref': [], 'context': {}}]
    >>> parse_html('<html><p class="doc-ti">Text</p></html>').to_dict(orient='records')
    []
    >>> parse_html('<html').to_dict(orient='records')
    []
    >>> parse_html('<html><p class="doc-ti">ANNEX</p><p class="ti-grseq-1"><span>Group</span></p><p class="normal">Text</p></html>').to_dict(orient='records')
    [{'text': 'Text', 'type': 'text', 'ref': [], 'context': {'document': 'ANNEX', 'group': 'Group'}, 'document': 'ANNEX', 'group': 'Group'}]
    """
    try:
        tree = ETree.fromstring(html)
    except ETree.ParseError:
        return pd.DataFrame()
    records = []
    for item in parse_article(tree):
        for key, value in item["context"].items():
            item[key] = value
        records.append(item)
    df = pd.DataFrame.from_records(records)
    df = df[df.type == "text"] if "type" in df.columns else df
    return df


def get_regulations(limit: int = -1, shuffle: bool = False) -> list:
    """Retrieve regulations from EUR-Lex.

    Parameters
    ----------
    limit : int
        The maximum number of regulations to retrieve (default: no limit).
    shuffle : bool
        Whether to shuffle the retrieved regulations (default: False).

    Returns
    -------
    list
        A list of CELLAR IDs.
    """
    query = "select ?doc where {?doc cdm:work_has_resource-type <http://publications.europa.eu/"  # pragma: no cover
    query += (
        "resource/authority/resource-type/REG_IMPL> . }"
        + (" order by rand()" if shuffle else "")
        + (" limit " + str(limit) if limit > 0 else "")
    )  # pragma: no cover
    results = run_query(prepend_prefixes(query))  # pragma: no cover
    cellar_ids = []  # pragma: no cover
    for result in results["results"]["bindings"]:  # pragma: no cover
        cellar_ids.append(result["doc"]["value"].split("/")[-1])  # pragma: no cover
    return cellar_ids  # pragma: no cover


def process_paragraphs(paragraphs: list) -> pd.DataFrame:
    """Process the paragraphs.

    Parameters
    ----------
    paragraphs : list
        The list of currently downloaded paragraphs.

    Returns
    -------
    pd.DataFrame
        A DataFrame containing the processed paragraphs.

    Examples
    --------
    >>> process_paragraphs([]).to_dict(orient='records')
    []
    >>> process_paragraphs([{'celex_id': '1', 'paragraph': 'Done at 2021-11-25.'}]).to_dict(orient='records')
    []
    """
    df_paragraphs = pd.DataFrame.from_records(paragraphs)
    if "paragraph" not in df_paragraphs.columns:
        return df_paragraphs
    df_paragraphs = (
        df_paragraphs[~df_paragraphs.paragraph.str.startswith("Done at")]
        if len(df_paragraphs)
        else df_paragraphs
    )
    df_paragraphs = (
        df_paragraphs[~df_paragraphs.paragraph.str.startswith("It shall apply from")]
        if len(df_paragraphs)
        else df_paragraphs
    )
    df_paragraphs = (
        df_paragraphs[~df_paragraphs.paragraph.str.contains("is replaced by")]
        if len(df_paragraphs)
        else df_paragraphs
    )
    df_paragraphs = (
        df_paragraphs[~df_paragraphs.paragraph.str.endswith("is updated.")]
        if len(df_paragraphs)
        else df_paragraphs
    )
    df_paragraphs = (
        df_paragraphs[~df_paragraphs.paragraph.str.endswith("is deleted.")]
        if len(df_paragraphs)
        else df_paragraphs
    )
    df_paragraphs = (
        df_paragraphs[~df_paragraphs.paragraph.str.endswith("is removed.")]
        if len(df_paragraphs)
        else df_paragraphs
    )
    df_paragraphs = (
        df_paragraphs[~df_paragraphs.paragraph.str.endswith("is hereby repealed.")]
        if len(df_paragraphs)
        else df_paragraphs
    )
    df_paragraphs = (
        df_paragraphs[~df_paragraphs.paragraph.str.endswith("are updated.")]
        if len(df_paragraphs)
        else df_paragraphs
    )
    df_paragraphs = (
        df_paragraphs[~df_paragraphs.paragraph.str.endswith("are deleted.")]
        if len(df_paragraphs)
        else df_paragraphs
    )
    df_paragraphs = (
        df_paragraphs[~df_paragraphs.paragraph.str.endswith("are removed.")]
        if len(df_paragraphs)
        else df_paragraphs
    )
    df_paragraphs = (
        df_paragraphs[~df_paragraphs.paragraph.str.contains("is amended ")]
        if len(df_paragraphs)
        else df_paragraphs
    )
    df_paragraphs = (
        df_paragraphs[~df_paragraphs.paragraph.str.contains("is repealed with")]
        if len(df_paragraphs)
        else df_paragraphs
    )
    df_paragraphs = (
        df_paragraphs[df_paragraphs.paragraph.str.endswith(".")]
        if len(df_paragraphs)
        else df_paragraphs
    )
    df_paragraphs = (
        df_paragraphs[
            df_paragraphs.paragraph.apply(lambda text: text[0].upper() == text[0])
        ]
        if len(df_paragraphs)
        else df_paragraphs
    )
    df_paragraphs = (
        df_paragraphs[~df_paragraphs.paragraph.str.contains("‘")]
        if len(df_paragraphs)
        else df_paragraphs
    )
    df_paragraphs = (
        df_paragraphs[~df_paragraphs.paragraph.str.contains("’")]
        if len(df_paragraphs)
        else df_paragraphs
    )
    df_paragraphs = (
        df_paragraphs[df_paragraphs.paragraph.apply(len) >= 100]
        if len(df_paragraphs)
        else df_paragraphs
    )
    df_paragraphs = (
        df_paragraphs.drop_duplicates("paragraph")
        if len(df_paragraphs)
        else df_paragraphs
    )
    return df_paragraphs
