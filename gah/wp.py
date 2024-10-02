from functools import reduce


def apply_replaces(text, replaces):
    return reduce(lambda t, r: t.replace(*r), replaces, text)


def preprocess(sample):
    replaces = ((' . ', '. '),
        (' .', '.'),
        (' ; ', '; '),
        (' : ', ': '),
        (' ! ', '! '),
        (' !', '!'),
        (' ? ', '? '),
        (' ?', '?'),
        (' *', '*'),
        (' , ', ', '),
        (' ’ ', '’'),
        (" 's", "'s"),
        (" n't", "n't"),
        (" N'T", "N'T"),
        (" 've", "'ve"),
        (" 'd", "'d"),
        ("`` ", "``"),
        (" ''", "''"),
        ("“ ", "“"),
        (" ”", "”"),
        (" ’re", "’re"),
        (" 're", "'re"),
        (" ’m", "’m"),            
        (" 'm", "'m"),
        ('<newline> ', '\n'),
        (' <newline>', '\n'),
        ('<newline>', '\n'),            
        (' \n', '\n'),
    )
    text = sample['story']
    text = apply_replaces(text, replaces)
    text = [s.strip(" ") for s in text.split("\n")]
    text = "\n".join(text)
        
    sample['story'] = text
    return sample