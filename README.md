# Scrape recipe data

## How to install

Download and install python 3 (eg using conda)
```bash
curl -O https://repo.continuum.io/archive/Anaconda3-4.4.0-Linux-x86_64.sh
bash Anaconda3-4.4.0-Linux-x86_64.sh
source .bashrc
```

Clone and move inside the repository
```bash
git clone https://github.com/alexabate/untitled.git && cd untitled
```

Set up a virtual environment using conda but use pip as the package manager by
adding pip when the conda env is created. Install the packages listed in the 
requirements.txt
```bash
conda create --name recipe_proj
source activate recipe_proj
conda install pip
pip install -r requirements.txt
```

## How to run

First get the bbc sitemap, run the function `scrapers.get_bbc_recipe_urls()`

```
python run_bbc.py
```

