"""Exact finite counterexample, not a model of any measured satellite sensor.

Normalized zero-mean continuous Gaussian objects convolved with a Gaussian PSF
have covariance C = S + B. A quarter rotation swaps diagonal entries. Two shape
classes can therefore share an image rotation orbit under a fixed anisotropic
PSF. The calculation illustrates existing incorrect-equivariance theory; it is
not claimed as a new theorem, real-data effect, or universal Bayes lower bound.
"""
from __future__ import annotations

import json


def witness() -> dict:
    blur = (2, 1)
    shape0 = (1, 4)  # unordered eigenvalues {1,4}
    shape1 = (3, 2)  # unordered eigenvalues {2,3}: a different shape class
    image0 = tuple(a + b for a, b in zip(shape0, blur))
    image1 = tuple(a + b for a, b in zip(shape1, blur))
    rotated_image0 = image0[::-1]
    physically_rotated_shape0 = tuple(a + b for a, b in zip(shape0[::-1], blur))
    joint_blur = blur[::-1]
    joint_image0 = tuple(a + b for a, b in zip(shape0[::-1], joint_blur))
    assert image0 == (3, 5) and image1 == rotated_image0 == (5, 3)
    assert physically_rotated_shape0 == (6, 2) != rotated_image0
    assert joint_image0 == rotated_image0
    recovered = [sorted(a - b for a, b in zip(c, blur)) for c in (image0, image1)]
    assert recovered == [[1, 4], [2, 3]]
    iso = (1, 1)
    isotropic_images = [tuple(a + b for a, b in zip(s, iso)) for s in (shape0, shape1)]
    assert sorted(isotropic_images[0]) != sorted(isotropic_images[1])
    return {
        "psf_covariance_diagonal": blur,
        "latent_covariance_diagonals": [shape0, shape1],
        "observed_covariance_diagonals": [image0, image1],
        "physical_rotation_fixed_psf": physically_rotated_shape0,
        "digital_rotation": rotated_image0,
        "joint_rotation_of_shape_and_psf": joint_image0,
        "recovered_shape_eigenvalues_with_psf": recovered,
        "equal_prior_two_point_population": {
            "best_rotation_invariant_image_only_01_risk": 0.5,
            "best_unrestricted_01_risk": 0.0,
        },
        "isotropic_psf_control_separates_classes_by_eigenvalues": True,
        "noncommutation_alone_insufficient": "The same anisotropic operator and two images "
            "with a constant class label have zero invariant and unrestricted risk.",
        "scope": "Exact algebra on a stipulated two-point Gaussian population. No images, "
            "training, fitted PSF, or scientific test data. Not evidence of a RarePlanes effect.",
    }


if __name__ == "__main__":
    print(json.dumps(witness(), sort_keys=True, indent=2))
