from fileinput import filename

from fastapi import FastAPI, HTTPException
from lxml import html
import requests
import os
import re


app = FastAPI()


@app.get("/scrap_repo")
async def scrap_repo(url: str):
    responseJson = "{}"
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


    fileDetails = tree.xpath("(//div[@data-testid='blob-size']/span/text())[1]")
    fileDetails = fileDetails[0]
    #Gets the line count
    lineCount = re.search(r'\d+', fileDetails).group()
    #Extract the last number
    Size = re.findall(r'\d+', fileDetails)[-1]
    #Extract the last word
    unitSize= re.findall(r'\w+', fileDetails)[-1]


def getExtension(text: str) -> str:
    text = text.replace("https://github.com/", "")
    text = text.replace(".github", "")
    text = text.split("/", 1)[-1]
    extension = "." + text.split(".", 1)[-1]
    print(extension)
    return extension if len(extension) > 1 else "no extension"
    # TODO
    # VERIFICA A TERMINAÇÃO DO ARQUIVO, QUANTIDADE DE LINHAS E TAMANHO DO ARQUIVO
    # CASO O TIPO DE ARQUIVO NÃO EXISTA DENTRO DO JSON, CRIAR UM NOVO INDICE DENTRO DO MESMO COM AS INFORMAÇÕES ADQUIRIDAS
    # CASO EXISTA, SOMAR OS TOTAIS

    # responseJson = {".py":{"extenssion":".py","count":10, "lines":4000, "bytes":65462},".js":{"extenssion":".js","count":10, "lines":4000, "bytes":65462}}
