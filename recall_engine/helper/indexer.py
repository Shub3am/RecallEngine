#Interverted Indexer class for recall engine. This class will be responsible for building the index and retrieving documents based on the index.
import pickle
import json
from recall_engine.cli.misc import CACHE_PATH, dataset_loader, dataset_loader_json
from recall_engine.helper.tokenizer import Tokenizer

class Indexer:
    """
    Indexer class for building and managing inverted indices over document collections.
    This class provides functionality to build, load, and save inverted indices that map
    terms to document IDs, enabling efficient document retrieval based on term queries.
    Attributes:
        doc_map (list[dict[str, str]]): Maps document IDs to their text content or structured data.
            Example Structures:
            - Simple: [{"doc_id_1": "Document text content"}, {"doc_id_2": "More text"}]
            - Structured: [
                {"id": "doc_id_1", "title": "Title 1", "body": "Document text content"},
                {"id": "doc_id_2", "title": "Title 2", "body": "More text"}
              ]
        index (dict[str, list[int]]): Inverted index mapping terms to lists of document IDs.
            Example Structure: {
                "term1": ["doc_array_index_1", "doc_array_index_3"],
                "term2": ["doc_array_index_2"],
                "term3": ["doc_array_index_1", "doc_array_index_2", "doc_array_index_3"]
            }
            Where each term key maps to a list of document IDs containing that term.
        default_file_path (str): Default file path for saving and loading index data.
    Methods:
        __init__(document_index, document_map, filePath): Initialize the Indexer with document map and index.
        __add_document(doc_id, text): Add a document to the index (private method).
        get_document(term): Retrieve document IDs containing a specific term.
        build(docPath, fileType, docIdKey, docAttrKeys): Build index from a data file.
        load(filepath): Load a previously saved index from disk.
        save(filepath): Persist the current index to disk.
    """
    def __init__(self, document_index: dict[str, list[int]] = {}, document_map: list[dict[str,str]] = [], filePath: str = CACHE_PATH) -> None:
        self.index = document_index
        self.doc_map = document_map
        self.default_file_path = filePath
        self.tokenizer = Tokenizer()
        
    def __add_document(self, doc_id: int, text: str) -> None:
        """Add a document to the index by tokenizing its text and updating term mappings.
        
        Args:
            doc_id: Unique identifier for the document (e.g., array index).
            text: Raw text content of the document to be indexed.
        """
        tokens = self.tokenizer.tokenize(text)
        for token in tokens:
            if token not in self.index:
                self.index[token] = []
            if doc_id not in self.index[token]:
                self.index[token].append(doc_id)
    def build(self, docPath: str, fileType: str = "json", docIdKey: str = "id", docAttrKeys: list[str] = ["title", "body"]) -> None:
        """Build the inverted index from a data file containing documents.
        
        Args:
            docPath: File path to the document collection (e.g., JSON file).
            fileType: Type of the input file (default is "json").
            docIdKey: Key in the document dict that contains the unique document ID (default is "id").
            docAttrKeys: List of keys in the document dict whose values should be concatenated for indexing (default is ["title", "body"]).
        """
        if fileType == "json":
            self.doc_map = dataset_loader_json(docPath)
        else:
            self.doc_map = dataset_loader(docPath)
        
        for idx, doc in enumerate(self.doc_map):
            # Extract text to index based on specified attribute keys
            text_to_index = " ".join([doc.get(attr, "") for attr in docAttrKeys])
            self.__add_document(idx, text_to_index)