from fastapi import FastAPI, HTTPException
from lxml import html
import requests
import re


app = FastAPI()


@app.get("/scrap_repo")
async def scrap_repo(url: str):
    responseJson = {}
    try:
        # Faz a requisição HTTP
        response = requests.get(url)
        response.raise_for_status()  # Verifica se a requisição foi bem-sucedida
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Erro ao acessar a URL: {e}")

    tree = html.fromstring(response.content)

    # Parseia o conteúdo HTML com lxml
    div_element = tree.xpath("(//div[@data-hpc='true'])[1]")

    if div_element:
        # Buscar todas as <tr>, ignorando a primeira (usando posição > 1)
        tr_list = div_element[0].xpath(".//tbody/tr[position() > 1 and position() < last()]")

        # Iterar sobre cada <tr> (ignorando a primeira)
        for tr in tr_list:
            # Obter todas as <td> dentro da <tr>
            td_list = tr.xpath("./td")

            # Procurar SVG e <a> dentro da <tr>
            svg_class = tr.xpath(".//svg/@class")  # Classe do SVG
            a_href = tr.xpath(".//a/@href")  # Link do <a>

            if a_href[0].startswith("http"):
                full_url = a_href[0]
            else:
                full_url = f"https://github.com{a_href[0]}"

            if "icon-directory" in svg_class:
                print("opening directory: " + full_url)
                openPath(full_url, responseJson)

            elif "color-fg-muted" in svg_class:
                print("opening file: " + full_url)
                scrap_file(full_url, responseJson)
            else:
                print("non valid type")

    return responseJson


def openPath(url: str, responseJson):
    try:
        # Faz a requisição HTTP
        response = requests.get(url)
        response.raise_for_status()  # Verifica se a requisição foi bem-sucedida
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Erro ao acessar a URL: {e}")

    # Parseia o conteúdo HTML com lxml
    tree = html.fromstring(response.content)

    div_element = tree.xpath("//table[@aria-labelledby='folders-and-files']")
    if div_element:
        # Buscar todas as <tr>, ignorando a primeira (usando posição > 1)
        tr_list = div_element[0].xpath(".//tbody/tr[position() > 1 and position() < last()]")

        # Iterar sobre cada <tr> (ignorando a primeira)
        for tr in tr_list:
            # Obter todas as <td> dentro da <tr>
            td_list = tr.xpath("./td")

            # Procurar SVG e <a> dentro da <tr>
            svg_class = tr.xpath(".//svg/@class")  # Classe do SVG
            a_href = tr.xpath(".//a/@href")  # Link do <a>

            full_url = f"https://github.com{a_href[0]}"

            if "icon-directory" in svg_class:
                print("opening directory: " + full_url)
                openPath(full_url, responseJson)

            elif "color-fg-muted" in svg_class:
                print("opening file: " + full_url)
                scrap_file(full_url,responseJson)
            else:
                print("non valid type: " + svg_class)

def scrap_file(url: str, responseJson):
    fileExtension = getExtension(url)

    try:
        # Faz a requisição HTTP
        response = requests.get(url)
        response.raise_for_status()  # Verifica se a requisição foi bem-sucedida
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Erro ao acessar a URL: {e}")

        # Parseia o conteúdo HTML com lxml
    tree = html.fromstring(response.content)


    fileDetails = tree.xpath("//*[@id='repos-sticky-header']//*/div[contains(@class, 'text-mono')]/*/span/text()")
    if len(fileDetails) == 0:
        print("FAILED TO READ FILE: " + getFileName(url))
        print("LAST ACCESSED URL: " + url)
        # Convert the tree back to a string (HTML format)
        html_string = html.tostring(tree, encoding="unicode")
        return

        # Save the HTML string to a file in the project root directory
        with open("output.html", "w", encoding="utf-8") as f:
            f.write(html_string)


    fileDetails = fileDetails[0]
    #Gets the line count
    lineCount = int(re.search(r'\d+', fileDetails).group())
    #Extract the last number
    size = int(re.findall(r'\d+', fileDetails)[-1])
    #Extract the last word
    unitSize= re.findall(r'\w+', fileDetails)[-1]



    if fileExtension in responseJson:
        extension = responseJson[fileExtension]["extension"]
        count = responseJson[fileExtension]["count"]
        lines = responseJson[fileExtension]["lines"]
        bytes = responseJson[fileExtension]["bytes"]

        if unitSize.lower() == 'bytes':
            bytes = bytes + size
        elif unitSize.lower() == 'kb':
            bytes = bytes + size * 1024
        elif unitSize.lower() == 'mb':
            bytes = bytes + size * 1024 * 1024
        elif unitSize.lower() == 'gb':
            bytes = bytes + size * 1024 * 1024 * 1024
        elif unitSize.lower() == 'tb':
            bytes = bytes + size * 1024 * 1024 * 1024 * 1024
        else:
            print("FAILED TO READ FILE SIZE: " + getFileName(url))
            print("LAST ACCESSED URL: " + url)
            return

        count = count + 1
        lines = lines + lineCount

        responseJson[fileExtension]["extension"] = extension
        responseJson[fileExtension]["count"] = count
        responseJson[fileExtension]["lines"] = lines
        responseJson[fileExtension]["bytes"] = bytes

    else:
        if unitSize.lower() == 'bytes':
            bytes = size
        elif unitSize.lower() == 'kb':
            bytes = size * 1024
        elif unitSize.lower() == 'mb':
            bytes = size * 1024 * 1024
        elif unitSize.lower() == 'gb':
            bytes = size * 1024 * 1024 * 1024
        elif unitSize.lower() == 'tb':
            bytes = size * 1024 * 1024 * 1024 * 1024
        else:
            print("FAILED TO READ FILE SIZE: " + getFileName(url))
            print("LAST ACCESSED URL: " + url)
            return

        jsonTypeObj = {"extension":fileExtension,"count":1, "lines":int(lineCount), "bytes":int(bytes)}
        responseJson[fileExtension] = jsonTypeObj

def getExtension(url: str) -> str:
    filename = getFileName(url)
    extension = "." + filename.split(".", 1)[-1]
    print(extension)
    return extension if len(extension) > 1 else "no extension"

def getFileName(url:str):
    url = url.replace("https://github.com/", "")
    url = url.replace(".github", "")
    filename = url.split("/", 1)[-1]
    return filename