def chunks(target_list: list,
           num_of_chunks: int) -> list[list]:
    for i in range(0, len(target_list), num_of_chunks):
        yield target_list[i:i + num_of_chunks]
