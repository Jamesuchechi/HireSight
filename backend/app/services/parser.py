from pyresparser import ResumeParser
from pathlib import Path
from typing import Dict


class ResumeParsingError(Exception):
    pass


class ResumeService:
    @staticmethod
    def parse(file_path: str) -> Dict:
        p = Path(file_path)
        if not p.exists():
            raise ResumeParsingError("File not found")
        try:
            data = ResumeParser(str(p)).get_extracted_data()
        except Exception as e:
            raise ResumeParsingError(str(e))
        return data
