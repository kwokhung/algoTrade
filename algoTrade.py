import algo
import futu as ft

if __name__ == "__main__":
    algo_code = algo.Code('HK.03333', '2019-04-17', '2019-04-17', 0)
    algo_code.print()

    # ret_code, df = algo_code.get_kline(algo_code.start, algo_code.end)

    # if ret_code == ft.RET_OK:
    # algo_code.plot_chart(df)

    algo_code.animate_chart()

    del algo_code
