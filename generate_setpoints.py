# run to generate testsetpoints.csv
# baased on draawing 677180.pdf


def generate_setpoints(initial_offset_y, initial_offset_x, offset_x, offset_y, rows, columns):
    """

    Args:
        initial_offset_x: initial offset from corner to well center a1
        initial_offset_y: initial offset from corner to well center a1
        offset_x: distance between wells
        offset_y: distance between wells

    Returns:

    """

    with open('testsetpoints.csv', 'w') as f:
        for y in range(rows):
            lines_buffer = []
            for x in range(columns):
                setpoint_x = round(initial_offset_x + x * offset_x, 2)
                setpoint_y = round(initial_offset_y + y * offset_y, 2)
                lines_buffer.append("{}, {}\n".format(setpoint_x, setpoint_y))
            if y % 2 != 0:
                lines_buffer.reverse()
            for line in lines_buffer:
                f.write(line)


if __name__ == '__main__':
    generate_setpoints(12.24, 18.38, 13, 13, 6, 8)
