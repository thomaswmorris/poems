from poems import Curator


def test_dates():
    print()
    curator = Curator()
    for author in ["bob-dylan", "t-s-eliot", "dante-alighieri", "horace", "ovid", "sappho", "anonymous"]:
        poem = curator.get_poem(author=author, verbose=False)
        print(f'{author:>16}: {repr(poem.author.dates(month_and_day=True))} or {repr(poem.author.dates(month_and_day=False))}')

    print(poem.html_body)