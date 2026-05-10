import json


PROJECT_ROOT = "./recall_engine"
STOP_WORDS_PATH = f"{PROJECT_ROOT}/helper/stop_words.txt"
CACHE_PATH = f"{PROJECT_ROOT}/cache/cache.pkl"
DATA_PATH = f"./datasets/movies.json"
def get_stop_words() -> list[str]:
    try:
        with open(STOP_WORDS_PATH) as words:
            words = words.read()
            words = words.splitlines()
            return words    
    except Exception as e:
        print(f"Error Getting Stopping Words: {e}")
        exit()
    
def dataset_loader_json(fileNameWithDir: str) -> dict[str, list[dict[str, str]] | int | str]:
    try:
        with open(fileNameWithDir) as file:
            return json.load(file)
    except Exception as e:
        print(f"Error At Reading File: {e}")
        exit()

def dataset_loader(fileNameWithDir: str) -> str:
    try:
        with open(fileNameWithDir) as file:
                return file.read()
    except Exception as e:
        print(f"Error At Reading File: {e}")
        exit()
        
        
