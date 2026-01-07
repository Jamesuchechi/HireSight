from pathlib import Path
from typing import Dict

from pyresparser import ResumeParser, resume_parser


class ResumeParsingError(Exception):
    pass


class ResumeService:
    @staticmethod
    def parse(file_path: str) -> Dict:
        p = Path(file_path)
        if not p.exists():
            raise ResumeParsingError("File not found")

        spaCy_module = resume_parser.spacy
        original_load = spaCy_module.load
        original_matcher = resume_parser.Matcher

        package_dir = Path(resume_parser.__file__).resolve().parent

        def patched_load(name, **kwargs):
            candidate_path = Path(name)
            if candidate_path.exists() and candidate_path.resolve() == package_dir:
                return original_load("en_core_web_sm", **kwargs)
            return original_load(name, **kwargs)

        class CompatMatcher(original_matcher):
            def add(self, label, on_match=None, *patterns):
                normalized = []
                if not patterns:
                    normalized = []
                elif len(patterns) == 1:
                    single = patterns[0]
                    normalized = single if isinstance(single, list) else [single]
                else:
                    for pat in patterns:
                        normalized.extend(pat if isinstance(pat, list) else [pat])
                return original_matcher.add(self, label, normalized, on_match=on_match)

        spaCy_module.load = patched_load
        resume_parser.Matcher = CompatMatcher
        try:
            data = ResumeParser(str(p)).get_extracted_data()
        except Exception as exc:
            raise ResumeParsingError(str(exc))
        finally:
            spaCy_module.load = original_load
            resume_parser.Matcher = original_matcher
        return data
