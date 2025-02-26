from fastapi import FastAPI, HTTPException
from lxml import html
import requests

app = FastAPI()


@app.get("/scrap_xpath")
async def scrap_xpath(url: str, xpath: str):
    try:
        # Faz a requisição HTTP
        response = requests.get(url)
        response.raise_for_status()  # Verifica se a requisição foi bem-sucedida
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Erro ao acessar a URL: {e}")

    # Parseia o conteúdo HTML com lxml
    tree = html.fromstring(response.content)

    # Usa XPath para extrair o elemento
    result = tree.xpath(xpath)

    # Verifica se o elemento foi encontrado
    if not result:
        raise HTTPException(status_code=404, detail="Nenhum elemento encontrado com o XPath fornecido.")

    # Retorna o resultado
    return {"result": result}

