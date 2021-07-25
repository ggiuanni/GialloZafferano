import requests
from bs4 import BeautifulSoup
import re
from string import digits
import json
from ModelRecipe import ModelRecipe
import os
import base64

debug = False

def saveRecipe(linkRecipeToDownload):
    soup = downloadPage(linkRecipeToDownload)
    title = findTitle(soup)
    ingredients = findIngredients(soup)
    description = findDescription(soup)
    category = findCategory(soup)
    imageBase64 = findImage(soup)
    macros = findMacros(soup)
    featured = findFeatured(soup)

    modelRecipe = ModelRecipe()
    modelRecipe.title = title
    modelRecipe.ingredients = ingredients
    modelRecipe.description = description
    modelRecipe.category = category
    modelRecipe.imageBase64 = imageBase64
    modelRecipe.macros = macros
    modelRecipe.featured = featured
    modelRecipe.source = linkRecipeToDownload

    createFileJson(modelRecipe.toDictionary(), modelRecipe.title)

def findTitle(soup):
    titleRecipe = ""
    for title in soup.find_all(attrs={'class' : 'gz-title-recipe gz-mBottom2x'}):
        titleRecipe = title.text
    return titleRecipe

def findIngredients(soup):
    allIngredients = {}
    for tag in soup.find_all(attrs={'class' : 'gz-ingredient'}):
        # link = tag.a.get('href')
        nameIngredient = tag.a.string
        contents = tag.span.contents[0]
        quantityProduct = re.sub(r"\s+", " ",  contents).strip()
        allIngredients[nameIngredient.lower()] = quantityProduct
    return allIngredients

def findMacros(soup):
    macros_names = soup.find_all(attrs={'class' : 'gz-list-macros-name'})
    macros_units = soup.find_all(attrs={'class' : 'gz-list-macros-unit'})
    macros_values = soup.find_all(attrs={'class' : 'gz-list-macros-value'})
    macros = {}
    for idx in range(0, len(macros_names)):
        mn = macros_names[idx].string.strip().lower()
        macros[mn] = {}
        macros[mn]["unit"] = macros_units[idx].string
        macros[mn]["value"] = macros_values[idx].string
    return macros

def findFeatured(soup):
    featured_data = {}
    for tag in soup.find_all(attrs={'class' : 'gz-name-featured-data'}):
        f_array = tag.get_text().split(":")
        if len(f_array) > 1:
            featured_data[tag.get_text().split(":")[0].lower()] = tag.get_text().split(":")[1].strip().lower()
        elif len(f_array) == 0:
            featured_data[tag.get_text().split(" ")[0].lower()] = " ".join(tag.get_text().split(" ")[1:]).strip().lower()
    return featured_data

def findDescription(soup):
    allDescription = ""
    for tag in soup.find_all(attrs={'class' : 'gz-content-recipe-step'}):
        removeNumbers = str.maketrans('', '', digits)
        try:
            description = tag.p.text.translate(removeNumbers)
        except:
            description = tag.get_text()
            
        allDescription =  allDescription + description
    return allDescription

def findCategory(soup):
    for tag in soup.find_all(attrs={'class' : 'gz-breadcrumb'}):
        category = tag.li.a.string
        return category

def findImage(soup):

    # Find the first picture tag
    pictures = soup.find('picture', attrs={'class': 'gz-featured-image'})

    # Fallback: find a div with class `gz-featured-image-video gz-type-photo`
    if pictures is None:
        pictures = soup.find('div', attrs={'class': 'gz-featured-image-video gz-type-photo'})

    imageSource = pictures.find('img')

    # Most of the times the url is in the `data-src` attribute
    imageURL = imageSource.get('data-src')

    # Fallback: if not found in `data-src` look for the `src` attr
    # Most likely, recipes which have the `src` attr
    # instead of the `data-src` one
    # are the older ones.
    # As a matter of fact, those are the ones enclosed
    # in <div> tags instead of <picture> tags (supported only on html5 and onward)
    if imageURL is None:
        imageURL = imageSource.get('src')

    imageToBase64 = str(base64.b64encode(requests.get(imageURL).content))
    imageToBase64 = imageToBase64[2:len(imageToBase64) - 1]
    return "data:image/jpg;base64,"+imageToBase64

def createFileJson(recipes, name):
    compact_name = name.replace(" ", "_").lower()
    folderRecipes = "Recipes"
    if not os.path.exists(folderRecipes):
        os.makedirs(folderRecipes)
    with open(folderRecipes + '/' + compact_name + '.json', 'w', encoding="utf-8") as file:
        file.write(json.dumps(recipes, ensure_ascii=False))

def downloadPage(linkToDownload):
    response = requests.get(linkToDownload)
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup

def downloadAllRecipesFromGialloZafferano():
    for pageNumber in range(1,countTotalPages() + 1):
        linkList = 'https://www.giallozafferano.it/ricette-cat/page' + str(pageNumber)
        response = requests.get(linkList)
        soup= BeautifulSoup(response.text, 'html.parser')
        for tag in soup.find_all(attrs={'class' : 'gz-title'}):
            link = tag.a.get('href')
            saveRecipe(link)
            print(link)
            if debug :
                break

        if debug :
            break

def countTotalPages():
    numberOfPages = 0
    linkList = 'https://www.giallozafferano.it/ricette-cat'
    response = requests.get(linkList)
    soup= BeautifulSoup(response.text, 'html.parser')
    for tag in soup.find_all(attrs={'class' : 'disabled total-pages'}):
        numberOfPages = int(tag.text)
    return numberOfPages

if __name__ == '__main__' :
    downloadAllRecipesFromGialloZafferano()
