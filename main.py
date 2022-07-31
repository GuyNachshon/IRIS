# from Speech import stt
from google_services import gsheets
import os
import json


def main():
    for f in os.listdir("exports/experiments"):
        vid = file.ExperimentFile(f"exports/experiments/{f}", f)
        rerun = False
        with open("finished.txt") as t:
            lines = t.read().splitlines()
            if f in lines:
                while rerun not in ["y", "n"]:
                    rerun = input(f"do you want to rerun {f}? (y/n)")
        if rerun.lower() == "n":
            print(f"skipping {f}")
            return
        file_name = f.replace(".mov", "")
        vid.read_frames()
        all_colors = vid.get_all_colors()
        with open(f'data/{file_name}.json', 'w+') as fp:
            json.dump(all_colors, fp, indent=4)
            fp.seek(0)
        res = gsheets.main(file_name, f'data/{file_name}.json')
        if res:
            with open("finished.txt", 'a') as t:
                t.write(f)


if __name__ == '__main__':
    main()
