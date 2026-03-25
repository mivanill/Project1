from rapidfuzz import fuzz


def find_similar_groups(df, threshold=80):
    descriptions = df["short_description"].fillna("").tolist()
    used = set()
    groups = []

    for i, desc in enumerate(descriptions):
        if i in used or not desc:
            continue

        group = [i]
        used.add(i)

        for j in range(i + 1, len(descriptions)):
            if j in used:
                continue

            score = fuzz.token_sort_ratio(desc, descriptions[j])

            if score >= threshold:
                group.append(j)
                used.add(j)

        if len(group) >= 3:
            groups.append(group)

    return groups