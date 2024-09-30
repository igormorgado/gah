# Geração Automática de Histórias

Research about the topic.

## Installation

Once you have the following installed and working

 - `Make`
 - `pyenv`
 - `pyenv-virtualenv`
 - `docker`

Execute:

`make pyvenv` - To install python version 3.11 and configure the virtualenv.

`make install` - To install all requirement packages. It may take some time.

`make langs` - To install Spacy languages

`make docker` - To install docker environment

The installation environment is based on:

- Python 3.11 (some libraries still do not support 3.12)
- Torch 2.4 
- Cuda 12.4

Unfortunately SpaCy is not compatible with Hugging Face transformers 4.45, hence
isn't possible to load latest Llamma-3.2, we will wait for updates from Spacy.

## How to use this


## Datasets used

We used some datasets


ROCStories ("igormorgado/ROCStories2016" / "igormorgado/ROCStories2018")

"Tackling The Story Ending Biases in The Story Cloze Test". Rishi Sharma, James Allen, Omid Bakhshandeh, Nasrin Mostafazadeh. In Proceedings of the 2018 Conference of the Association for Computational Linguistics (ACL), 2018

"A Corpus and Cloze Evaluation for Deeper Understanding of Commonsense Stories". Nasrin Mostafazadeh, Nathanael Chambers, Xiaodong He, Devi Parikh, Dhruv Batra, Lucy Vanderwende, Pushmeet Kohli and James Allen. In Proceedings of the 2016 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies (NAACL HLT), 2016


WritingPrompts [euclaise/writingprompts,  euclaise/WritingPromptsX , euclaise/WritingPrompts_curated, euclaise/WritingPrompts_preferences]

Angela Fan, Mike Lewis, and Yann Dauphin. 2018. Hierarchical Neural Story Generation. In Proceedings of the 56th Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers), pages 889–898, Melbourne, Australia. Association for Computational Linguistics.