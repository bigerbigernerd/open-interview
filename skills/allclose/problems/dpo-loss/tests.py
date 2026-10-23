import numpy as np


def cases():
    rng = np.random.default_rng(24)

    def args(n, scale=20.0, beta=0.1):
        base = rng.normal(size=n) * scale - 100
        return dict(policy_chosen_logps=base + rng.normal(size=n) * 3, policy_rejected_logps=base - 5 + rng.normal(size=n) * 3,
                    ref_chosen_logps=base + rng.normal(size=n) * 3, ref_rejected_logps=base - 5 + rng.normal(size=n) * 3, beta=beta)

    return [
        dict(name="one pair", kwargs=dict(policy_chosen_logps=np.array([-10.0]), policy_rejected_logps=np.array([-12.0]),
                                         ref_chosen_logps=np.array([-11.0]), ref_rejected_logps=np.array([-11.5])), sample=True),
        dict(name="batch of 4", kwargs=args(4), sample=True),
        dict(name="beta 0.5", kwargs=args(8, beta=0.5)),
        dict(name="policy equals reference (loss = log 2)", kwargs=dict(policy_chosen_logps=np.full(3, -20.0), policy_rejected_logps=np.full(3, -30.0),
                                                                        ref_chosen_logps=np.full(3, -20.0), ref_rejected_logps=np.full(3, -30.0))),
        dict(name="huge margins (stability)", kwargs=dict(policy_chosen_logps=np.array([-10.0, -9000.0]), policy_rejected_logps=np.array([-9000.0, -10.0]),
                                                          ref_chosen_logps=np.array([-50.0, -50.0]), ref_rejected_logps=np.array([-50.0, -50.0]), beta=1.0)),
        dict(name="batch of 64", kwargs=args(64, beta=0.05)),
    ]
