#!/usr/bin/env python3
import string
from collections import Counter

# Translate uppercase -> lowercase, punctuation -> None.
trans = str.maketrans(string.ascii_uppercase, string.ascii_lowercase,
                      string.punctuation)


def tweets(filename):
    with open(filename) as f:
        tw = []
        for row in f:
            sp = row.split(',', maxsplit=3)
            _, _, _, t = sp
            tw.append(t.strip())
        return tw


def count(tweets):
    counter = Counter()
    for text in tweets:
        # Remove non ascii.
        text = ''.join(c for c in text if 31 < ord(c) < 127)
        text = text.translate(trans)
        counter.update(text.split())
    return counter


def main(filename, top=100, tf=False):
    tw = tweets(filename)
    counter = count(tw)
    for t, f in counter.most_common(top):
        if tf:
            print(t, f)
        else:
            print(t)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--file')
    parser.add_argument('--count', type=int, default=100)
    parser.add_argument('--tf', action='store_true')
    args = parser.parse_args()
    main(args.file, args.count, args.tf)
