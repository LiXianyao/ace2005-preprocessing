# ACE2005 preprocessing

This is a simple code for preprocessing ACE 2005 corpus for Event Extraction task. 

Using the existing methods were complicated for me, so I made this project.

## Prerequisites

1. Prepare **ACE 2005 dataset**. 

   (Download: https://catalog.ldc.upenn.edu/LDC2006T06. Note that ACE 2005 dataset is not free.)

2. Install the packages.
   ```
   pip install stanfordcorenlp beautifulsoup4 nltk tqdm
   ```
    
3. Download stanford-corenlp model.
    ```bash
    wget http://nlp.stanford.edu/software/stanford-corenlp-full-2018-10-05.zip
    unzip stanford-corenlp-full-2018-10-05.zip
    ```

4. For Chinese, Download stanford-chinese model
    ```bash
    http://nlp.stanford.edu/software/stanford-chinese-corenlp-2018-10-05-models.jar
    ```
    move the jar into stanford-corenlp-full-2018-10-05/
    than start a server for Chinese-Properties
    ```bash
    java -mx3g -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLPServer -props StanfordCoreNLP-chinese.properties -annotators 'tokenize,ssplit,pos,lemma,parse' -port 9000 -timeout 300000
    ```
    
    than just Call main.py with this command:
    ```bash
    python main.py --data=./data/ace_2005_td_v7/data/Chinese --lang=zh --host='http://localhost' --port=9000
    ```

Additional. Accessing Stanford CoreNLP Server using Python:
   ```python
   from stanfordcorenlp import StanfordCoreNLP
   import json
   nlp = StanfordCoreNLP('http://localhost', port=9000,timeout=300000,lang='zh')
   CHINESE_PROPERTIES = { 
    "tokenize.language": "zh", 
    "segment.model": "edu/stanford/nlp/models/segmenter/chinese/ctb.gz", "segment.sighanCorporaDict": "edu/stanford/nlp/models/segmenter/chinese", "segment.serDictionary": "edu/stanford/nlp/models/segmenter/chinese/dict-chris6.ser.gz", "segment.sighanPostProcessing": "true", 
    "ssplit.boundaryTokenRegex": "[.。]|[!?！？]+", 
    "pos.model": "edu/stanford/nlp/models/pos-tagger/chinese-distsim/chinese-distsim.tagger" ,
    "parse.model": "edu/stanford/nlp/models/srparser/chineseSR.ser.gz"
    }
   sentence = '北京邮电大学位于西土城路10号，英文名为Beijing University of Posts and Telecommunications，简称BUPT'
   d = json.loads(nlp.annotate(sentence,properties=CHINESE_PROPERTIES))
```
   part of data in d['sentences'][0]['tokens'] are: 
   ```json
    [       
        {   
            "pos": "NR",
            "characterOffsetBegin": 0,
            "word": "北京",
            "index": 1,
            "lemma": "北京",
            "originalText": "北京",
            "characterOffsetEnd": 2
        },  
        {   
            "pos": "NN",
            "characterOffsetBegin": 2,
            "word": "邮电",
            "index": 2,
            "lemma": "邮电",
            "originalText": "邮电",
            "characterOffsetEnd": 4
        },  
        {   
            "pos": "NN",
            "characterOffsetBegin": 4,
            "word": "大学",
            "index": 3,
            "lemma": "大学",
            "originalText": "大学",
            "characterOffsetEnd": 6
        },
        {
            "pos": "VV",
            "characterOffsetBegin": 6,
            "word": "位于",
            "index": 4,
            "lemma": "位于",
            "originalText": "位于",
            "characterOffsetEnd": 8
        },
            {   
            "pos": "NN",
            "characterOffsetBegin": 8,
            "word": "西",
            "index": 5,
            "lemma": "西",
            "originalText": "西", 
            "characterOffsetEnd": 9
        },
        {   
            "pos": "NR",
            "characterOffsetBegin": 9,
            "word": "土城",
            "index": 6,
            "lemma": "土城",
            "originalText": "土城", 
            "characterOffsetEnd": 11
        },  
        {   
            "pos": "NN",
            "characterOffsetBegin": 11,
            "word": "路",
            "index": 7,
            "lemma": "路",
            "originalText": "路",
            "characterOffsetEnd": 12
        },  
        {   
            "pos": "NT",
            "characterOffsetBegin": 12,
            "word": "10号",
            "index": 8,
            "lemma": "10号",
            "originalText": "10号", 
            "characterOffsetEnd": 15
        }
    ]
```
    
## Usage

Run:

```bash
sudo python main.py --data=./data/ace_2005_td_v7/data/English
``` 

- Then you can get the parsed data in `output directory`. 

- If it is not executed with the `sudo`, an error can occur when using `stanford-corenlp`.

- It takes about 30 minutes to complete the pre-processing.

## Output

### Format

I follow the json format described in [EMNLP2018-JMEE](https://github.com/lx865712528/EMNLP2018-JMEE) repository like the bellow sample.

If you want to know event types and arguments in detail, read [this document (ACE 2005 event guidelines)](https://www.ldc.upenn.edu/sites/www.ldc.upenn.edu/files/english-events-guidelines-v5.4.3.pdf).


**`sample.json`**
```json
[
  {
    "sentence": "He visited all his friends.",
    "tokens": ["He", "visited", "all", "his", "friends", "."],
    "pos-tag": ["PRP", "VBD", "PDT", "PRP$", "NNS", "."],
    "golden-entity-mentions": [
      {
        "text": "He", 
        "entity-type": "PER:Individual",
        "start": 0,
        "end": 0
      },
      {
        "text": "his",
        "entity-type": "PER:Group",
        "start": 3,
        "end": 3
      },
      {
        "text": "all his friends",
        "entity-type": "PER:Group",
        "start": 2,
        "end": 5
      }
    ],
    "golden-event-mentions": [
      {
        "trigger": {
          "text": "visited",
          "start": 1,
          "end": 1
        },
        "arguments": [
          {
            "role": "Entity",
            "entity-type": "PER:Individual",
            "text": "He",
            "start": 0,
            "end": 0
          },
          {
            "role": "Entity",
            "entity-type": "PER:Group",
            "text": "all his friends",
            "start": 2,
            "end": 5
          }
        ],
        "event_type": "Contact:Meet"
      }
    ],
    "parse": "(ROOT\n  (S\n    (NP (PRP He))\n    (VP (VBD visited)\n      (NP (PDT all) (PRP$ his) (NNS friends)))\n    (. .)))"
  }
]
```


### Data Split

The result of data is divided into test/dev/train as follows.
```
├── output
│     └── test.json
│     └── dev.json
│     └── train.json
│...
```

This project use the same data partitioning as the previous work ([Yang and Mitchell, 2016](https://www.cs.cmu.edu/~bishan/papers/joint_event_naacl16.pdf);  [Nguyen et al., 2016](https://www.aclweb.org/anthology/N16-1034)). The data segmentation is specified in `data_list.csv`.

Below is information about the amount of parsed data when using this project. It is slightly different from the parsing results of the two papers above. The difference seems to have occurred because there are no promised rules for splitting sentences within the sgm format files.

|          | Documents    |  Sentences   |Triggers    | Arguments | Entity Mentions  |
|-------   |--------------|--------------|------------|-----------|----------------- |
| Test     | 40        | 713           | 422           | 892             |  4226             |
| Dev      | 30        | 875           | 492           | 933             |  4050             |
| Train    | 529       | 14724         | 4312          | 7811             |   53045            |
