# run to generate testsetpoints.csv


def generate_setpoints(initial_offset_y, initial_offset_x, offset_x, offset_y, rows, columns, hysteresis_offset):
    """Write setpoints to testsetpoints.csv

    Args:
        initial_offset_x: initial offset from corner to well center a1 -- for now this is hardcoded in globals.py, leave at 0
        initial_offset_y: initial offset from corner to well center a1 -- for now this is hardcoded in globals.py, leave at 0
        offset_x: distance between wells in x direction
        offset_y: distance between wells in y direction
        rows: number of wells in y direction
        columns: number of wells in x direction
    """

    with open('testsetpoints.csv', 'w') as f:
        for y in range(rows):
            lines_buffer = []
            for x in range(columns):
                # Compensate hysteresis on x axis by changing the setpoints
                if y % 2 != 0 and x != columns - 1:
                    setpoint_x = round(initial_offset_x + x * offset_x + hysteresis_offset, 2)
                elif y % 2 == 0 and (x == 0 and y != 0):
                    setpoint_x = round(initial_offset_x + x * offset_x + hysteresis_offset, 2)
                else:
                    setpoint_x = round(initial_offset_x + x * offset_x, 2)
                setpoint_y = round(initial_offset_y + y * offset_y, 2)
                lines_buffer.append("{}, {}\n".format(setpoint_x, setpoint_y))
            if y % 2 != 0:
                lines_buffer.reverse()
            for line in lines_buffer:
                f.write(line)


if __name__ == '__main__':
    # settings for cellstar 96 well plate
    generate_setpoints(0, 0, 108 / 12, 108 / 12, 8, 12, 2.5)
