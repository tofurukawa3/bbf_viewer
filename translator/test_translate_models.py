import unittest
import sys
import os

# Appending the translator directory to the path so we can import the module correctly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from translate_models import clean_text

class TestCleanText(unittest.TestCase):
    def test_clean_text_basic(self):
        # Basic text without spaces
        self.assertEqual(clean_text("Hello World"), "Hello World")
        
    def test_clean_text_newlines(self):
        # Text with newlines and indentation that XML often has
        xml_text = "\n        This is a sentence\n        that spans across multiple\n        lines in an XML file.\n    "
        self.assertEqual(clean_text(xml_text), "This is a sentence that spans across multiple lines in an XML file.")
        
    def test_clean_text_tabs_and_spaces(self):
        # Text with mixed tabs, spaces, and newlines
        messy_text = "\t\tSome   text\n\n\twith    irregular spacing.   "
        self.assertEqual(clean_text(messy_text), "Some text with irregular spacing.")

    def test_clean_text_empty(self):
        self.assertEqual(clean_text(None), "")
        self.assertEqual(clean_text(""), "")
        self.assertEqual(clean_text("   \n \t "), "")

if __name__ == '__main__':
    unittest.main()
