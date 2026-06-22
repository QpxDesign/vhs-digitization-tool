input_file_name = "data/title.principals-sorted.tsv"

with open(input_file_name) as input_file:
    data = input_file.read().split("\n")
    headers = data[0]
    lines = data[1:]
    with open(f"{input_file_name.replace('.tsv', '')}-directors.tsv", "w") as output_file:
        output_file.write(headers)
        for line in lines:
            if len(line.split('\t')) < 4:
                continue
            if line.split('\t')[3] == "director":
                output_file.write(line + "\n")
