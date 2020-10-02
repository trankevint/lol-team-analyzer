import time
from lcu import LCU
from checker import Checker
from tabulate import tabulate


checker = Checker('')
lcu = LCU()


def wait_for_champ_select():
    while True:
        teammates = lcu.get_champ_select_teammates()
        if len(teammates) > 0:
            return teammates
        time.sleep(2.5)


def run():
    print("Waiting for game...")
    teammates = wait_for_champ_select()
    print("Found game.")

    table = []
    for teammate in teammates:
        print("Checking " + teammate["name"])
        row = [teammate["name"], teammate["assigned_role"]]
        analysis = checker.get_account_history(teammate["name"], 1)
        if analysis is None:
            row.append("No data")
            row.append("No data")
        else:
            main_role = analysis[0]
            if teammate["assigned_role"] == main_role:
                row.append("Yes")
            else:
                row.append("No (" + analysis[0] + " main)")
            win_rate = f'{analysis[1][0]} / {analysis[1][0] + analysis[1][1]}'
            row.append(win_rate)
        table.append(row)

    headers = ["Name", "Assigned Role", "On Role?", "Win Rate (past 1 days)"]
    print(tabulate(table, headers))


run()
