import algo
import sys

print('Arguments ({}): {}'.format(len(sys.argv), str(sys.argv)))

if __name__ == "__main__":
    algo_code = algo.Code()

    algo_code.animate_chart()
    # algo_code.trade()
    # algo_code.test()

    del algo_code
