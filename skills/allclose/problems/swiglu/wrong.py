"""Buggy variants the tests must catch."""
import numpy as np


def _sig(z):
    return 1 / (1 + np.exp(-z))


def gelu_instead(x, w_gate, w_up, w_down):
    g = x @ w_gate
    gelu = 0.5 * g * (1 + np.tanh(np.sqrt(2 / np.pi) * (g + 0.044715 * g ** 3)))
    return (gelu * (x @ w_up)) @ w_down


def silu_on_up_branch(x, w_gate, w_up, w_down):
    u = x @ w_up
    return ((x @ w_gate) * u * _sig(u)) @ w_down


def sigmoid_gate(x, w_gate, w_up, w_down):
    return (_sig(x @ w_gate) * (x @ w_up)) @ w_down


def silu_on_both(x, w_gate, w_up, w_down):
    g, u = x @ w_gate, x @ w_up
    return (g * _sig(g) * u * _sig(u)) @ w_down
