import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import pandas as pd
import yaml

plt.rc('font', family='serif')

def points_mistake_spot(question, mistake_spot, keys):
    if mistake_spot in keys[question]:
        points = keys[question][mistake_spot]
    else:
        points = keys['global'][mistake_spot]
    return points

def deduct(question, mistake, keys):
    '''
    Returns points to deduct in the given question
    '''
    points = 0
    for mistake_spot in mistake:
        points += points_mistake_spot(question, mistake_spot, keys)

    return points

def score(net_id, mistakes, keys):
    '''
    Returns the total score of one student
    '''
    mistakes_list = []
    if not mistakes:
        mistakes_list.append({
            'net_id': net_id,
            'question': '',
            'mistake_spot': '',
            'deduct': 0
        })
    for question, mistake in mistakes.items():

        if type(mistake) == str:
            mistake = [mistake]

        for mistake_spot in mistake:

            mistakes_list.append({
                'net_id': net_id,
                'question': question,
                'mistake_spot': mistake_spot,
                'deduct': points_mistake_spot(question, mistake_spot, keys)
            })

    return pd.DataFrame(mistakes_list)

def read(yaml_name):

    with open(yaml_name) as f:
        raw = yaml.load(f, Loader=yaml.FullLoader)

    l = []
    for net_id, mistakes in raw.items():

        if mistakes is None:
            mistakes = {}

        if net_id == 'keys':
            continue
        l.append(score(net_id, mistakes, raw['keys']))

    d = pd.concat(l)
    return d

def get_max_score(yaml_name):
    with open(yaml_name) as f:
        raw = yaml.load(f, Loader=yaml.FullLoader)

    scores = []
    for question, mistakes in raw['keys'].items():
        if 'empty' in mistakes:
            scores.append(mistakes['empty'])

    return np.abs(sum(scores))

def save_pdf(d, output):
    fig, ax = plt.subplots()
    ax.axis('tight')
    ax.axis('off')
    ax.table(cellText=d.values, colLabels=d.columns, loc='center')
    pp = PdfPages(output)
    pp.savefig(fig, bbox_inches='tight')
    pp.close()

def save_csv(d, output, assignment):
    l = []
    for name, g in d.groupby(['net_id']):
        l.append({
            'net_id': name,
            'total_score': g['total_score'][0]
        })
    d = pd.DataFrame(l)
    d = d.rename(columns={'net_id': 'Student ID', 'total_score': assignment})
    d[['Student ID', assignment]].to_csv(output, index=False)


def get_total_scores(d, max_score):
    for name, g, in d.groupby(['net_id']):
        total_deduct = g['deduct'].sum()
        total_score = max_score + total_deduct
        d.loc[d['net_id'] == name, 'total_score'] = total_score
    d = d.astype({'total_score': 'int32'})
    return d

def report(d, max_score):
    net_id = d['net_id'].unique()[0]

    l = [f'{net_id}:']
    questions = []
    for idx, row in d.iterrows():
        if row['deduct'] == 0:
            continue
        if row['question'] not in questions:
            l.append(f"  {row['question']}:")
            questions.append(row['question'])
        report = f"    {row['deduct']:>4}: {row['mistake_spot']}"
        l.append(report)
    total_score = d['total_score'].unique()[0]
    l.append(f'total_score: {total_score}/{max_score}')
    s = '\n'.join(l)

    with open(f'graded/_{net_id}_.txt', 'w') as f:
        f.write(s)

def run():
    d = read('notes.yaml')
    max_score = get_max_score('notes.yaml')
    d = get_total_scores(d, max_score)
    save_csv(d, 'notes.csv', 'C01')
    save_pdf(d, 'notes.pdf')
    d.groupby('net_id').apply(report, max_score=max_score)

run()
