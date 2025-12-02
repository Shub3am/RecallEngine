import json


PROJECT_ROOT = "./recall_engine"
STOP_WORDS_PATH = f"{PROJECT_ROOT}/helper/stop_words.txt"
CACHE_PATH = f"{PROJECT_ROOT}/cache/cache.pkl"
DATA_PATH = f"./data/movies.json"
def get_stop_words() -> list[str]:
    try:
       
        with open(STOP_WORDS_PATH) as words:
            words = words.read()
            words = words.splitlines()
            return words    
    except Exception as e:
        print(f"Error Getting Stopping Words: {e}")
        exit()
    

def dataset_loader(fileNameWithDir: str, fileType: str="json") -> list[dict[str, str]] | str:
    try:
        with open(fileNameWithDir) as file:
            if (fileType == "json"):
                return json.load(file)
            elif (fileType == "text"):
                return file.read()
            else:
                print(f"Unsupported file type: {fileType}")
                raise NotImplementedError(f"Unsupported file type: {fileType}")
    except Exception as e:
        print(f"Error At Reading File: {e}")
        exit()
        
        
