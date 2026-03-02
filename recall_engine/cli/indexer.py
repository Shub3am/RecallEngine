#Interverted Indexer class for recall engine. This class will be responsible for building the index and retrieving documents based on the index.
import pickle
import json
from recall_engine.cli.misc import CACHE_PATH

class Indexer:
    def __init__(self, docmap: dict[str, str], index: dict[str, list[str]]) -> None:
        self.doc_map = docmap
        self.index = index
        self.default_file_path = CACHE_PATH
        
    def __add_document(self, doc_id: str, text: str) -> None:
        pass
    def get_document(self, term: str) -> list[str]:
        pass
    def build(self, tokens, documents: dict[str, str]) -> None:
        pass
    
    def load(self, filepath: str = "") -> None:
        if not filepath:
            filepath = self.default_file_path
        
        with open(filepath, "rb") as f:
            file_dump = pickle.load(f)
            data = json.loads(file_dump)
            self.doc_map = data["doc_map"]
            self.index = data["index"]
    
    def save(self, filepath: str = "") -> None:
        if not filepath:
            filepath = self.default_file_path
        
        with open(filepath, "wb") as f:
            file_dump = json.dumps({
                "doc_map": self.doc_map,
                "index": self.index
            })
            pickle.dump(file_dump, f)

    