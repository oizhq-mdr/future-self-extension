def pvq_calculate_scores(data):
    pvq_scoring = {
        'Conformity': ['D2LP-1'],
        'Tradition': ['D2LP-2'],
        'Benevolence': ['D2LP-3'],
        'Universalism': ['D2LP-4'],
        'Self-Direction': ['D2LP-5'],
        'Stimulation': ['D2LP-6'],
        'Hedonism': ['D2LP-7'],
        'Achievement': ['D2LP-8'],
        'Power': ['D2LP-9'],
        'Security': ['D2LP-10'],
    }
    scores = {}
    for category, items in pvq_scoring.items():
        score = data[items].mean(axis=1).mean()  # Compute the mean score for each category
        scores[category] = score
    return scores

def generate_pvq_prompt(data):
    scores = pvq_calculate_scores(data)
    pvq_template = ""
    for key, score in scores.items():
        if 1 <= score <= 2:
            pvq_template += '- {0} is of minimal importance to this person, rarely influencing their decisions or behaviors.\n'.format(
                key)
        elif score <= 3:
            pvq_template += "- {0} holds some importance but are not primary drivers of this person's actions.\n".format(
                key)
        elif score <= 4:
            pvq_template += "- This person considers {0} somewhat important, but {0} may not consistently guide this person's daily choices.\n".format(
                key)
        elif score <= 5:
            pvq_template += "- {0} is important to this person and often influences their decisions and how they interact with the world.\n".format(
                key)
        elif score <= 6:
            pvq_template += "- This person places a high level of importance on {0}, and {0} significantly influences this person's life choices and behaviors.\n".format(
                key)
        elif score <= 7:
            pvq_template += "- {0} is of utmost importance and is central to this person's life. {0} guides their actions, decisions, and priorities.\n".format(
                key)
        else:
            pvq_template += "{0}: Score not in the expected range.\n".format(key)

    return pvq_template