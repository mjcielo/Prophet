
from scoring import calculate_points

points = calculate_points(2, 1, 2, 1)
print("Exact score points:", points)

points = calculate_points(3, 1, 2, 1)
print("Correct outcome points:", points)

points = calculate_points(1, 2, 2, 1)
print("Wrong outcome points:", points)
