def get_stop_words() -> list[str]:
    try:
        with open("./helper/stop_words.txt") as words:
            words = words.read()
            words = words.splitlines()
            return words    
    except Exception as e:
        print(f"Error Getting Stopping Words: {e}")
        exit()
    

def dataset_loader(fileNameWithDir):
    try:
        with open(fileNameWithDir) as file:
            return file.read()
    except Exception as e:
        print(f"Error At Reading File: {e}")
        exit()
        