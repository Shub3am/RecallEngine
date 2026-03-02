#Interverted Indexer class for recall engine. This class will be responsible for building the index and retrieving documents based on the index.
import pickle
import json
from recall_engine.cli.misc import CACHE_PATH, dataset_loader

class Indexer:
    def __init__(self, docmap: dict[str, str], index: dict[str, list[str]]) -> None:
        self.doc_map = docmap
        self.index = index
        self.default_file_path = CACHE_PATH
        
    def __add_document(self, doc_id: str, text: str) -> None:
        pass
    def get_document(self, term: str) -> list[str]:
        pass
    def build(self, docPath: str, fileType: str = "json", docIdKey: str = "id", docAttrKeys: list[str] | None = None) -> None:
        if docAttrKeys is None:
            docAttrKeys = []
        try: 
            documents: list[dict[str,str]] = dataset_loader(docPath, fileType)
            if (type(documents) is not list):
                raise ValueError(f"Expected a list of documents, but got {type(documents)}")
            for document in documents:
                doc_id = document[docIdKey]
                doc_text = ""
                if docAttrKeys:
                    build_doc_text: list[str]= []
                    for attr in docAttrKeys:
                        if attr not in document:
                            raise ValueError(f"Attribute {attr} not found in document {doc_id}. Skipping this document.")
                        build_doc_text.append(str(document[attr]))
                    doc_text = " ".join(build_doc_text)
                else:
                
                    build_doc_text: list[str] = []
                    for key, value in document.items():
                        if key == docIdKey:
                            continue

                        if type(value) is str and value != "":
                            build_doc_text.append(str(value))

                    doc_text = " ".join(build_doc_text)
                if not doc_text.strip():
                    print(f"Warning: Document {doc_id} has empty text. Skipping.")
                    return
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

    