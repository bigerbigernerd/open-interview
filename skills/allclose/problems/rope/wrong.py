"""Buggy variants the tests must catch."""
import numpy as np


def interleaved_pairs(x, positions, base=10000.0):
    d = x.shape[-1]
    theta = np.outer(positions, base ** (-np.arange(0, d, 2) / d))
    cos, sin = np.cos(theta), np.sin(theta)
    x1, x2 = x[..., 0::2], x[..., 1::2]  # original paper pairing; not the HF layout
    out = np.empty_like(x)
    out[..., 0::2] = x1 * cos - x2 * sin
    out[..., 1::2] = x1 * sin + x2 * cos
    return out


def exponent_i_over_d(x, positions, base=10000.0):
    d = x.shape[-1]
    theta = np.outer(positions, base ** (-np.arange(d // 2) / d))
    theta = np.concatenate([theta, theta], -1)
    rot = np.concatenate([-x[..., d // 2:], x[..., :d // 2]], -1)
    return x * np.cos(theta) + rot * np.sin(theta)


def rotate_sign_flipped(x, positions, base=10000.0):
    d = x.shape[-1]
    theta = np.outer(positions, base ** (-np.arange(0, d, 2) / d))
    theta = np.concatenate([theta, theta], -1)
    rot = np.concatenate([x[..., d // 2:], -x[..., :d // 2]], -1)  # rotates clockwise
    return x * np.cos(theta) + rot * np.sin(theta)


def ignores_positions(x, positions, base=10000.0):
    d, t = x.shape[-1], x.shape[-2]
    theta = np.outer(np.arange(t), base ** (-np.arange(0, d, 2) / d))
    theta = np.concatenate([theta, theta], -1)
    rot = np.concatenate([-x[..., d // 2:], x[..., :d // 2]], -1)
    return x * np.cos(theta) + rot * np.sin(theta)
