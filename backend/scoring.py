
def calculate_points(
    predicted_home,
    predicted_away,
    actual_home,
    actual_away
):
    # Exact score prediction
    if (
        predicted_home == actual_home
        and predicted_away == actual_away
    ):
        return 5

    # Determine predicted match outcome
    if predicted_home > predicted_away:
        predicted_result = "home_win"
    elif predicted_home < predicted_away:
        predicted_result = "away_win"
    else:
        predicted_result = "draw"

    # Determine actual match outcome
    if actual_home > actual_away:
        actual_result = "home_win"
    elif actual_home < actual_away:
        actual_result = "away_win"
    else:
        actual_result = "draw"

    # Correct outcome, but incorrect exact score
    if predicted_result == actual_result:
        return 3

    # Incorrect outcome
    return 0
