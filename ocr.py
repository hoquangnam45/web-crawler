import os
import imghdr
from PIL import Image
import pytesseract

ALLOWED_FILE_TYPES = ["jpg", "png"]

def extractText(filePath: str) -> str | None:
    fileType = imghdr.what(filePath)
    if (fileType in ALLOWED_FILE_TYPES):
        img = Image.open(filePath)
        return pytesseract.image_to_string(img, lang="vie") # NOTE: Good thing that vietnamese character set is larger than English character set
    else:
        return None
    
# NOTE: For testing purposes only
def main(inputFolderPath: str, outputFilePath: str):
        for file in os.listdir(inputFolderPath):
            inputFilePath = inputFolderPath + os.path.sep + file
            text = repr(extractText(inputFilePath))
            with open(outputFilePath, "w") as outputFile:
                if text is not None:
                    outputFile.write(inputFilePath + ":" + text)
                else:
                    outputFile.write(inputFilePath + ":")


if __name__ == "__main__":
    main("ocr_input", "ocr_output/output.txt")