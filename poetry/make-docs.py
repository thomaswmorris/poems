from datetime import datetime
import calendar
import pandas as pd
import github as gh
import sys; sys.path.insert(1, 'poetry/')
import numpy as np
from poetry import Poetizer
from context_utils import get_month, get_weekday, get_day, get_holiday, get_season, get_liturgy
import os, re
from io import StringIO

import argparse, sys
parser = argparse.ArgumentParser()
parser.add_argument('--username', type=str, help='Email address from which to send the poem',default='')
parser.add_argument('--password', type=str, help='Email password',default='')
parser.add_argument('--recipient', type=str, help='Where to send the poem',default='poemsfromtom@gmail.com')
parser.add_argument('--repo_lsfn', type=str, help='Where to send the poem',default='')
parser.add_argument('--poet', type=str, help='Which poet to send', default='random')
parser.add_argument('--title', type=str, help='Which title to send', default='random')
parser.add_argument('--repo', type=str, help='Which GH repository to load', default='')
parser.add_argument('--token', type=str, help='GH token', default='')
parser.add_argument('--context', type=bool, help='Whether to send contextual poems', default=False)
parser.add_argument('--rh', type=bool, help='Whether to consider past poems sent', default=False)
parser.add_argument('--wh', type=bool, help='Whether to consider this poem in the future', default=False)
parser.add_argument('--hist_tag', type=str, help='What tag to write to the history with', default='')
parser.add_argument('--subj_tag', type=str, help='Email subject prefix', default='')
parser.add_argument('--hour', type=str, help='Hour of the day to send', default=7)
parser.add_argument('--token_from_heroku', type=bool, help='Whether to get token from os env', default=False)

args = parser.parse_args()

if args.token_from_heroku: args.token = os.environ['GITHUB_TOKEN']

def commit_elements(_elems):

    dt_now = datetime.fromtimestamp(history.iloc[-1]['timestamp'])
    now_date, now_time = dt_now.isoformat()[:19].split('T') 

    head_sha  = poetizer.repo.get_branch('master').commit.sha
    base_tree = poetizer.repo.get_git_tree(sha=head_sha)

    tree   = poetizer.repo.create_git_tree(_elems, base_tree)
    parent = poetizer.repo.get_git_commit(sha=head_sha) 

    commit = poetizer.repo.create_git_commit(f'update logs {now_date} {now_time}', tree, [parent])
    master_ref = poetizer.repo.get_git_ref('heads/master')
    master_ref.edit(sha=commit.sha)

# Initialize the poetizer
poetizer = Poetizer()

print(args.repo, args.token)

# Choose a poem that meets the supplied conditions
poetizer.load_history(repo_name=args.repo, repo_token=args.token) # This automatically loads the repo as well
history = poetizer.history.copy()

history['strip_title'] = [re.sub(r'^(THE|AN|A)\s+', '', title) for title in history['title']]

dt_now = datetime.fromtimestamp(history.iloc[-1]['timestamp'])
now_date, now_time = dt_now.isoformat()[:19].split('T')
print(f'today is {now_date} {now_time}')
home_index = f'''
    <html>
    <head>
        <title></title>
        <meta http-equiv = "refresh" content="0; url={dt_now.year:02}-{dt_now.month:02}-{dt_now.day:02}"/>
    </head>
    </html>
    '''

ymds = []
for i, loc in enumerate(history.index):
    y, m, d = history.loc[loc,'date'].split('-')
    ymds.append(f'{y:0>2}-{m:0>2}-{d:0>2}')

random_index = f'''
    <html>
        <title> </title>
        <script>
        var ymds = [{','.join([f'"{ymd}"' for ymd in ymds])}];
        window.location.href = ymds[Math.floor(Math.random() * ymds.length)];
        </script>
    </html>
    '''

arch_string = f'<a href="archive">archive</a>'
poet_string = f'<a href="poets">poets</a>'
tday_string = f'<a href="index">today</a>'

poets_index = f'''<html><title>poets</title>\n
            <p style="font-family:Garamond; color:Black; font-size: 20px; margin-bottom:0; margin : 0; padding-top:0;">
            <i><b>{arch_string}&nbsp;</b>/<b>&nbsp;poets&nbsp;</b>/<b>&nbsp;{tday_string}</b></i><br>'''

