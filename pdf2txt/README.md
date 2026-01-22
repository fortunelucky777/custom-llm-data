# OCR Based PDF2TXT

## Environment 
- Python: `3.12` 
- Package management: `Conda` 

## File Structure 

```
offline_packages_windows/
├── python/              # Python Offline Packages 
├── models/              # PaddleOCR Models 
├── source/              # Source code 
│   ├── samples          # sample PDFs 
│   ├── ...              # 
│   └── compare.py       # Main python script
├── requirements.txt     
└── README.md            
```

## How to Run 

- Step 1: Create Conda Venv

```sh
conda create --name pdf2txt
```

- Step 2: Install Packages Offline

```sh
conda activate pdf2txt 
pip install --no-index --find-links .\python -r .\requirements.txt 
```

- Step 3: Model Copy 

Copy the files of `models/paddleocr/` into ``C:\Users\<user-name>\.paddlex`

- Step 4: Copy PDF files into `./sources/samples/` and run following command:

```sh
cd source 
python compare.py .\samples\<pdf-file> --output-dir .\results\
````
