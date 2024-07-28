from poems import Curator


def test_dates():
    print()
    curator = Curator()
    for author in ["bob-dylan", "t-s-eliot", "dante-alighieri", "horace", "ovid", "sappho", "anonymous"]:
        poem = curator.get_poem(author=author, verbose=False)
        print(f'{author:>16}: {repr(poem.author.dates(month_and_day=True))} or {repr(poem.author.dates(month_and_day=False))}')

def test_poems():
    curator = Curator()
    for index, entry in curator.catalog.df.iterrows():
        p = curator.get_poem(author=entry.author, title=entry.title)
        p.email_html