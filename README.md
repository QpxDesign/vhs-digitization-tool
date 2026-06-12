## VHS Research Tool

### Proudly made without 'AI', adherent to [Lying Club's Anti-AI Pledge](https://lying.club/ai)

#### What is this

This is a simple script to help determine the rarity of VHS Tapes/DVDs.

### How it works

From an IMDB URL, it collects metadata about the item from IMDB's static datasets (see below for instructions on how to obtain the data). Using said metadata (title(s), director, year, etc), it checks several physical media repositories to see if they have the item, and JustWatch, to see if the item streams/is available for digital purchase.

### Set Up Guide

1. Install requirements
2. Download data [from IMDB](https://datasets.imdbws.com) and place in `data/`
   - The following files are required: `title.basics.tsv`, `name.basics.tsv`, and `title.principals.tsv` (~6GB Total)
3. Run the script: `python3 walkthrough.py`
