import pickle
import numpy as np
import matplotlib.pyplot as plt

with open("acpl_rating_dataset.pkl", "rb") as f:
    dataset = pickle.load(f)

acpls = np.array([d[0] for d in dataset])
ratings = np.array([d[1] for d in dataset])

# Quadratic fit tends to match ACPL-rating curves better than linear
coeffs = np.polyfit(acpls, ratings, deg=2)
poly = np.poly1d(coeffs)

print("Fitted polynomial:")
print(poly)

# Sanity check plot
plt.scatter(acpls, ratings, alpha=0.5, label="Actual games")
x_line = np.linspace(min(acpls), max(acpls), 100)
plt.plot(x_line, poly(x_line), color="red", label="Fitted curve")
plt.xlabel("ACPL (decided positions excluded)")
plt.ylabel("Actual rating")
plt.legend()
plt.savefig("acpl_rating_fit.png")
print("Saved plot to acpl_rating_fit.png")

# Generate the replacement function for your main script
print("\nReplace your estimate_rating() function with:")
print(f"""
def estimate_rating(acpl):
    return {coeffs[0]:.6f} * acpl**2 + {coeffs[1]:.6f} * acpl + {coeffs[2]:.4f}
""")