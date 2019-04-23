import algo
import sys

print('Arguments ({}): {}'.format(len(sys.argv), str(sys.argv)))

if __name__ == "__main__":
    algo_code = algo.Code(sys.argv[1], sys.argv[2])

    algo_code.animate_chart()
    # algo_code.trade()

    del algo_code
