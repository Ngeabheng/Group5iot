"""
Name: Na Sereyvattanac


Dataset: health_lifestyle_dataset.csv
  (https://www.kaggle.com/datasets/chik0di/health-and-lifestyle-dataset)

"""

import numpy as np

# ---------------------------------
# STEP 1: Training data D
# ----------------------------------
training_data = [
    (21.8, 3.4, 279, 0),
    (29.9, 5.8, 240, 0),
    (34.4, 8.1, 285, 0),
    (30.3, 8.9, 251, 1),
    (36.9, 8.6, 197, 0),
    (31.1, 4.1, 290, 0),
    (21.0, 3.4, 268, 0),
    (22.1, 8.4, 256, 0),
    (25.9, 4.6, 287, 1),
    (38.2, 6.5, 230, 1),
    (28.1, 9.4, 208, 1),
    (37.2, 4.5, 289, 1),
    (19.6, 3.8, 299, 1),
    (33.1, 4.6, 262, 1),
    (28.3, 4.2, 161, 0),
    (21.8, 5.8, 189, 1),
    (19.8, 5.7, 259, 0),
    (24.9, 4.6, 264, 1),
    (36.1, 9.5, 259, 0),
    (32.1, 4.3, 288, 0),
]


X = np.array([[row[0], row[1], row[2]] for row in training_data])
y = np.array([row[3] for row in training_data])
n = len(X)  # number of training samples (n = 20)

print("Training data loaded.")
print(f"Number of training samples (n): {n}")
print(f"Number of features: {X.shape[1]}\n")


def get_k(n_samples):
    """Ask the user for k, ensuring 0 < k <= n."""
    while True:
        try:
            k = int(input(f"Enter k (must satisfy 0 < k <= {n_samples}): "))
            if 0 < k <= n_samples:
                return k
            print(f"Invalid input. k must be between 1 and {n_samples}.")
        except ValueError:
            print("Please enter a valid integer.")


# ------------------------------------
# STEP 3: Distance calculation
# ------------------------------------
def euclidean_distance(x, x_prime):
    """
    d(x, x') = sqrt( (x1-x1')^2 + (x2-x2')^2 + (x3-x3')^2 )
    x and x_prime are 1D numpy arrays of the same length.
    """
    return np.sqrt(np.sum((x - x_prime) ** 2))


# --------------------------------------
# STEP 4: Test sample x_q
# --------------------------------------
x_query = np.array([20, 3.4, 161])  # the point we want to predict a label for


# --------------------------------------
# STEP 5 & 6: Iterate over training samples, compute distance matrix
# --------------------------------------
def compute_distances(X, x_query):
    """
    Compute the Euclidean distance from x_query to every training sample.
    Returns a 1D numpy array of length n (the distance matrix/vector).
    """
    distances = np.zeros(len(X))
    for i in range(len(X)):
        distances[i] = euclidean_distance(X[i], x_query)
    return distances


# -------------------------------------------
# STEP 7: Choose the k nearest neighbors and compute weights
# -------------------------------------------
def get_k_nearest(distances, k):
    """
    Use NumPy to find the indices of the k smallest distances.
    Returns: (neighbor_indices, neighbor_distances)
    """
    neighbor_indices = np.argsort(
        distances)[:k]   # indices of k smallest distances
    neighbor_distances = distances[neighbor_indices]
    return neighbor_indices, neighbor_distances


def compute_weights(distances):
    """
    weight_i = 1 / (d_i + epsilon)
    A tiny epsilon avoids division by zero if a distance is exactly 0.
    """
    epsilon = 1e-9
    return 1.0 / (distances + epsilon)


# ------------------------------------------
# STEP 8: Compute the predicted label
#   y_hat = argmax_c  sum_{i in N_k} w_i * 1(y_i == c)
# -------------------------------------------
def predict_label(neighbor_indices, neighbor_weights, y):
    """
    For each class c present among the k nearest neighbors, sum the weights
    of the neighbors that belong to that class. Predict the class with the
    highest total weight.
    """
    neighbor_labels = y[neighbor_indices]
    classes = np.unique(neighbor_labels)

    class_scores = {}
    for c in classes:
        # sum of weights for neighbors whose label equals c
        class_scores[c] = np.sum(neighbor_weights[neighbor_labels == c])

    predicted_class = max(class_scores, key=class_scores.get)
    return predicted_class, class_scores


# ------------------------------------------
# MAIN PROGRAM: run the full KNN pipeline
# ------------------------------------------
def knn_predict(X, y, x_query, k, verbose=True):
    distances = compute_distances(X, x_query)
    neighbor_indices, neighbor_distances = get_k_nearest(distances, k)
    neighbor_weights = compute_weights(neighbor_distances)
    predicted_class, class_scores = predict_label(
        neighbor_indices, neighbor_weights, y)

    if verbose:
        print(f"\nQuery point x_q = {x_query.tolist()}, k = {k}\n")

        print("Distance from x_q to every training sample:")
        for i in range(len(X)):
            print(f"  No.{i+1:2d}  Feature={X[i].tolist()}  Label={y[i]}  "
                  f"Distance={distances[i]:.3f}")

        print(f"\nThe {k} nearest neighbors (sorted by distance):")
        for rank, idx in enumerate(neighbor_indices, start=1):
            print(f"  Rank {rank}: No.{idx+1}  Feature={X[idx].tolist()}  "
                  f"Label={y[idx]}  Distance={distances[idx]:.3f}  "
                  f"Weight={compute_weights(distances[idx:idx+1])[0]:.5f}")

        print("\nWeighted vote total for each class:")
        for c, score in class_scores.items():
            print(f"  Class {c}: total weight = {score:.5f}")

        print(f"\nPredicted label (y_hat) = {predicted_class}")

    return predicted_class


if __name__ == "__main__":
    k = get_k(n)
    knn_predict(X, y, x_query, k)
