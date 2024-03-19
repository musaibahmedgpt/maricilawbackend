# Textract Project

## Prerequisites

### Install Poppler

Poppler is required for processing PDF files. Follow the instructions below to install Poppler on Windows, Linux, and macOS:

#### Windows:

1. Download the latest Poppler for Windows from [Poppler's official repository](https://poppler.freedesktop.org/).
2. Extract the contents to a directory.
3. Add the Poppler bin directory to your system PATH.

#### Linux:

```bash
sudo apt-get install poppler-utils
```

#### macOS:

```bash
brew install poppler
```

## Setting Up AWS Credentials

Before running the Textract script, make sure to set your AWS credentials in a `.env` file. Add the following lines to the `.env` file:

```env
AWS_ACCESS_KEY=<your_aws_access_key>
AWS_SECRET_ACCESS_KEY=<your_aws_secret_key>
```

## Installation and Usage

1. Download the zip file given:

2. Navigate to the project directory:

```bash
cd Textract-Project
```

3. (Optional) Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows, use 'venv\Scripts\activate'
```

4. Install the required dependencies:

```bash
pip install -r requirements.txt
```

5. Run the Textract script:

```bash
python main.py <path_to_pdf>
```

After running the script, you will find the following files saved in the root directory:

- `filename.json`: JSON file containing key-value pairs for each page of the input PDF.
- `filename.txt`: Text file containing the entire extracted text for clarity.

## How the Script Works

1. The script converts each page of the PDF into an image.
2. It sends each image to Textract to extract key-value pairs and table data.
3. The extracted response is parsed into a Textract `Document` object.
4. The script extracts key-value pairs and saves them as a JSON array. Each object in the array corresponds to a page of the input PDF.
5. The entire extracted text is saved into a `.txt` file for clarity.
