def sort_dataset(input_file_name: str):
    def sorter(e):
        int_id = e.split("\t")[0].replace("nm", "")
        if not int_id.isnumeric():
            print(e)
            return -1
        return int(e.split("\t")[0].replace("nm", ""))
    with open(input_file_name) as input_file:
        data = input_file.read().split("\n")
        headers = data[0]
        lines = data[1:]
        lines.sort(key=sorter)
        with open(f"{input_file_name.replace('.tsv', '')}-sorted.tsv", "w") as output_file:
            output_file.write(headers)
            for line in lines:
                output_file.write(line + "\n")


def check_sorted(input_file_name: str):
    with open(input_file_name) as file:
        prev_id = -1
        for line in file:
            if line.split("\t")[0] == "tconst":
                continue
            if not line.split("\t")[0].replace('tt', '').isnumeric():
                print(line)
            imdb_id = int(line.split("\t")[0].replace("tt", ""))
            if imdb_id < prev_id:
                raise Exception("NOT SORTED")
            prev_id = imdb_id


# check_sorted("data/title.principals-sorted.tsv")
# sort_dataset("data/title.principals.tsv")
# sort_dataset("data/title.basics.tsv")
sort_dataset("data/name.basics.tsv")
