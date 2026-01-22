# OCR에 기초한 PDF화일에서의 본문검출 

## 실행환경 
- Python: `3.11` 
- Package management: `Conda` 

## 화일구조 

```
offline_packages_windows/
├── python/              # Python Offline서고들 
├── models/              # PaddleOCR모형 
├── source/              # 원천코드
│   ├── samples          # sample PDF들 
│   ├── ...              # 
│   └── compare.py       # 기본 Python코드
├── requirements.txt     
└── README.md            # 코드설명서
```

## 실행방법 

- 1단계: Conda가상환경 만들기 

```sh
conda create --name pdf2txt python=3.11
```

- 2단계: 서고설치 

```sh
conda activate pdf2txt 
pip install --no-index --find-links .\python -r .\requirements.txt 
```

- 3단계: 모형복사 

`models/paddleocr/`등록부에 있는 화일들을 `C:\Users\<user-name>\.paddlex`등록부에 복사.

- 4단계: `./sources/samples/`에 PDF화일복사를 하고 다음의 명령문 실행 

```sh
cd source 
python compare.py .\samples\<pdf-file> --output-dir .\results\
````
