"""This functions performs the prediction with the the help of ftio.py
"""

from __future__ import annotations
import sys
from ftio.prediction.pools import predictor_with_pools
from ftio.prediction.processes_zmq import predictor_with_processes_zmq
from ftio.prediction.processes import predictor_with_processes
from ftio.prediction.shared_resources import SharedResources


def main(args: list[str] = sys.argv) -> None:
    """runs the prediction and launches new threads whenever data is available

    Args:
        args (list[str]): arguments passed from command line
    """
    # Init
    shared_resources = SharedResources()
    mode = "procs"  # "procs" or "pool"

    if "pool" in mode.lower():
        # prediction with a Pool of process and a callback mechanism
        predictor_with_pools(shared_resources, args)
    else:
        if any("zmq" in x for x in args):
            # prediction with Processes of process and a callback mechanism + zmq
            predictor_with_processes_zmq(
                shared_resources,
                args,
            )
        else:
            # prediction with Processes of process and a callback mechanism
            predictor_with_processes(shared_resources, args)


if __name__ == "__main__":
    main(sys.argv)
