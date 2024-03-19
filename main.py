import os
import io
from fastapi.responses import FileResponse
import json
import boto3
import numpy as np
from dotenv import load_dotenv
from pdf2image import convert_from_bytes, convert_from_path
from PIL import Image
import trp
from trp.trp2 import TDocument, TDocumentSchema
import trp.trp2 as t2
from trp.t_pipeline import order_blocks_by_geo
from fastapi import FastAPI, File, UploadFile,Response,Request
from typing import List
from docc import *
from fastapi.middleware.cors import CORSMiddleware  # Add this import

app = FastAPI()

# Configure CORS
origins = [
    "http://localhost:5173",  # Add the origin of your React application
    "http://localhost",       # Add other origins if needed
    # Add other origins as needed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)




def convert_pdf_to_images(pdf_bytes: bytes) -> List[str]:
    images = convert_from_bytes(pdf_bytes)
    image_paths = []
    for i, image in enumerate(images):
        print(i)
        #preprocessed_image = preprocess_image(np.array(image))
        image_path = f"page_{i+1}.png"
        image.save(image_path)
        image_paths.append(image_path)
    return image_paths

def save_uploaded_image_to_temp_file(image_file: UploadFile) -> str:
    """Saves an uploaded image file to a temporary file."""
    temp_image_path = f"uploaded_image.png"
    with open(temp_image_path, 'wb') as temp_image:
        temp_image.write(image_file.file.read())
    return temp_image_path

def analyze_document(image_path: str, access_key: str, secret_key: str, region='eu-west-3'):
    textract_client = boto3.client('textract', region_name=region,
                                   aws_access_key_id=access_key,
                                   aws_secret_access_key=secret_key)

    with open(image_path, 'rb') as image_file:
        response = textract_client.analyze_document(
            Document={
                'Bytes': image_file.read()
            },
            FeatureTypes=['FORMS','TABLES','QUERIES'],
            QueriesConfig= {"Queries": [{
            "Text": "What is the document number located above 'To be completed by Police Officer' at the top of the scanned document?",
            "Alias": "UTT_NUMBER"
        },
        {
            "Text": "What is the full name of Court?",
            "Alias": "COURT_NAME"
        },
         {
            "Text": "What is the Date of Return by Mail or Apepar in Person?",
            "Alias": "ADJOURNED_DATE"
        },
        
         {
            "Text": "What is the Defendent's First Name?",
            "Alias": "FIRST_NAME"
        },
        {
            "Text": "What is the Defendent's LAST Name?",
            "Alias": "LAST_NAME"
        }
        ]}
        )

    return response


def extract_key_value_pairs(response) -> dict:
    with open('response.json', 'w') as file:
        json.dump(response,file,indent=4)
    #doc = Document(response)
    t_doc = TDocumentSchema().load(response)
    key_value_pairs = {}
    raw_text = ""
    ordered_doc = order_blocks_by_geo(t_doc)
    
    trp_doc = trp.Document(TDocumentSchema().dump(ordered_doc))
    for page in trp_doc.pages:
        #print(page)
        for line in page.lines:
            for word in line.words:
                if word.text:
                    raw_text += word.text + " "
            raw_text += "\n"

        for field in page.form.fields:
            key = str(field.key)
            value = str(field.value)
            if key in key_value_pairs:
                suffix = 2
                while f"{key}#{suffix}" in key_value_pairs:
                    suffix += 1
                key = f"{key}#{suffix}"
            key_value_pairs[key] = value

        for table in page.tables:
            for row in table.rows:
                if row.cells:
                    key = str(row.cells[0])
                    value = str(row.cells[1])
                    if key in key_value_pairs:
                        suffix = 2
                        while f"{key}#{suffix}" in key_value_pairs:
                            suffix += 1
                        key = f"{key}#{suffix}"
                    key_value_pairs[key] = value
    # d = t2.TDocumentSchema().load(response)
    # page = d.pages[0]
    d = t2.TDocumentSchema().load(response)
    
    query_answers = d.get_query_answers(page=d.pages[0])
    print(query_answers)
    for x in query_answers:
        key = str(x[1])
        if key in key_value_pairs:
                suffix = 2
                while f"{key}#{suffix}" in key_value_pairs:
                    suffix += 1
                key = f"{key}#{suffix}"
                #key_value_pairs[key] = value
        value = str(x[2])
        key_value_pairs[key] = value


    with open('ordered.json', 'w') as file:
        json.dump(key_value_pairs,file,indent=4)
    return key_value_pairs, raw_text
@app.post("/upload/")
async def analyze_upload_file(file: UploadFile = File(...)):
    print("request recieved")
    access_key= 'AKIAYS2NXI54RWZVJEN6'
    secret_key= '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'
    file_ext = os.path.splitext(file.filename)[1]
    if file_ext.lower() == '.pdf':
        pdf_bytes = await file.read()
        image_paths = convert_pdf_to_images(pdf_bytes)
        print(image_paths)
    elif file_ext.lower() in ('.jpg', '.jpeg', '.png'):
        
        temp_image_path = save_uploaded_image_to_temp_file(file)
        image_paths = [temp_image_path]
    else:
        return {"error": "Unsupported file format"}

    finalized_array = []
    finalized_text = ""
    
#print("Processing page number:", i + 1)
    response = analyze_document(image_paths[0], access_key, secret_key)
    results, text = extract_key_value_pairs(response)
    finalized_array.append(results)
    finalized_text += text
    response = Response(content=json.dumps({"extracted_results": finalized_array, "raw_text": finalized_text}), status_code=200)

    # Add the Access-Control-Allow-Origin header to allow all origins
    response.headers["Access-Control-Allow-Origin"] = "*"

    # Return the response
    return response
    #return 

@app.post("/convertToWord/")
async def convert_to_word(data:dict = Request)-> dict:
    print(data['data'])
    header_image_path = 'header_image.png'  # Replace with the path to your header image
    footer_image_path = 'footer_image.png'
    create_word_document(data['data'], header_image_path, footer_image_path)
    file_path = 'your_document.docx'

    # # Open the file in binary mode
    # with open(file_path, 'rb') as file:
    #     file_content = file.read()

    # Return the file as a response
    response = FileResponse(file_path, filename='your_document.docx', media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')


    # Add the Access-Control-Allow-Origin header to allow all origins
    response.headers["Access-Control-Allow-Origin"] = "*"

    # Return the response
    return response
    #return {}

@app.post("/convertToPDF")
async def convert_to_pdf(text: Request):
    print(text)
    return {"message": "Text received and printed successfully."}

import uvicorn

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080)