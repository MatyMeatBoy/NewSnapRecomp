"""MENU-LANG-01: every language table of the in-game menu has the Spanish table's texts, id for id."""
import re
import unittest
from pathlib import Path

from newsnap.upstream import ROOT, UPSTREAM

OVERLAYS = ROOT / 'newsnap/overlays'
LANGUAGES = {'es': 'text_es', 'fr': 'text_fr', 'de': 'text_de', 'it': 'text_it', 'ja': 'text_ja', 'ko': 'text_ko',
             'zh_hant': 'text_zh_hant'}
ENTRY = re.compile(r'\[(UI_[A-Z0-9_]+)\]\s*=\s*((?:"(?:[^"\\]|\\.)*"\s*)+)')
LITERAL = re.compile(r'"((?:[^"\\]|\\.)*)"')
SPECIFIER = re.compile(r'%[-0-9.]*[a-zA-Z%]')


def table(language):
    text = (OVERLAYS / f'ui_text_{language}.inc').read_text(encoding='utf-8')
    return text, [(name, ''.join(LITERAL.findall(value))) for name, value in ENTRY.findall(text)]


class MenuLanguages(unittest.TestCase):
    def test_every_table_has_the_same_texts_and_format_specifiers(self):
        _, spanish = table('es')
        self.assertGreater(len(spanish), 400)
        for language, name in LANGUAGES.items():
            text, entries = table(language)
            self.assertIn(f'static const char *const {name}[UI_TEXT_COUNT] = {{', text)
            self.assertEqual(text.count('SWKBD('), 1, language)
            self.assertEqual([n for n, _ in entries], [n for n, _ in spanish], language)
            for (ident, value), (_, reference) in zip(entries, spanish):
                self.assertTrue(value, f'{language} {ident} is empty')
                self.assertEqual(SPECIFIER.findall(value), SPECIFIER.findall(reference), f'{language} {ident}')

    def test_each_table_replaces_its_keyboard_only_row(self):
        from newsnap.snap_menu_adapt import edits
        upstream = (UPSTREAM / 'runtime/ui_text.c').read_text(encoding='utf-8')
        pairs = dict(edits()['runtime/ui_text.c'])
        for language in LANGUAGES:
            include = f'#include "ui_text_{language}.inc"\n'
            old = [a for a, b in pairs.items() if b == include]
            self.assertEqual(len(old), 1, language)
            self.assertEqual(upstream.count(old[0]), 1, language)


if __name__ == '__main__':
    unittest.main()
