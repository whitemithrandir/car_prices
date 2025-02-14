def scale_number_to_three_digits_fixed(number: float) -> float:
    """
    Scale a number so that its integer part has three digits.
    For example:
    - 0.412 -> 412.0
    - 0.025689 -> 259.9
    - 0.000008956 -> 895.6
    - 0.0 -> 0
    :param number: A float number to be scaled.
    :return: The scaled number with three integer digits.
    """
    if number == 0:
        return 0

    # Scale the number to ensure 3 digits before the decimal point
    while number < 100:
        number *= 10

    return round(number, 3)