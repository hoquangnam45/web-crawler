import os

def read(fileName: str) -> list[str]:
    f = open(fileName, 'r', encoding='utf-8')
    data: list[str] = []
    for _, line in enumerate(f):
        try:
            line = repr(line)
            line = line[1:len(line) - 3]
            data.append(line)
        except Exception as e:
            print(e)
    return data

def appendFile(fileName: str, contents: list[str]):
    with open(fileName, 'a') as f1:
        for content in contents:
            f1.write(content + os.linesep)