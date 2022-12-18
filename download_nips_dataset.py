from bs4 import BeautifulSoup
import os
import pandas as pd
import re
import requests
import subprocess
import pdb
from tqdm import tqdm

from pdfminer.high_level import extract_text
from multiprocessing import Pool

# Set to true if you want to download the paper to your local drive
DOWNLOAD_PAPERS = False
OUTPUT_PATH = "Output"
YEAR_MIN = 1988
YEAR_MAX = 2021

def text_from_pdf(pdf_path, download_papers = False):
    if not os.path.exists(pdf_path):
        print("PDF file not Found - Exiting")
        return
    text = extract_text(pdf_path)
    if download_papers == False:
        os.remove(pdf_path)
    return text

def extract_abstract(soup):
    return soup.find_all('p')[3:-2][0].text


def extract_authors(soup):
    authors = [auth.strip() for auth in soup.find_all('p')[1].text.split(',')]
    return authors

def extract_paper_from_link(link):

    paper_title = link.contents[0]
    info_link = base_url + link["href"]
    blank,base_1,year,root,hash_ = link['href'].split('/')
    hash_id = hash_.split('-')[0]
    pdf_link = base_url +'/' + base_1 + '/' + year +'/file/'+ hash_id+'-Paper.pdf'
    pdf_name = hash_id
    pdf_path = os.path.join("working", "pdfs", str(year), pdf_name+ ".pdf")
    paper_id = pdf_name
    
    if not os.path.exists(pdf_path):
        pdf = requests.get(pdf_link)
        if not os.path.exists(os.path.dirname(pdf_path)):
            os.makedirs(os.path.dirname(pdf_path))
        pdf_file = open(pdf_path, "wb")
        pdf_file.write(pdf.content)
        pdf_file.close()
    
    # Get text from Research Paper (Includes Abstract, Title, Author etc.)
    paper_text = text_from_pdf(pdf_path, DOWNLOAD_PAPERS)

    html_content = requests.get(info_link).content
    paper_soup = BeautifulSoup(html_content, "html.parser")
    
    # Extracting Abstract
    try: 
        abstract = extract_abstract(paper_soup)
        
    except:
        # print("Abstract not found %s" % paper_title.encode("ascii", "replace"))
        abstract = ""
    
    #Extracting Authors
    authors = extract_authors(paper_soup)
    for author in authors:
        paper_authors.append([len(paper_authors)+1, paper_id, author[0]])
    
    #Return paper details
    return [paper_id, authors, year, paper_title, pdf_name, abstract, paper_text]

papers = list()
paper_authors = list()

base_url  = "https://proceedings.neurips.cc/"
index_urls = {1987: "https://proceedings.neurips.cc/paper/1987"}
for year in range(1988,2022):
    # year = i+1987
    index_urls[year] = "https://proceedings.neurips.cc/paper/%d" % (year)

years = [i for i in range(YEAR_MIN,YEAR_MAX)]

if YEAR_MIN<1988 or YEAR_MAX>2022:
    print("YEAR_MIN & YEAR_MAX should be between 1988 and 2022")
    exit()

# Extract Papers for each year
for year in years:

    print("Year : ", year)
    index_url = index_urls[year]
    index_html_path = os.path.join("working", "html", str(year)+".html")

    #Download the page containing all NIPS papers for the year
    html_content = requests.get(index_url).content
    soup = BeautifulSoup(html_content, "html.parser")

    # For each paper of that year, extract the details
    paper_links = [link for link in soup.find_all('a') if link["href"][:7]=="/paper/"]
    for link in tqdm(paper_links):
        papers.append(extract_paper_from_link(link))

# Create Output directory if it doesn't exist
if not os.path.exists(OUTPUT_PATH):
    os.makedirs(OUTPUT_PATH)

# Save data as CSV
pd.DataFrame(papers, columns=["id", "authors", "year", "title", "pdf_name", "abstract", "paper_text"]).sort_values(by="id").to_csv(os.path.join(OUTPUT_PATH, "papers.csv"), index=False)
pd.DataFrame(paper_authors, columns=["id", "paper_id", "author_id"]).sort_values(by="id").to_csv(os.path.join(OUTPUT_PATH, "paper_authors.csv"), index=False)