for _poet in sorted(np.unique(history['poet'])):

    tag, name, birth, death, nationality, link = poetizer.data[_poet]['metadata'].values()

    title_list = history.sort_values('strip_title').loc[history['poet']==_poet, 'title']
    date_list  = history.sort_values('strip_title').loc[history['poet']==_poet, 'date']

    poets_index += f'''\n\n<p style="font-size: 28px;">{name} 
    <span style="font-family:Garamond; color:Black; font-size: 20px; margin-bottom:0; margin : 0; padding-top:0;">
    ({birth}&#8212;{death}) {poetizer.html_flags[nationality]}'''
    
    for title, date in zip(title_list, date_list):

        y, m, d = date.split('-')
        poets_index += f'\n<br><i><a href={y}-{m}-{d}">{poetizer.titleize(title)}</a></i>'
        
    poets_index += '\n<br><br style="line-height: 10px" /></span></p>'

poets_index += '\n<html>'

####### 

archive_index = f'''<html><title>archive</title>\n
            <p style="font-family:Garamond; color:Black; font-size: 20px; margin-bottom:0; margin : 0; padding-top:0;">
            <i><b>archive&nbsp;</b>/<b>&nbsp;{poet_string}&nbsp;</b>/<b>&nbsp;{tday_string}</b></i></p>'''
_m = '0'

dts = map(datetime.fromtimestamp, history.timestamp.values)
archive_ordering = np.argsort([-dt.year - 1e-3 * dt.month + 1e-6 * dt.day for dt in dts])

for index, entry in history.iloc[archive_ordering].iterrows():

    poet, title, type, date, time, timestamp, _ = entry
    tag, name, birth, death, nationality, link = poetizer.data[poet]['metadata'].values()

    y, m, d = date.split('-')

    if not m == _m:
        archive_index += f'</td></table>'
        archive_index += f'\n<br><h2 style="font-size: 28px;">{get_month(timestamp).capitalize()} {y}</h2>'
        archive_index += f'\n<table cellspacing="18"><td>'
        _m = m

    poetizer.load_poem(poet=poet, title=title, when=timestamp, verbose=False)

    day = f'{int(get_day(timestamp))}&nbsp;'

    if len(day) == 7: day += '&nbsp;&nbsp;'
    if int(d) in [11,21]: archive_index += f'</td><td>'

    archive_index += f'\n<p style="font-size: 20px;margin-top:0;margin-bottom:8">{day}&#8212;&nbsp;'
    archive_index += f'<i><a href="{y}-{m}-{d}">{poetizer.titleize(title)}</a>&nbsp;by&nbsp;{name}</i></p>'

archive_index += '\n</td></table>\n</html>'

#######

blob  = poetizer.repo.create_git_blob(home_index, "utf-8")
elems = [gh.InputGitTreeElement(path='poems/index.html', mode='100644', type='blob', sha=blob.sha)]

blob  = poetizer.repo.create_git_blob(random_index, "utf-8")
elems.append(gh.InputGitTreeElement(path='poems/random.html', mode='100644', type='blob', sha=blob.sha))

#blob  = poetizer.repo.create_git_blob(poets_index, "utf-8")
#elems.append(gh.InputGitTreeElement(path='poems/poets.html', mode='100644', type='blob', sha=blob.sha))

#blob  = poetizer.repo.create_git_blob(archive_index, "utf-8")
#elems.append(gh.InputGitTreeElement(path='poems/archive.html', mode='100644', type='blob', sha=blob.sha))

commit_elements(elems)

n_history = len(history)
ys, ms, ds = [], [], []

elems = []

for i, loc in enumerate(history.index):

    y, m, d = history.loc[loc,'date'].split('-')

    dt = datetime(int(y),int(m),int(d),7,0,0) 
    dt_prev = datetime.fromtimestamp(dt.timestamp() - 86400)
    dt_next = datetime.fromtimestamp(dt.timestamp() + 86400)
    
    poetizer.load_poem(poet=history.loc[loc,'poet'], title=history.loc[loc,'title'], when=history.loc[loc,'timestamp'], verbose=False, include_flags=True)

    print(y, m, d, poetizer.poet, poetizer.title)

    prev_string = f'<a href="{dt_prev.year:02}-{dt_prev.month:02}-{dt_prev.day:02}">«previous</a>&nbsp;</b>/<b>&nbsp;' if i > 0 else ''
    next_string = f'&nbsp;</b>/<b>&nbsp;<a href="{dt_next.year:02}-{dt_next.month:02}-{dt_next.day:02}">next»</a>' if i < n_history - 1 else ''
    rand_string = f'<a href="random">random</a>'

    html_color = 'black'

    today = tday_string if i < n_history - 1 else 'today'
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>

    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <title>{poetizer.nice_fancy_date}</title>
    <meta name="description" content="Core HTML Project">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">

    <!-- External CSS -->
    <link rel="stylesheet" href="../assets/vendor/bootstrap/bootstrap.min.css">
    <link rel="stylesheet" href="../assets/vendor/select2/select2.min.css">
    <link rel="stylesheet" href="../assets/vendor/owlcarousel/owl.carousel.min.css">
    <link rel="stylesheet" href="../assets/vendor/lightcase/lightcase.css">

    <!-- Fonts -->
    <link href="https://fonts.googleapis.com/css?family=Lato:300,400|Work+Sans:300,400,700" rel="stylesheet">

    <!-- CSS -->
    <link rel="stylesheet" href="../assets/css/style.min.css">
    <link rel="stylesheet" href="https://cdn.linearicons.com/free/1.0.0/icon-font.min.css">
    <link href="https://file.myfontastic.com/7vRKgqrN3iFEnLHuqYhYuL/icons.css" rel="stylesheet">

    <!-- Modernizr JS for IE8 support of HTML5 elements and media queries -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/modernizr/2.8.3/modernizr.js"></script>

