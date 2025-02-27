from fileinput import filename

from fastapi import FastAPI, HTTPException
from lxml import html
import json
import requests
import os
import re

app = FastAPI()

@app.get("/scrap_repo")
async def scrap_repo(url: str):
    responseJson = {}
    try:
        # Make HTTP request
        response = requests.get(url + "/commits")
        response.raise_for_status()  # Check if request was successful
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Erro ao acessar a URL: {e}")

    tree = html.fromstring(response.content)

    repoHash = tree.xpath("//*[starts-with(@data-testid, 'commit-group-title')][1]/text()")
    print(f"REPO HASH: {repoHash}")
    repoHash = repoHash[0]

    # JSON file name
    file_name = f"{repoHash}.json"

    print(f"URL: {url}")

    # Process URL to create directory
    urlDir = url.replace("https://github.com/", "")
    urlDir = urlDir.split("/")
    directory = "repos/" + urlDir[0] + "/" + urlDir[1]

    # JSON file name
    file_name = f"{repoHash}.json"
    file_path = os.path.join(directory, file_name)

    # Create directory if it doesn't exist
    os.makedirs(directory, exist_ok=True)

    # Check if file already exists
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
        print(f"⚠️ File already exists at: {file_path} (not overwritten)")
        responseJson = json.loads(content)
        return responseJson
    else:
        try:
            # Make HTTP request
            response = requests.get(url)
            response.raise_for_status()  # Check if request was successful
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=400, detail=f"Erro ao acessar a URL: {e}")

        tree = html.fromstring(response.content)
        # Parse HTML content with lxml
        div_element = tree.xpath("(//div[@data-hpc='true'])[1]")

        if div_element:
            # Find all <tr> elements, skipping the first one (using position > 1)
            tr_list = div_element[0].xpath(".//tbody/tr[position() > 1 and position() < last()]")

            # Iterate over each <tr> (skipping the first)
            for tr in tr_list:
                # Get all <td> elements within the <tr>
                td_list = tr.xpath("./td")

                # Search for SVG and <a> inside the <tr>
                svg_class = tr.xpath(".//svg/@class")  # SVG class
                a_href = tr.xpath(".//a/@href")  # <a> link

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

        storeJsonData(directory, repoHash, responseJson)

        return responseJson


def openPath(url: str, responseJson):
    try:
        # Make HTTP request
        response = requests.get(url)
        response.raise_for_status()  # Check if request was successful
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Erro ao acessar a URL: {e}")

    # Parse HTML content with lxml
    tree = html.fromstring(response.content)

    div_element = tree.xpath("//table[@aria-labelledby='folders-and-files']")
    if div_element:
        # Find all <tr> elements, skipping the first one (using position > 1)
        tr_list = div_element[0].xpath(".//tbody/tr[position() > 1 and position() < last()]")

        # Iterate over each <tr> (skipping the first)
        for tr in tr_list:
            # Get all <td> elements within the <tr>
            td_list = tr.xpath("./td")

            # Search for SVG and <a> inside the <tr>
            svg_class = tr.xpath(".//svg/@class")  # SVG class
            a_href = tr.xpath(".//a/@href")  # <a> link

            full_url = f"https://github.com{a_href[0]}"

            if "icon-directory" in svg_class:
                print("opening directory: " + full_url)
                openPath(full_url, responseJson)

            elif "color-fg-muted" in svg_class:
                print("opening file: " + full_url)
                scrap_file(full_url, responseJson)
            else:
                print("non valid type: " + svg_class)


def scrap_file(url: str, responseJson):
    fileExtension = getExtension(url)

    try:
        # Make HTTP request
        response = requests.get(url)
        response.raise_for_status()  # Check if request was successful
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Erro ao acessar a URL: {e}")

    # Parse HTML content with lxml
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
    # Gets the line count
    lineCount = int(re.search(r'\d+', fileDetails).group())
    # Extract the last number
    size = int(re.findall(r'\d+', fileDetails)[-1])
    # Extract the last word
    unitSize = re.findall(r'\w+', fileDetails)[-1]

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

        jsonTypeObj = {"extension": fileExtension, "count": 1, "lines": int(lineCount), "bytes": int(bytes)}
        responseJson[fileExtension] = jsonTypeObj


def getExtension(url: str) -> str:
    filename = getFileName(url)
    extension = "." + filename.split(".", 1)[-1]
    print(extension)
    return extension if len(extension) > 1 else "no extension"
    # TODO
    # Check the file ending, line count, and file size
    # If file type doesn't exist in JSON, create new index with acquired info
    # If exists, sum totals

    # Example JSON structure
    # responseJson = {".py":{"extension":".py","count":10, "lines":4000, "bytes":65462},".js":{"extension":".js","count":10, "lines":4000, "bytes":65462}}


def getFileName(url: str):
    url = url.replace("https://github.com/", "")
    url = url.replace(".github", "")
    filename = url.split("/", 1)[-1]
    return filename


def storeJsonData(url, repoHash, jsonData):
    print(f"URL: {url}")

    # Process URL to create directory
    url = url.replace("https://github.com/", "")
    url = url.split("/")
    directory = "repos/" + url[0] + "/" + url[1]

    # JSON file name
    file_name = f"{repoHash}.json"
    file_path = os.path.join(directory, file_name)

    # Create directory if it doesn't exist
    os.makedirs(directory, exist_ok=True)

    # Check if file already exists
    if os.path.exists(file_path):
        print(f"⚠️ File already exists at: {file_path} (not overwritten)")
        return  # Exit function without creating file

    # If file doesn't exist, create and save data
    with open(file_path, "w", encoding="utf-8") as json_file:
        json.dump(jsonData, json_file, indent=4, ensure_ascii=False)

    print(f"✅ JSON file saved at: {file_path}")