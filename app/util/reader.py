def read_prompt(filename):
    file = open(f"app/prompt/{filename}.txt", 'r')
    text = file.read()
    file.close()
    return text
