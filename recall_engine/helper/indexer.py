#Interverted Indexer class for recall engine. This class will be responsible for building the index and retrieving documents based on the index.
import pickle
import json
from recall_engine.cli.misc import CACHE_PATH, dataset_loader_json
from recall_engine.helper.tokenizer import Tokenizer

class Indexer:
    """
    Indexer class for building and managing inverted indices over document collections.
    This class provides functionality to build, load, and save inverted indices that map
    terms to document IDs, enabling efficient document retrieval based on term queries.
    Attributes:
        doc_map (dict[str, dict[str|int, str]]): Maps document IDs to their text content or structured data.
            Example Structures:
            - Structured: {
                "doc_id_1": {"title": "Title 1", "body": "Document text content"},
                "doc_id_2": {"title": "Title 2", "body": "More text"}
              }
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
    def __init__(self, document_index: dict[str, list[str]] = {}, document_map: dict[str,dict[str,str]] = {}, filePath: str = CACHE_PATH) -> None:
        self.index = document_index
        self.doc_map = document_map
        self.default_file_path = filePath
        self.tokenizer = Tokenizer()
        
    def __add_document(self, doc_id: str, text: str) -> None:
        """Add a document to the index by tokenizing its text and updating term mappings.
        
        Args:
            doc_id: Unique identifier for the document (e.g., array index).
            text: Raw text content of the document to be indexed.
        
        Example progression with sample data:
            doc_id = "550"
            text = "The Matrix science fiction action"
        """
        
        # Step 1: Tokenize the text into individual words
        # tokens = ["matrix", "science", "fiction", "action"]
        tokens = self.tokenizer.tokenize(text)
        
        # Step 2: Iterate through each token
        for token in tokens:
            # Step 3a: Check if token exists in index, if not create empty list
            # First iteration: "matrix" not in index → self.index["matrix"] = []
            if token not in self.index:
                self.index[token] = []
            
            # Step 3b: Check if doc_id already exists for this token to avoid duplicates
            # First iteration: "550" not in self.index["matrix"] → append it
            # self.index["matrix"] = ["550"]
            if doc_id not in self.index[token]:
                self.index[token].append(doc_id)
        
        # Final state of index after processing all tokens:
        # self.index = {
        #     "matrix": ["550"],
        #     "science": ["550"],
        #     "fiction": ["550"],
        #     "action": ["550"]
        # }
    def build(self, docPath: str, docIdKey: str = "id", excludeDocKeys: list[str] = ["id"]) -> None:
        """Build the inverted index from a data file containing documents.
        
        Args:
            docPath: File path to the document collection (e.g., JSON file).
            excludeDocKeys: List of keys in the document dict to exclude from indexing (default is ["id"]).
        """
        dataset = dataset_loader_json(docPath)

        for doc in dataset:
            doc_id = str(doc[docIdKey])
            # Combine all text fields except the excluded keys into a single string for indexing
            text_content = " "
            for key, value in doc.items():
                if key not in excludeDocKeys:
                    text_content += str(value) + " "
            self.doc_map[doc_id] = doc
            self.__add_document(doc_id, text_content.strip())