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
        doc_map (dict[str, str]): Maps document IDs to their text content or structured data.
            Example Structures:
            - Simple: {"doc_id_1": "document text content", "doc_id_2": "more text"}
            - Structured: {
                "doc_id_1": {"title": "Document Title", "body": "document body text"},
                "doc_id_2": {"title": "Another Title", "body": "another body"}
              }
        index (dict[str, list[str]]): Inverted index mapping terms to lists of document IDs.
            Example Structure: {
                "term1": ["doc_id_1", "doc_id_3"],
                "term2": ["doc_id_2"],
                "term3": ["doc_id_1", "doc_id_2", "doc_id_3"]
            }
            Where each term key maps to a list of document IDs containing that term.
        default_file_path (str): Default file path for saving and loading index data.
    Methods:
        __init__(docmap, index): Initialize the Indexer with document map and index.
        __add_document(doc_id, text): Add a document to the index (private method).
        get_document(term): Retrieve document IDs containing a specific term.
        build(docPath, fileType, docIdKey, docAttrKeys): Build index from a data file.
        load(filepath): Load a previously saved index from disk.
        save(filepath): Persist the current index to disk.
    """
    
    def __init__(self, docmap: dict[str, str], index: dict[str, list[str]]) -> None:
        self.doc_map = docmap 
        self.index = index 
        self.default_file_path = CACHE_PATH
        
    def __add_document(self, doc_id: str, text: str) -> None:
        self.index = doc_id
        self.doc_map[doc_id] = text
        
        pass
    def get_document(self, term: str) -> list[str]:
        pass
    def build(self, docPath: str, fileType: str = "json", docIdKey: str = "id", docAttrKeys: list[str] | None = None) -> None:
        if docAttrKeys is None:
            docAttrKeys = []
        try: 
            if(fileType not in ["json", "text"]):
                raise NotImplementedError(f"Unsupported file type: {fileType}")
            if fileType == "json":
                documents: list[dict[str,str]] = dataset_loader_json(docPath)            
                if (type(documents) is not list):
                    raise ValueError(f"Expected a list of documents, but got {type(documents)}")
                for document in documents:
                    doc_id = document[docIdKey]
                    doc_text = " ".join([document[key] for key in docAttrKeys])
                    self.__add_document(doc_id, doc_text)
               
        except Exception as e:
            print(f"Error Building Index: {e}")
            exit()
    
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

    