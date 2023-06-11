from flask import Flask, render_template
from bs4 import BeautifulSoup
import requests
from PyPDF2 import PdfReader
from io import BytesIO
import pandas as pd
import re
from selenium import webdriver
from selenium.webdriver.common.by import By

app = Flask(__name__)

@app.route('/')
def home():
    from bs4 import BeautifulSoup
    import requests
    from PyPDF2 import PdfReader
    from io import BytesIO
    import pandas as pd

    # Get the HTML of the webpage
    url = 'https://infrastructure.planninginspectorate.gov.uk/legislation-and-advice/register-of-advice/'
    response = requests.get(url)
    html = response.text

    # Parse the HTML with BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')

    # Find all rows in the table
    rows = soup.find_all('tr')

    # Prepare a list to store the data
    data = []

    # Loop through each row
    for row in rows:
        # Find all cells in the row
        cells = row.find_all('td')

        # Check if the row has at least one cell
        if len(cells) >= 1:
            # Get the text of the first cell
            preview_text = cells[0].get_text()

            # Check if the preview text contains 'Project Update Meeting'
            if 'Project Update Meeting' in preview_text:
                # Find the first link in the row
                link = row.find('a')

                # Get the URL of the link
                project_url = link['href']

                # Get the content of the linked page
                linked_page_response = requests.get(project_url)
                linked_page_html = linked_page_response.text
                linked_page_soup = BeautifulSoup(linked_page_html, 'html.parser')
                
                # Initialize project_name to an empty string
                project_name = ''
                
                # Find all 'div' elements with the class 'ipcformhead'
                project_name_divs = linked_page_soup.find_all('div', class_='ipcformhead')

                # Loop through all found 'div' elements
                for project_name_div in project_name_divs:
                    # Find the 'h2' element within the current 'div'
                    project_name_h2 = project_name_div.find('h2')

                    # Check if the 'h2' element was found
                    if project_name_h2 is not None:
                        # Get the text of the 'h2' element
                        project_name = project_name_h2.get_text()

                        # Find the 'span' element within the 'h2'
                        project_name_span = project_name_h2.find('span')

                        # Check if the 'span' element was found
                        if project_name_span is not None:
                            # Get the text of the 'span' element
                            project_name_span_text = project_name_span.get_text()

                            # Remove the text of the 'span' element from the project name
                            project_name = project_name.replace(project_name_span_text, '')

                        # Remove any trailing or leading whitespace
                        project_name = project_name.strip()

                        # If the project name was found, stop the loop
                        if project_name:
                            break



                # Find the 'div' element which contains the date
                date_div = linked_page_soup.find('div', style="float: right; font-size: 1.1em; font-weight: bold; margin-right: 10px; margin-left: 50px;")
                # Get the text of the 'div' element
                date = date_div.get_text()
                
                # Find all 'div' elements with the class 'ipcformhead'
                promoter_divs = linked_page_soup.find_all('div', class_='ipcformhead')

                # Loop through all found 'div' elements
                for promoter_div in promoter_divs:
                    # Find the 'em' element within the current 'div'
                    promoter_em = promoter_div.find('em')

                    # Check if the 'em' element was found
                    if promoter_em is not None:
                        # Get the text of the 'em' element
                        promoter_name = promoter_em.get_text()
        
                        # Remove "- anon." from the project name, regardless of case and whitespace
                        promoter_name = re.sub(r'\s*-\s*anon\.\s*', '', promoter_name, flags=re.IGNORECASE)

                        # If the project name was found, stop the loop
                        if promoter_name:
                            break

                # Find the image with alt text 'attachment 1'
                pdf_image = linked_page_soup.find('img', alt='attachment 1')

                # The grandparent of the image is the 'a' tag with the 'href' attribute
                pdf_link = pdf_image.parent.parent

                # Get the URL of the PDF from the 'href' attribute
                pdf_url = pdf_link['href']

                # Print the PDF URL before trying to download and parse it
                # print('Attempting to download and parse:', pdf_url)

                # Get the content of the PDF
                pdf_response = requests.get(pdf_url)
                pdf_file = BytesIO(pdf_response.content)

                # Parse the PDF file with PyPDF2
                pdf_reader = PdfReader(pdf_file)
                pdf_content = ''
                for page in pdf_reader.pages:
                    pdf_content += page.extract_text()
                    
                # Split the content at the specified phrase and select the second part
                phrase = 'Summary of key points discussed , and advice given'
                parts = pdf_content.split(phrase)
                if len(parts) > 1:
                    pdf_content = parts[1]  # Select the part after the phrase
                
                # Split the content into paragraphs at each occurrence of two newline characters
                paragraphs = pdf_content.split('\n\n')

                # Join the paragraphs with '<br><br>' to create HTML line breaks
                pdf_content = '<br><br>'.join(paragraphs)

                # Add the data to the list
                data.append([project_name, promoter_name, date, pdf_content, project_url])

                # Stop after finding 5 entries
                if len(data) >= 5:
                    break

    for item in data:
        print('Project Name:', item[0])
        print('Promoter:', item[1])
        print('Date:', item[2])
        print('Meeting Note:', item[3])
        print('Project URL:', item[4])
        print()

    # Instead of printing the data, return it as a string
    output = ''
    for item in data:
        output += f'Project Name: {item[0]}<br>'
        output += f'Promoter: {item[1]}<br>'
        output += f'Date: {item[2]}<br>'
        output += f'Meeting Note: {item[3]}<br>'
        output += f'Project URL: {item[4]}<br><br>'
    
    # Setup webdriver
    driver = webdriver.Safari()
    driver.get('https://infrastructure.planninginspectorate.gov.uk/projects/register-of-applications/')

    # Wait for the table to load
    driver.implicitly_wait(10)

    # Find the table
    table = driver.find_element(By.TAG_NAME, 'table')

    # Get all rows in the table
    rows = table.find_elements(By.TAG_NAME, 'tr')

    # Extract the 'Application' and 'Status' from each row
    pre_exam_projects = []
    for row in rows:
        cols = row.find_elements(By.TAG_NAME, 'td')
        if len(cols) > 0:
            application = cols[0].text
            status = cols[5].text  # Corrected index
            if status == "Pre-examination":
                pre_exam_projects.append(application)

    driver.quit()

   # Render the HTML template and pass the data to it
    return render_template('index.html', data=data, pre_exam_projects=pre_exam_projects)

    
if __name__ == '__main__':
    app.run(debug=True)