</head>

<body data-spy="scroll" data-target="#navbar-nav-header" class="static-layout">
	<div class="boxed-page">

<nav id="gtco-header-navbar" class="navbar navbar-expand-lg py-4">
    <div class="container">
        <div class="collapse navbar-collapse" id="navbar-nav-header">
            <ul class="navbar-nav ml-auto">
                <li class="nav-item"><a class="nav-link" href="index">Home</a></li>
                <li class="nav-item"><a class="nav-link" href="cv">CV</a></li>
                <li class="nav-item"><a class="nav-link" href="papers">Papers</a></li>
                <li class="nav-item"><a class="nav-link" href="projects">Projects</a></li>
                <li class="nav-item"><a class="nav-link" href="poems">Poems</a></li>
                <li class="nav-item"><a class="nav-link" href="crosswords">Crosswords</a></li>
                <li class="nav-item"><a class="nav-link" href="blog">Blog</a>
                </li>
            </ul>
        </div>
    </div>    
</nav>		

<section class="bg-white">
    <div class="container">
        <div class="row section topspace" style="padding-left: 0%; padding-right: 0%;">
            <p style="color:Black; font-size: 20px; margin-bottom:0; margin : 0; padding-top:0;">
                <i><b>{prev_string}{rand_string}{next_string}</b>
                <br>{poetizer.nice_fancy_date}</i></p>
                <br>
            <div class="col-md-12">
                <h2 style="color:'{html_color}'; font-size: 30px; margin-bottom:0; margin : 0; padding-top:0;">{poetizer.titleize(poetizer.title)}</h2>
                <p style="color:{html_color}; font-size: 20px; margin-bottom:0; margin : 0; padding-top:0;"><i>by 
                <a href="{poetizer.link}">{poetizer.name}</a> ({poetizer.birth}&#8212;{poetizer.death})</i>{poetizer.flag_ish}</p>
                <blockquote align="justify">
                {poetizer.html_body}
                </blockquote>
            </div>
        </div>	<!-- /container -->
    </div>	<!-- /container -->
</section>		<!-- Counter Section -->
	
</div>
	<!-- External JS -->
	<script type="text/javascript" src="http://ajax.googleapis.com/ajax/libs/jquery/1/jquery.js"></script>
	<script src="../assets/vendor/bootstrap/popper.min.js"></script>
	<script src="../assets/vendor/bootstrap/bootstrap.min.js"></script>
	<script src="../assets/vendor/select2/select2.min.js "></script>
	<script src="../assets/vendor/owlcarousel/owl.carousel.min.js"></script>
	<script src="../assets/vendor/isotope/isotope.min.js"></script>
	<script src="../assets/vendor/lightcase/lightcase.js"></script>
	<script src="../assets/vendor/waypoints/waypoint.min.js"></script>
	<script src="../assets/vendor/countTo/jquery.countTo.js"></script>

	<!-- Main JS -->
	<script src="js/app.min.js "></script>
	<script src="//localhost:35729/livereload.js"></script>
</body>
</html>
'''

    index_fn = f'poems/{y}-{m}-{d}.html'

    try:    contents = poetizer.repo.get_contents(index_fn, ref='master').decoded_content.decode()
    except: contents = None

    print(32*'#')

    if html == contents:
        continue

    '''
    running_string = ''
    for char1, char2 in zip(contents, html_header + poetizer.poem_html):
        
        running_string += char1

        if not char1 == char2: break

    print(running_string)

    #if i > 10: assert False
    '''

    blob = poetizer.repo.create_git_blob(html, "utf-8")

elems.append(gh.InputGitTreeElement(path=index_fn, mode='100644', type='blob', sha=blob.sha))

commit_elements(elems)
print(f'wrote to {index_fn}')