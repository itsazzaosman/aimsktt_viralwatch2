#!/bin/bash
set -e 

mkdir -p data/{raw,processed,external} notebooks src/{data,models,features,api} dashboard scripts

if [ ! -d "data/external/BDBV2026-Data" ]; then
    git clone https://github.com/INRB-UMIE/BDBV2026-Data.git data/external/BDBV2026-Data
else
    cd data/external/BDBV2026-Data && git pull && cd ../../../
fi

DON602_URL="https://www.who.int/emergencies/disease-outbreak-news/item/2026-DON602"
DON603_URL="https://www.who.int/emergencies/disease-outbreak-news/item/2026-DON603"

curl -sS -L -o data/raw/DON602.html "$DON602_URL"
curl -sS -L -o data/raw/DON603.html "$DON603_URL"

echo "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  data/raw/DON602.html" > data/raw/checksums.txt
echo "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  data/raw/DON603.html" >> data/raw/checksums.txt

if command -v sha256sum &> /dev/null; then
    sha256sum -c data/raw/checksums.txt || true
fi

python -m venv venv
source venv/Scripts/activate
pip install --upgrade pip --quiet

cat <<EOT > requirements.txt
numpy
pandas
scikit-learn
keras
transformers
fastapi
uvicorn
pydantic
EOT

pip install -r requirements.txt --quiet