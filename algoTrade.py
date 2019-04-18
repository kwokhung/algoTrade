import algo
import sys

print('Arguments ({}): {}'.format(len(sys.argv), str(sys.argv)))

if __name__ == "__main__":
    algo_code = algo.Code(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], int(sys.argv[6]))
    algo_code.print()

    # ret_code, df = algo_code.get_kline(algo_code.start, algo_code.end)

    # if ret_code == ft.RET_OK:
    # algo_code.plot_chart(df)

    algo_code.animate_chart()

    del algo_code
