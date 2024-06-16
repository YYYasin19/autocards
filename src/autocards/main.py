from functools import lru_cache
from pathlib import Path
import os
from tqdm import tqdm
from autocards.llm import OpenAI
import click
from pypdf import PdfReader
import tiktoken
import genanki

TEMPLATES_PATH = Path("src/autocards/templates")
DEBUG_MODE = os.environ.get("DEBUG_MODE", False)

prompt_templates = {
    "de": {
        "system": open(TEMPLATES_PATH / "de" / "system.txt").read(),
        "assistant": open(TEMPLATES_PATH / "de" / "create_qa_pairs.txt").read(),
    },
    "en": {
        "system": open(TEMPLATES_PATH / "en" / "system.txt").read(),
        "assistant": open(TEMPLATES_PATH / "en" / "create_qa_pairs.txt").read(),
    },
}


class PDFSource:
    """
    Possible sources are PDFs or images. The user can also provide multiple sources for a single call
    """

    def __init__(self, src_path: Path, page_range: str = ""):
        self.src_path: Path = src_path
        self.reader = PdfReader(src_path)
        self.tokenizer = tiktoken.encoding_for_model("gpt-4")

        # parse page-range
        self.page_range = page_range
        start, end = page_range.split("-") if "-" in page_range else (None, None)
        self.start = max(0, int(start) - 1) if start else None
        self.end = int(end) if end else None

    @lru_cache
    def get_text(self) -> str:
        """Read the text of the PDF and return it"""
        text = "".join([page.extract_text() for page in self.reader.pages[self.start : self.end]])
        if DEBUG_MODE:
            self.src_path.with_suffix(".txt").write_text(text)
        return text

    def read_chunks(self, chunk_size: int = 6_000) -> list[str]:
        """Read the text of the PDF and return it in chunks"""
        text = self.get_text()
        tokens = len(self.tokenizer.encode(text))

        return [text[i : i + chunk_size] for i in range(0, tokens, chunk_size)]

    def get_snippet(self) -> str:
        """A small snipppet showing the start and end of the document"""
        text = self.get_text()
        start, end = text[:100], text[-100:]
        return f"{start} ... {end}"


class DeckCreator:
    def __init__(self, model: OpenAI, language: str = "de"):
        self.language = language
        self.model = model
        self.anki_model = genanki.Model(
            1607392319,
            "Simple Model",
            fields=[
                {"name": "Question"},
                {"name": "Answer"},
            ],
            templates=[
                {
                    "name": "Card 1",
                    "qfmt": "{{Question}}",
                    "afmt": '{{FrontSide}}<hr id="answer">{{Answer}}',
                },
            ],
        )

    def create_deck(self, name: str, source: PDFSource, output_path: Path, num_questions: int = 5, example: str = ""):
        deck = genanki.Deck(deck_id=123456, name=name)
        for chunk in tqdm(source.read_chunks(int(self.model.context_length * 0.8)), desc="Working through chunks..."):
            system = prompt_templates[self.language]["system"]
            prompt = prompt_templates[self.language]["assistant"].format(
                src_document_type="PDF", chunk=chunk, num_questions=num_questions, example=example
            )
            response: dict[str, list] = self.model.generate_json(system, prompt)
            # either 'ergebnis' or first key or empty list
            results = response.get("ergebnis", response.get(list(response.keys())[0], []))

            for result in results:
                deck.add_note(
                    genanki.Note(
                        model=self.anki_model,
                        # fields=[result["frage"], result["antwort"]], # TODO: split into question and answer
                        fields=list(result.values())[:2],
                    )
                )

        genanki.Package(deck).write_to_file(output_path.with_suffix(".apkg"))


@click.command()
@click.argument("deck-name", type=str, default="Test")
@click.argument("source_path", type=click.Path(exists=True, dir_okay=False), default=Path("data/example.pdf"))
@click.argument("output_path", type=click.Path(), default=Path("test_deck.apkg"))
@click.option("--page-range", type=str, default="")
@click.option("--num-questions", type=int, default=10)
@click.option("--language", type=str, default="en")
def main(deck_name: str, source_path: Path, page_range: str, output_path: Path, num_questions: int, language: str):
    source_path, output_path = Path(source_path), Path(output_path)  # Why do I have to cast this myself?
    print(f"Creating deck {deck_name} from {source_path} {f'[{page_range}]' if page_range else ''}")
    source = PDFSource(source_path, page_range)
    print(f"Source: {source.src_path.name} [{source.page_range}] \n\n{source.get_snippet()}")
    creator = DeckCreator(model=OpenAI(), language=language)
    creator.create_deck(deck_name, source, output_path, num_questions=num_questions)


if __name__ == "__main__":
    main()
