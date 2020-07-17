def wrap_by_word(text, n):
    """
    returns a string where \n is inserted between every n words

    :url https://www.reddit.com/r/learnpython/comments/4i2z4u/how_to_add_a_new_line_after_every_nth_word/
    """
    a = text.split()
    to_return = str()
    for i in range(0, len(a), n):
        to_return += ' '.join(a[i:i + n]) + '\n'
    return to_return


def wrap_by_letter(text, n):
    """returns a string where \n is inserted between every n letters..."""
    a = list(text)
    to_return = str()
    for i in range(0, len(a), n):
        to_return += ''.join(a[i:i + n]) + '\n'
    
    return to_return
