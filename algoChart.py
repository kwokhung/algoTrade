import algo
import sys

print('Arguments ({}): {}'.format(len(sys.argv), str(sys.argv)))

if __name__ == "__main__":
    algo_code = algo.Code()

    algo_code.chart()

    del algo_code
