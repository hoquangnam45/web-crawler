import os
import imghdr
from PIL import Image
import pytesseract
import urllib.request


def extractText(filePath: str) -> str | None:
    ALLOWED_FILE_TYPES = ["jpg", "png", "jpeg"]
    fileType = imghdr.what(filePath)
    if (fileType in ALLOWED_FILE_TYPES):
        img = Image.open(filePath)
        return pytesseract.image_to_string(img, lang="vie") # NOTE: Good thing that vietnamese character set is larger than English character set
    else:
        return None
    
# NOTE: Extension and file name can be inferred from the url, so file name does not necessarily need to include the extension
def downloadAndExtractText(url: str, downloadFile: str | None = None) -> str | None:
    if downloadFile is None:
        downloadFile, _ = urllib.request.urlretrieve(url, downloadFile)
    return extractText(downloadFile)
    
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
    print(downloadAndExtractText("https://static.wixstatic.com/media/6deb20_7663dc4624b149b6a74f933c79c6f223~mv2.jpg/v1/fill/w_1000,h_556,al_c,q_85,usm_0.66_1.00_0.01/6deb20_7663dc4624b149b6a74f933c79c6f223~mv2.jpg"))
    # main("ocr_input", "ocr_output/output.txt")