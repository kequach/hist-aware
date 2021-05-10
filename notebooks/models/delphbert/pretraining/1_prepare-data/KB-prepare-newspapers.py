import os
from os.path import isfile
import re
import sys
from pathlib import Path

from tqdm import tqdm
import pandas as pd

import nltk.data
from delphbert.pretraining.tokenizer.tokenizer import BasicTokenizer

if len(sys.argv) < 3:
    print('Usage: python3 KB-prepare-newspapers.py source-path dest-path')

source_dir = sys.argv[1]
dest_dir = sys.argv[2]

sent_detector = nltk.data.load('tokenizers/punkt/dutch.pickle')
tokenizer = BasicTokenizer()

os.makedirs(dest_dir, exist_ok=True)

def _clean(article):
    words = re.sub(r"[-\[\]\#/@;:,<>{}=~|*»]", "", str(article)) # cleaning useless parts of sentences
    words = re.sub(r"^\s*|\s\s*", " ", words).strip() # reduce spaces
    words = re.sub(r'[^\x00-\x7F]+', "", words) # eliminate non unicode chars
    return words

# List CSVs
file_names = [str(x) for x in Path(source_dir).glob("*.csv")]
out, i, j = '', 0, 0
for filename in tqdm(file_names, ncols=80):
    if isfile(filename) is False:
        continue
    print(f"\nCSV: {filename}")
    source_path = os.path.join(source_dir, filename)

    if out:
        out += '\n'

    # Eval as we want the original types of the df 
    df = pd.read_csv(filename, converters={'p': eval})
    # Only keep subject and the text of the paragraph
    df.drop(df.columns.difference(["subject", "p"]), axis=1, inplace=True)
    # Filter by type of article
    df = df[df["subject"] == "artikel"]
    # Explode as "p" contains multiple paragraphs already
    df = df.explode('p', ignore_index = True)
    df.drop(columns = ["subject"], inplace=True)
    print(f"Length DF: {df.shape[0]}")
    
    results = []
    for i,r in tqdm(df.iterrows(), total=df.shape[0], ncols=80):
        if (pd.isnull(r['p'])):
            continue
        else:
            #clean_r = _clean(r["p"])
            if i % 100000 == 0:
                dest_path = dest_dir + '/{}.txt'.format(j)
                with open(dest_path, 'w') as f:
                    f.write(out)
                out, i = '', 0
                j += 1
            sents = sent_detector.tokenize(r["p"])
            sents = [' '.join(tokenizer.tokenize(s)) for s in sents]
            out += '\n'.join(sents) + '\n'

    # dest_path = dest_dir + '/{}.txt'.format(j)
    # with open(dest_path, 'w') as f:
    #     f.write(out)
    # out, i = '', 0
    # j += 1

# Catch last things
if out:
    dest_path = dest_dir + '/{}.txt'.format(j)
    with open(dest_path, 'w') as f:
        f.write(out)
