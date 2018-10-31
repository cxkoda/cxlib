"""
Lookup journal abbreviations from ADS site, parse bibtex file, and add journal abbreviations
taken from https://gist.github.com/wtbarnes/cb543af8cbe53bd65d761177bcc83a86
modified by cxkoda
"""
import requests
import unicodedata
import itertools
import argparse
import copy

from bs4 import BeautifulSoup
import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase
from bibtexparser.latexenc import unicode_to_latex, unicode_to_crappy_latex1


ADS_URL_REFEREED = 'http://adsabs.harvard.edu/abs_doc/refereed.html'
ADS_URL_NON_REFEREED = 'http://adsabs.harvard.edu/abs_doc/non_refereed.html'


def get_abbreviations(abbrev_url):
    """
    Scrape and parse abbreviations from ADS page
    """
    html = requests.get(abbrev_url).text
    html = BeautifulSoup(html, 'lxml').pre
    abbreviations = {}
    for child in html:
        if type(child).__name__.lower() != 'tag':
            continue
        abbrev = ' '.join(child.get_text().strip().split())
        title = remove_unicode(' '.join(str(child.next_sibling).strip().split()))
        abbreviations[title] = abbrev

    return abbreviations


def remove_unicode(unicode_string):
    """
    Strip accents, umlauts, etc., from unicode characters
    """
    return unicodedata.normalize('NFKD', unicode_string).encode('ascii', 'ignore').decode('utf-8')


def tex_filter(string):
    """
    Any replacement, filtering in the journal abbreviations
    """
    return string.replace('&', '\&')


def latex_to_unicode(string):
    """
    Convert a LaTeX string to unicode equivalent.

    NOTE: Taken from latest bibtexparser codebase
    (https://github.com/sciunto-org/python-bibtexparser),
    but using the version in pip as the newest version seems
    to have some bugs. This could be a problem with new releases
    on PyPI
    """
    if '\\' in string or '{' in string:
        for k, v in itertools.chain(unicode_to_crappy_latex1, unicode_to_latex):
            if v in string:
                string = string.replace(v, k)

    # If there is still very crappy items
    if '\\' in string:
        for k, v in unicode_to_crappy_latex2:
            if v in string:
                parts = string.split(str(v))
                for key, string in enumerate(parts):
                    if key+1 < len(parts) and len(parts[key+1]) > 0:
                        # Change order to display accents
                        parts[key] = parts[key] + parts[key+1][0]
                        parts[key+1] = parts[key+1][1:]
                string = k.join(parts)

    # Place accents at correct position
    # LaTeX requires accents *before* the character. Unicode requires accents
    # to be *after* the character. Hence, by a raw conversion, accents are not
    # on the correct letter, see
    # https://github.com/sciunto-org/python-bibtexparser/issues/121.
    # We just swap accents positions to fix this.
    cleaned_string = []
    i = 0
    while i < len(string):
        if not unicodedata.combining(string[i]):
            # Not a combining diacritical mark, append it
            cleaned_string.append(string[i])
            i += 1
        elif i < len(string) - 1:
            # Diacritical mark, append it but swap with next character
            cleaned_string.append(string[i + 1])
            cleaned_string.append(string[i])
            i += 2
        else:
            # If trailing character is a combining one, just discard it
            i += 1

    # Normalize unicode characters
    # Also, when converting to unicode, we should return a normalized Unicode
    # string, that is always having only compound accentuated character (letter
    # + accent) or single accentuated character (letter with accent). We choose
    # to normalize to the latter.
    cleaned_string = unicodedata.normalize("NFC", "".join(cleaned_string))

    # Remove any left braces
    cleaned_string = cleaned_string.replace("{", "").replace("}", "")

    return cleaned_string


check_rules = [
    lambda journal_name: journal_name.replace('&', 'and'),
    lambda journal_name: journal_name.replace('The', '').lstrip(),
]

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input_bibfile", help="Path to bibtex file to be read")
    parser.add_argument("-o", "--output_bibfile", help="Path to bibtex file to write")
    args = parser.parse_args()
    # Abbreviations from ADS web
    abbrev_ref = get_abbreviations(ADS_URL_REFEREED)
    abbrev_non_ref = get_abbreviations(ADS_URL_NON_REFEREED)
    abbreviations = {**abbrev_non_ref, **abbrev_ref}
    # Add any missing ones here
    abbreviations['The Astrophysical Journal Letters'] = 'ApJL'
    abbreviations['The Astronomy and Astrophysics Review'] = 'ApJL'

    # Parse bibtex file
    with open(args.input_bibfile, 'r') as f:
        bib = f.read()
    bib = bibtexparser.loads(bib)

    # Replace journal name entries
    for entry in bib.entries:
        journal_key = ''
        if 'journal' in entry.keys():
            journal_key = 'journal'
        elif 'journaltitle' in entry.keys():
            journal_key = 'journaltitle'
        else:
            print('No journal title found for %s' % entry['ID'])
            continue

        journal_name = remove_unicode(latex_to_unicode(entry[journal_key]))
        possible_names = [rule(journal_name) for rule in check_rules]
        abbrev_found = False

        for journal_name in possible_names:
            if journal_name in abbreviations.keys():
                entry[journal_key] = tex_filter(abbreviations[journal_name])
                break
            else:
                print('No abbreviation found for %s' % journal_name)

    # Write new bibtex file
    writer = BibTexWriter()
    with open(args.output_bibfile, 'w') as f:
        f.write(writer.write(bib))
